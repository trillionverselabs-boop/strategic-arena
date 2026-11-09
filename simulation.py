# Simulation loop — OASIS-style: rounds -> observe -> retrieve -> act -> stance update.
# Interventions inject at a round. Progress pushed via on_round for the desktop socket.

from __future__ import annotations

from typing import Callable, List

from .agents import StakeholderAgent
from .models import Event, Intervention, Scenario, SimulationResult, Snapshot


def run_simulation(
    scenario: Scenario,
    personas,
    events_out: List[Event] | None = None,
    on_round: Callable[[Snapshot], None] | None = None,
    llm=None,
) -> SimulationResult:
    """Run the full simulation. Returns a filled SimulationResult (scoring/reporting
    happen downstream). events_out/snapshots are returned inside the result."""
    agents: List[StakeholderAgent] = [StakeholderAgent(p) for p in personas]
    result_events: List[Event] = []
    snapshots: List[Snapshot] = []

    rounds = scenario.rounds
    interventions: List[Intervention] = scenario.interventions

    for rnd in range(1, rounds + 1):
        # late intervention: everyone observes it first
        for iv in interventions:
            if iv.inject_at_round == rnd:
                for a in agents:
                    a.observe(f"Intervention: {iv.name} — {iv.description}", 0.9, rnd)
                result_events.append(
                    Event(round=rnd, actor="<god>", action="intervention", text=f"{iv.name}: {iv.description}")
                )

        # each agent acts, seeing the current stance landscape
        stances = {a.p.name: a.p.stance for a in agents}
        for a in agents:
            move = a.act(scenario.title, stances, rnd, llm)
            a.p.stance = max(-1.0, min(1.0, a.p.stance + move["stance_delta"]))
            a.observe(move["text"] or move["action"], 0.4, rnd)
            if move["text"] or move["action"] != "waits":
                result_events.append(
                    Event(round=rnd, actor=a.p.name, action=move["action"], text=move["text"])
                )
            # everyone notices everyone else's move
            for other in agents:
                if other is not a:
                    other.observe(f"{a.p.name} {move['action']}", 0.3, rnd)

        snap = Snapshot(round=rnd, stances={a.p.name: round(a.p.stance, 3) for a in agents})
        snapshots.append(snap)
        if on_round:
            on_round(snap)

        # lightweight reflection mid-run and at end (Smallville)
        if rnd == max(1, rounds // 2) or rnd == rounds:
            for a in agents:
                a.reflect(llm, rnd)

    return SimulationResult(
        title=scenario.title,
        goal=scenario.goal,
        rounds=rounds,
        personas=[a.p for a in agents],
        events=result_events,
        snapshots=snapshots,
        interventions_shot=[iv.name for iv in interventions],
    )
