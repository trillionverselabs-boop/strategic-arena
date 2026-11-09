# Ingestion — GraphRAG: documents -> stakeholders (personas) + relationships.
# The LLM extracts entities/relationships. Every extracted item carries a source
# ref so the report can tell the user *why* the sim thinks someone is against them.

from __future__ import annotations

import json
from typing import List, Tuple

from .models import Document, Persona

EXTRACT_PROMPT = """You are extracting the stakeholder landscape from a decision document.

Read the documents. Identify the people, groups, and orgs whose reaction matters
to this decision (max {max_personas}). For each one give:
- name: short display name (e.g. "Enterprise IT", "The Community")
- role: one word (e.g. "blocker", "champion", "user", "regulator", "competitor")
- stance: -1 (will fight this) to +1 (wants this), based ONLY on what the document says
- reason: one sentence, with a source marker like [evidence ¶2] quoting the doc
- source: which document type and paragraph backs this

Also list relationships: pairs that oppose or support each other, as [name_a, name_b, label].

Respond with ONLY valid JSON matching this shape:
{{
  "personas": [{{"name": "...", "role": "...", "stance": 0.0, "reason": "...", "source": "..."}}],
  "relationships": [["...", "...", "opposes"]]
}}

DOCUMENTS:
{docs}
"""


def _docs_block(documents: List[Document]) -> str:
    out = []
    for d in documents:
        label = d.source or d.type.value
        out.append(f"[{d.type.value}] ({label})\n{d.content}")
    return "\n\n".join(out)


def extract_personas(
    documents: List[Document], llm, max_personas: int = 8
) -> Tuple[List[Persona], List[Tuple[str, str, str]]]:
    """documents -> (personas, relationships). llm: ctx.llm (has .complete)."""
    prompt = EXTRACT_PROMPT.format(max_personas=max_personas, docs=_docs_block(documents))
    try:
        raw = llm.complete(prompt)
    except Exception:
        return [], []
    parsed = _parse_json(raw)
    if parsed is None:
        return [], []
    personas: List[Persona] = []
    for p in parsed.get("personas", [])[:max_personas]:
        try:
            personas.append(
                Persona(
                    name=str(p.get("name", "Stakeholder")),
                    role=str(p.get("role", "stakeholder")),
                    stance=_clamp(float(p.get("stance", 0.0))),
                    reasons=[str(p.get("reason", ""))] if p.get("reason") else [],
                )
            )
        except Exception:
            continue
    rels: List[Tuple[str, str, str]] = []
    for r in parsed.get("relationships", []):
        if isinstance(r, (list, tuple)) and len(r) >= 3:
            rels.append((str(r[0]), str(r[1]), str(r[2])))
    return personas, rels


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def _parse_json(raw) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    text = str(raw)
    # strip code fences
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None
