# Scoring — friction (0-100) calibrated by input quality, the veto player, and the
# competition read (red / purple / blue). Uncertainty comes from how thin the
# input was, NOT from the LLM's mood.

from __future__ import annotations

from typing import List, Tuple

from .models import Document, Persona, SimulationResult

BLOCKER_THRESHOLD = -0.3

# Competition axis, ordered left -> right: red (everyone fighting for the same
# fish) -> purple (a real contest with winnable ground) -> blue (open water).
SEA = {
    "red":    {"level": "high",   "label": "Red ocean",    "color": "#e5484d",
               "meaning": "everyone is fighting for the same fish"},
    "purple": {"level": "medium", "label": "Purple ocean", "color": "#8b5cf6",
               "meaning": "contested middle — a real fight with winnable ground"},
    "blue":   {"level": "low",    "label": "Blue ocean",   "color": "#3b82f6",
               "meaning": "open water — nobody is contesting this"},
}
SEA_ORDER = ["red", "purple", "blue"]  # red on the left, blue on the right

# Not on the axis: the axis is a competition scale, and this is the absence of a
# read. Printed when blue cannot be earned — see sea_state().
INSUFFICIENT = {
    "level": "unknown",
    "label": "Insufficient input",
    "color": "#6b7280",
    "meaning": "Nobody who could contest this was identified, so 'uncontested' "
               "cannot be claimed. Add the parties who could stop it, or the "
               "document that names them.",
}

# A party must be at least this able to block before their restraint counts as
# evidence of open water.
CAPACITY_MIN = 0.5


def score_input(documents: List[Document]) -> Tuple[float, str, List[str]]:
    """Return (quality 0..1, confidence, suggestions). Thin input = low confidence."""
    if not documents:
        return 0.0, "low", ["Add at least one decision document."]
    n = len(documents)
    has_evidence = any(d.type.value == "evidence" for d in documents)
    has_decision = any(d.type.value == "decision" for d in documents)
    quality = 0.30 + 0.15 * min(n, 3)
    if has_decision:
        quality += 0.15
    if has_evidence:
        quality += 0.25
    quality = min(1.0, quality)
    confidence = "high" if quality >= 0.75 else ("medium" if quality >= 0.5 else "low")
    suggestions = []
    if not has_evidence:
        suggestions.append("Add an evidence document (real data/quotes) for grounded stances.")
    if n < 2:
        suggestions.append("Add a second document to give the sim more to ground on.")
    return quality, confidence, suggestions


def friction_score(result: SimulationResult, input_quality: float) -> Tuple[float, float]:
    """Return (friction 0..100, uncertainty ±)."""
    personas = result.personas
    if not personas:
        return 0.0, 20.0
    neg_mass = sum(1.0 for p in personas if p.stance < -0.3)
    strong_neg = sum(1.0 for p in personas if p.stance < -0.7)
    avg_stance = sum(p.stance for p in personas) / len(personas)
    base = (1.0 - avg_stance) / 2.0 * 70          # 0..70
    blocker_part = min(30, neg_mass * 10 + strong_neg * 10)  # 0..30
    friction = max(0.0, min(100.0, base + blocker_part))
    uncertainty = round((1.0 - input_quality) * 30.0 + 3.0, 1)  # thin input -> wide ±
    return round(friction, 1), uncertainty


def _power(persona: Persona) -> float:
    """How much this party's stance actually matters: dislike x ability to stop it.

    "Who can challenge" is not "who is angriest". A vocal party with no lever moves
    the read far less than a quiet party who controls the budget or the licence.
    Unassessed capacity gets the benefit of the doubt (0.5) — unknown is not zero.
    """
    cap = getattr(persona, "capacity", None)
    return 0.5 if cap is None else max(0.0, min(1.0, float(cap)))


def find_blocker(personas: List[Persona]) -> Persona | None:
    """The veto player — or None when nobody is meaningfully against the move."""
    if not personas:
        return None
    negative = [p for p in personas if p.stance < BLOCKER_THRESHOLD]
    if not negative:
        return None
    # Most *effective* objection first: a -1.0 with capacity 0 cannot stop anything,
    # while a -0.6 with capacity 0.9 is the person you actually have to talk to.
    return min(negative, key=lambda p: p.stance * _power(p))


def _poss(name: str) -> str:
    """Singular possessive that survives names already ending in s."""
    n = (name or "they").strip()
    return f"{n}'" if n.lower().endswith("s") else f"{n}'s"


def build_counter_moves(blocker: Persona, result: SimulationResult) -> List[str]:
    if blocker is None or blocker.stance >= BLOCKER_THRESHOLD:
        return []
    moves = [
        f"Address {_poss(blocker.name)} core objection directly before launch — it drives their stance.",
    ]
    champions = [p for p in result.personas if p.stance > 0.5]
    if champions:
        moves.append(f"Have {champions[0].name} carry the announcement — they already lean in.")
    grounded = [r for r in blocker.reasons if r]
    if grounded:
        moves.append(f"Rebut the claim in: {grounded[0]} — that's their load-bearing reason.")
    return moves


def _camp_is_a_fight(camp: dict, personas: List[Persona]) -> bool:
    """Does this coalition actually have someone who can stop the move?

    A camp is a cluster of people, and a cluster of mild complainers is not a fight.
    We resolve its members to the personas we know; if none of them has both the
    dislike and the lever, it does not count as a blocking camp. When a member's
    stance or capacity is unknown we assume it blocks — never guess that a fight
    is harmless.
    """
    names = set(camp.get("members") or [])
    members = [p for p in personas if p.name in names]
    if not members:
        return True
    return any(p.stance < BLOCKER_THRESHOLD and _power(p) >= CAPACITY_MIN
               for p in members)


def sea_state(result: SimulationResult) -> dict:
    """Competition read. High competition = red, medium = purple, low = blue.

    Separate scale from per-stakeholder stance colour (red/amber/green) so the
    two never get conflated: this is about the landscape, not about one player.
    """
    against = [c for c in result.camps if c.get("lean") == "against"]
    # A hard veto needs both dislike and a lever. Anger without capacity is noise.
    hard_veto = (result.blocker is not None
                 and result.blocker.stance < -0.7
                 and _power(result.blocker) >= CAPACITY_MIN)
    blocking_camps = [c for c in against if _camp_is_a_fight(c, result.personas)]
    f = result.friction

    if hard_veto or len(blocking_camps) >= 2 or f >= 65:
        if hard_veto:
            why = f"hard veto player ({result.blocker.name} {result.blocker.stance:+.2f})"
        elif len(blocking_camps) >= 2:
            why = f"{len(blocking_camps)} blocking camps"
        else:
            why = f"friction {f:.0f}/100"
        key = "red"
    elif f < 35 and not blocking_camps:
        key, why = "blue", f"no blocking camp, friction {f:.0f}/100"
    else:
        key, why = "purple", f"friction {f:.0f}/100 with {len(blocking_camps) or 'no'} blocking camp(s)"

    # Blue must be earned. "Nobody objected" is not "nobody could" — the Arete run
    # named no opponent at all and printed Blue ocean, which is an empty room
    # described as open water. Blue is only printable with a named party who could
    # contest it and a reason they don't.
    if key == "blue":
        contestable = []
        for p in result.personas:
            cap = getattr(p, "capacity", None)
            if cap is not None and cap >= CAPACITY_MIN:
                contestable.append((cap, p))
        if not result.personas:
            key = "insufficient"
            why = "no party was named in the input — an empty room is not open water"
        elif not contestable:
            unassessed = any(getattr(p, "capacity", None) is None for p in result.personas)
            key = "insufficient"
            why = (
                "no party's capacity to contest was assessed" if unassessed
                else "no named party could have contested this"
            )
        else:
            cap, strongest = max(contestable, key=lambda pair: pair[0])
            why = (
                f"{strongest.name} could contest this (capacity {cap:.1f}) "
                f"and does not — friction {f:.0f}/100"
            )

    if key == "insufficient":
        return {
            "state": "insufficient",
            "level": INSUFFICIENT["level"],
            "label": INSUFFICIENT["label"],
            "color": INSUFFICIENT["color"],
            "meaning": INSUFFICIENT["meaning"],
            "why": why,
            "order": SEA_ORDER,
        }

    return {
        "state": key,
        "level": SEA[key]["level"],
        "label": SEA[key]["label"],
        "color": SEA[key]["color"],
        "meaning": SEA[key]["meaning"],
        "why": why,
        "order": SEA_ORDER,
    }
