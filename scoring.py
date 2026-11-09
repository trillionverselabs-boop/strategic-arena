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


def find_blocker(personas: List[Persona]) -> Persona | None:
    """The veto player — or None when nobody is meaningfully against the move."""
    if not personas:
        return None
    worst = min(personas, key=lambda p: p.stance)
    return worst if worst.stance < BLOCKER_THRESHOLD else None


def build_counter_moves(blocker: Persona, result: SimulationResult) -> List[str]:
    if blocker is None or blocker.stance >= BLOCKER_THRESHOLD:
        return []
    moves = [
        f"Address {blocker.name}'s core objection directly before launch — it drives their stance.",
    ]
    champions = [p for p in result.personas if p.stance > 0.5]
    if champions:
        moves.append(f"Have {champions[0].name} carry the announcement — they already lean in.")
    grounded = [r for r in blocker.reasons if r]
    if grounded:
        moves.append(f"Rebut the claim in: {grounded[0]} — that's their load-bearing reason.")
    return moves


def sea_state(result: SimulationResult) -> dict:
    """Competition read. High competition = red, medium = purple, low = blue.

    Separate scale from per-stakeholder stance colour (red/amber/green) so the
    two never get conflated: this is about the landscape, not about one player.
    """
    against = [c for c in result.camps if c.get("lean") == "against"]
    hard_veto = result.blocker is not None and result.blocker.stance < -0.7
    f = result.friction

    if hard_veto or len(against) >= 2 or f >= 65:
        if hard_veto:
            why = f"hard veto player ({result.blocker.name} {result.blocker.stance:+.2f})"
        elif len(against) >= 2:
            why = f"{len(against)} blocking camps"
        else:
            why = f"friction {f:.0f}/100"
        key = "red"
    elif f < 35 and not against:
        key, why = "blue", f"no blocking camp, friction {f:.0f}/100"
    else:
        key, why = "purple", f"friction {f:.0f}/100 with {len(against) or 'no'} blocking camp(s)"

    return {
        "state": key,
        "level": SEA[key]["level"],
        "label": SEA[key]["label"],
        "color": SEA[key]["color"],
        "meaning": SEA[key]["meaning"],
        "why": why,
        "order": SEA_ORDER,
    }
