"""Leverage — what each party is worth, computed, not asserted.

"Legal can stop it" is a fact the reader already had. What they do not have is a
*number*: how many of the heat points in this room are Legal's, and what happens
to the call if Legal's condition is met. That is a counterfactual, so it has to
be computed from the same friction function the run used — never asked of a model
and never estimated by eye.

The method is the Shapley value (Shapley, 1953) over the room's own friction
function, with one convention that keeps it honest:

    a party "not in S" is *neutral* (0.0 — undecided, their condition met),
    not absent.

Two reasons. Absent parties shrink the sample, and friction averages stances, so
a three-person room and a six-person room are not comparable — a lone hostile
voice would read as more heat than the whole room it came from. Neutralising
keeps the room the same size and asks the only question a reader cares about:
*how much of this heat is that party's, above a room where nobody objects?*

Consequences worth knowing, all of them load-bearing:

- ``baseline`` (everyone neutral) is not zero — a room of undecided parties still
  scores 35 on this scale. That floor belongs to the decision, not to a person.
- ``sum(party.value) == total - baseline`` exactly. The bar adds up or the code
  is wrong; ``tests/test_leverage.py`` asserts it.
- A supporter has a *negative* value: they take heat out of the room. The UI
  shows them as cooling, never as a bar of negative width.
"""

from __future__ import annotations

import random
from math import factorial
from typing import Dict, List, Sequence

from . import scoring

NEUTRAL = 0.0      # undecided / condition met — what a counterfactual moves to
SETTLED = 0.4      # a satisfied party is mildly *for* it, not merely silent
MAX_EXACT = 12     # 2^12 subsets is instant; above that we sample permutations


class _Room:
    """What `scoring.friction_score` reads: a list of things with a stance."""

    __slots__ = ("personas",)

    def __init__(self, stances: Sequence[float]):
        self.personas = [_Stance(s) for s in stances]


class _Stance:
    __slots__ = ("stance",)

    def __init__(self, stance: float):
        self.stance = stance


def friction(stances: Sequence[float], quality: float = 1.0) -> float:
    """The run's own friction, on any hypothetical room. One source of truth."""
    # duck-typed on purpose: friction_score reads only .personas[].stance, so
    # pricing a hypothetical room needs no SimulationResult and no model call.
    return scoring.friction_score(_Room(stances), quality)[0]  # type: ignore[arg-type]


OPEN_WAR = 65.0   # the line sea_state() uses for a red read
CONTESTED = 35.0  # the line sea_state() uses for blue


def band(value: float) -> Dict[str, str]:
    """The same three bands the results page shades, named once."""
    if value >= OPEN_WAR:
        return {"key": "open_war", "label": "Open war"}
    if value >= CONTESTED:
        return {"key": "contested", "label": "Contested ground"}
    return {"key": "quiet", "label": "Quiet ground"}


def _values(stances: Sequence[float]) -> Dict[int, float]:
    """v(S) for every subset, memoised — the whole game in one pass."""
    n = len(stances)
    vals: Dict[int, float] = {}
    for mask in range(1 << n):
        vals[mask] = friction([stances[i] if (mask >> i) & 1 else NEUTRAL
                               for i in range(n)])
    return vals


def _shapley_exact(stances: Sequence[float], vals: Dict[int, float]) -> List[float]:
    n = len(stances)
    phi = [0.0] * n
    for i in range(n):
        for mask in range(1 << n):
            if (mask >> i) & 1:
                continue
            s = bin(mask).count("1")
            w = factorial(s) * factorial(n - s - 1) / factorial(n)
            phi[i] += w * (vals[mask | (1 << i)] - vals[mask])
    return phi


def _shapley_sampled(stances: Sequence[float], permutations: int = 2000,
                     seed: int = 7) -> List[float]:
    """Large rooms: average the marginal contribution over random orderings.

    Deterministic (fixed seed) so a run's numbers never move between reads —
    a ledger that changes when you reopen it is not a ledger.
    """
    n = len(stances)
    rng = random.Random(seed)
    phi = [0.0] * n
    order = list(range(n))
    for _ in range(permutations):
        rng.shuffle(order)
        room = [NEUTRAL] * n
        prev = friction(room)
        for i in order:
            room[i] = stances[i]
            now = friction(room)
            phi[i] += now - prev
            prev = now
    return [x / permutations for x in phi]


def shapley(stances: Sequence[float]) -> List[float]:
    stances = list(stances)
    if not stances:
        return []
    if len(stances) <= MAX_EXACT:
        return _shapley_exact(stances, _values(stances))
    return _shapley_sampled(stances)


def _veto_left(parties: List[dict]) -> str:
    """Who can still stop it, given the (possibly satisfied) room."""
    blocking = [p for p in parties
                if p["stance"] < scoring.BLOCKER_THRESHOLD
                and (p.get("capacity") is None or p["capacity"] >= scoring.CAPACITY_MIN)]
    if not blocking:
        return ""
    # the effective one first: dislike x lever
    return min(blocking, key=lambda p: p["stance"] * (p.get("capacity") or 0.5))["name"]


def _counterfactual(parties: List[dict], satisfied: Sequence[str]) -> dict:
    """Re-run the room's arithmetic with those parties' conditions met."""
    room = [SETTLED if p["name"] in satisfied else p["stance"] for p in parties]
    value = friction(room)
    names = ", ".join(satisfied)
    return {
        "label": names,
        "friction": round(value, 1),
        "band": band(value),
        "veto_left": _veto_left([dict(p, stance=SETTLED if p["name"] in satisfied else p["stance"])
                                 for p in parties]),
    }


def ledger(personas: Sequence) -> dict:
    """The whole read for one finished room.

    ``personas`` are anything with ``name``, ``stance`` and ``capacity`` — the
    same dicts ``meta.json`` already stores, so this works on old runs too.
    """
    parties = []
    for p in personas or []:
        stance = getattr(p, "stance", None)
        if stance is None and isinstance(p, dict):
            stance = p.get("stance")
        if stance is None:
            continue
        parties.append({
            "name": getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else "?"),
            "stance": round(float(stance), 3),
            "capacity": (getattr(p, "capacity", None) if not isinstance(p, dict)
                         else p.get("capacity")),
        })
    if not parties:
        return {"available": False, "why": "no party had a stance to price"}

    stances = [p["stance"] for p in parties]
    phi = shapley(stances)
    total = friction(stances)
    baseline = friction([NEUTRAL] * len(stances))
    attributable = round(total - baseline, 1)

    rows = []
    for p, v in zip(parties, phi):
        share = (v / attributable * 100.0) if attributable else 0.0
        rows.append({
            "name": p["name"],
            "stance": p["stance"],
            "capacity": p["capacity"],
            "value": round(v, 1),
            "share": round(share, 1),
            "cools": v < -0.05,
            "veto": (p["stance"] < scoring.BLOCKER_THRESHOLD
                     and (p["capacity"] is None or p["capacity"] >= scoring.CAPACITY_MIN)),
        })
    rows.sort(key=lambda r: -r["value"])

    # Coalitions, two honest kinds.
    #
    # The friction function is additive in stances (an average plus two counts),
    # so a pair almost never costs *more heat* than the sum of its parts — the
    # "+6 interaction" of the design mockup does not exist in this model and is
    # not faked here. What a pair can do that neither half can is clear the veto
    # together. That is computed, and it is the claim worth printing.
    n = len(parties)
    pairs = []
    if n <= MAX_EXACT:
        vals = _values(stances)
        for i in range(n):
            for j in range(i + 1, n):
                both = vals[(1 << i) | (1 << j)]
                one = vals[1 << i] + vals[1 << j] - vals[0]
                inter = both - one
                ca = _counterfactual(parties, [parties[i]["name"]])["veto_left"]
                cb = _counterfactual(parties, [parties[j]["name"]])["veto_left"]
                cab = _counterfactual(parties, [parties[i]["name"], parties[j]["name"]])["veto_left"]
                if inter >= 0.5:
                    pairs.append({
                        "kind": "heat", "a": parties[i]["name"], "b": parties[j]["name"],
                        "interaction": round(inter, 1),
                        "together": round(both, 1), "apart": round(one, 1),
                        "line": (f"{parties[i]['name']} and {parties[j]['name']} cost "
                                 f"{inter:.1f} more heat together than apart"),
                    })
                elif ca or cb:
                    if not cab:
                        pairs.append({
                            "kind": "veto", "a": parties[i]["name"], "b": parties[j]["name"],
                            "interaction": 0.0, "together": round(both, 1),
                            "apart": round(one, 1),
                            "line": (f"clearing either one alone leaves a veto; "
                                     f"clearing both leaves none"),
                        })
        pairs.sort(key=lambda r: (r["kind"] != "veto", -r["interaction"]))

    # counterfactuals worth reading: each voter, the top pair, all blockers
    singles = [_counterfactual(parties, [r["name"]]) for r in rows if not r["cools"]][:4]
    both = []
    if pairs:
        both = [_counterfactual(parties, [pairs[0]["a"], pairs[0]["b"]])]
    blockers = [r["name"] for r in rows if r["veto"]]
    everyone = [_counterfactual(parties, blockers)] if len(blockers) > 1 else []
    # the same two names can arrive by two routes (top pair, and every blocker);
    # one row per scenario, first occurrence wins
    seen, counterfactuals = set(), []
    for cf in singles + both + everyone:
        if cf["label"] not in seen:
            seen.add(cf["label"])
            counterfactuals.append(cf)

    return {
        "available": True,
        "baseline": round(baseline, 1),
        "total": round(total, 1),
        "attributable": attributable,
        "band": band(total),
        "parties": rows,
        "pairs": pairs[:3],
        "counterfactuals": counterfactuals,
        "method": ("exact Shapley over the room's friction function, each party "
                   f"neutralised in turn ({1 << n} subsets)"),
        "subsets": 1 << n,
    }


def ledger_for_run(run: dict) -> dict:
    """`reporting.load_run()` output → the ledger for that room."""
    return ledger((run.get("meta") or {}).get("personas") or [])
