# Scoring — friction score (0-100) with calibration from input quality.
# Friction = how hard this decision will be to land. Uncertainty comes from
# how thin the input was, NOT from the LLM's mood.

from __future__ import annotations

from typing import List, Tuple

from .models import Document, Persona, SimulationResult


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
    # negative stance mass: how many people are against it, and how hard
    neg_mass = sum(1.0 for p in personas if p.stance < -0.3)
    strong_neg = sum(1.0 for p in personas if p.stance < -0.7)
    avg_stance = sum(p.stance for p in personas) / len(personas)
    # friction: base from avg stance (inverted), plus blockers
    base = (1.0 - avg_stance) / 2.0 * 70          # 0..70
    blocker_part = min(30, neg_mass * 10 + strong_neg * 10)  # 0..30
    friction = max(0.0, min(100.0, base + blocker_part))
    uncertainty = round((1.0 - input_quality) * 30.0 + 3.0, 1)  # thin input -> wide ±
    return round(friction, 1), uncertainty


def find_blocker(personas: List[Persona]) -> Persona | None:
    if not personas:
        return None
    return min(personas, key=lambda p: p.stance)


def build_counter_moves(blocker: Persona, result: SimulationResult) -> List[str]:
    if blocker is None or blocker.stance >= -0.3:
        return []
    moves = [
        f"Address {blocker.name}'s core objection directly before launch — it drives their stance.",
    ]
    # widen: if a champion exists, use them to carry the message
    champions = [p for p in result.personas if p.stance > 0.5]
    if champions:
        moves.append(f"Have {champions[0].name} carry the announcement — they already lean in.")
    # evidence-backed: cite the strongest grounded reason
    grounded = [r for r in blocker.reasons if r]
    if grounded:
        moves.append(f"Rebut the claim in: {grounded[0]} — that's their load-bearing reason.")
    return moves
