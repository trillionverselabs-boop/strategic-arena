"""Frozen, checkable claims. No claim, no run: a report you cannot score is marketing."""

from __future__ import annotations

import uuid
from typing import List

from .models import SimulationResult

EXTRACT_CLAIMS_PROMPT = """Read the documents and list the factual claims that a stakeholder
reaction depends on. For each one, quote the source span it came from. Max 8.

Respond with ONLY valid JSON:
{{"claims": [{{"claim": "...", "source": "exact quoted span from the document"}}]}}

DOCUMENTS:
{docs}
"""


def build_claims(result: SimulationResult) -> List[dict]:
    """Deterministic claims derived only from this run. Each is scorable yes/no."""
    claims: List[dict] = []
    window = f"{result.rounds} rounds"

    if result.blocker:
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "veto_player",
            "claim": (f"{result.blocker.name} is the binding constraint on this "
                      f"decision within {window}."),
            "expected": {"subject": result.blocker.name,
                         "stance": round(result.blocker.stance, 2)},
            "source": (result.blocker.reasons[0] if result.blocker.reasons else ""),
        })
    else:
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "no_veto_player",
            "claim": f"No stakeholder blocks this decision within {window}.",
            "expected": {"subject": None},
            "source": "",
        })

    lo = max(0.0, result.friction - result.uncertainty)
    hi = min(100.0, result.friction + result.uncertainty)
    claims.append({
        "id": uuid.uuid4().hex[:8],
        "kind": "friction_band",
        "claim": (f"Observed friction will land between {lo:.0f} and {hi:.0f} "
                  f"(point estimate {result.friction:.0f} +/- {result.uncertainty:.0f})."),
        "expected": {"lo": round(lo, 1), "hi": round(hi, 1),
                     "point": round(result.friction, 1)},
        "source": "input quality score",
    })

    against = [c for c in result.camps
               if c.get("lean") == "against" and c.get("members")]
    if against:
        camp = max(against, key=lambda c: len(c.get("members", [])))
        members = list(camp["members"])
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "coalition",
            "claim": (f"The blocking camp ({', '.join(members)}) stays aligned "
                      f"against the decision."),
            "expected": {"members": members},
            "source": "camp clustering",
        })
    return claims


def extract_claims(result: SimulationResult, llm, documents) -> List[dict]:
    """Optional GraphRAG-style enrichment: claims quoted from the documents.

    Returns [] on any failure. The deterministic claims always stand.
    """
    from .ingestion import _docs_block, _parse_json

    try:
        raw = llm.complete(EXTRACT_CLAIMS_PROMPT.format(docs=_docs_block(documents)))
    except Exception:
        return []
    parsed = _parse_json(raw)
    if not parsed:
        return []
    out: List[dict] = []
    for c in parsed.get("claims", [])[:8]:
        if not isinstance(c, dict):
            continue
        text = str(c.get("claim", "")).strip()
        if not text:
            continue
        out.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "extracted",
            "claim": text,
            "expected": {},
            "source": str(c.get("source", "")).strip(),
        })
    return out
