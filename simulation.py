# Simulation loop — OASIS-style: rounds -> observe -> retrieve -> act -> stance update.
# Interventions can be queued mid-run (the god-mode move) and are drained at the
# start of the next round, so the graph bends while the user watches.

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List

from .agents import StakeholderAgent
from .models import Event, Intervention, Scenario, SimulationResult, Snapshot

# Parties act independently within a round — they only read the shared stance
# map. Running them concurrently turns a 16-round × 7-party run (112 sequential
# model calls) into ~16 × one-call latency, which is the difference between a
# 30-minute review and a few minutes.
MAX_WORKERS = 8


def _act_in_parallel(agents: List[StakeholderAgent], title: str, stances: dict,
                     rnd: int, llm) -> list:
    def one(a):
        return a, a.act(title, stances, rnd, llm)

    if llm is None or len(agents) <= 1:
        return [one(a) for a in agents]
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(agents))) as pool:
        return list(pool.map(one, agents))


def _reflect_in_parallel(agents: List[StakeholderAgent], rnd: int, llm) -> None:
    if llm is None or len(agents) == 1:
        for a in agents:
            a.reflect(llm, rnd)
        return
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(agents))) as pool:
        list(pool.map(lambda a: a.reflect(llm, rnd), agents))


def run_simulation(
    scenario: Scenario,
    personas,
    events_out: List[Event] | None = None,
    on_round: Callable[[Snapshot], None] | None = None,
    llm=None,
    injection_queue: list | None = None,
) -> SimulationResult:
    """Run the full simulation. Returns a filled SimulationResult (scoring/reporting
    happen downstream)."""
    agents: List[StakeholderAgent] = [StakeholderAgent(p) for p in personas]
    result_events: List[Event] = []
    snapshots: List[Snapshot] = []

    rounds = scenario.rounds
    interventions: List[Intervention] = scenario.interventions

    for rnd in range(1, rounds + 1):
        # scheduled intervention: everyone observes it first
        for iv in interventions:
            if iv.inject_at_round == rnd:
                for a in agents:
                    a.observe(f"Intervention: {iv.name} — {iv.description}", 0.9, rnd)
                result_events.append(
                    Event(round=rnd, actor="<god>", action="intervention",
                          text=f"{iv.name}: {iv.description}")
                )

        # live intervention: queued from the UI / agent while the run is in flight
        while injection_queue:
            iv = injection_queue.pop(0)
            for a in agents:
                a.observe(f"Intervention: {iv.name} — {iv.description}", 0.95, rnd)
            result_events.append(
                Event(round=rnd, actor="<god>", action="intervention",
                      text=f"{iv.name}: {iv.description}")
            )

        # each agent acts, seeing the current stance landscape
        stances = {a.p.name: a.p.stance for a in agents}
        for a, move in _act_in_parallel(agents, scenario.title, stances, rnd, llm):
            a.p.stance = max(-1.0, min(1.0, a.p.stance + move["stance_delta"]))
            a.observe(move["text"] or move["action"], 0.4, rnd)
            if move["text"] or move["action"] != "waits":
                result_events.append(
                    Event(round=rnd, actor=a.p.name, action=move["action"], text=move["text"])
                )
            for other in agents:
                if other is not a:
                    other.observe(f"{a.p.name} {move['action']}", 0.3, rnd)

        snap = Snapshot(round=rnd, stances={a.p.name: round(a.p.stance, 3) for a in agents})
        snapshots.append(snap)
        if on_round:
            on_round(snap)

        # lightweight reflection mid-run and at end (Smallville)
        if rnd == max(1, rounds // 2) or rnd == rounds:
            _reflect_in_parallel(agents, rnd, llm)

    return SimulationResult(
        title=scenario.title,
        goal=scenario.goal,
        rounds=rounds,
        personas=[a.p for a in agents],
        events=result_events,
        snapshots=snapshots,
        interventions_shot=[iv.name for iv in interventions],
        llm_failures=sum(a.failures for a in agents),
    )
