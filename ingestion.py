# Ingestion — documents -> stakeholders (personas) + relationships.
# The LLM extracts entities/relationships. Every extracted item carries a source
# ref so the report can tell the user *why* the sim thinks someone is against them.

from __future__ import annotations

import json
from typing import List, Tuple

from .models import Document, Persona

# The real reason the last extraction failed, so the report can say "trust gate
# denied the model override" instead of "the model call failed".
LAST_ERROR = ""

# What the extraction understood the artefact to *say*, in three plain lines. Same
# model call, one more key — the page needs "what does this mean" answered by the
# reader of the text, not assembled by a template afterwards.
LAST_READ: dict = {}

# ── the lens ──────────────────────────────────────────────────────────
# Reception depends on the medium. A README is judged by maintainers deciding
# whether to merge and security reviewers deciding whether to allow the install;
# a tweet is judged by the people who quote it. Same engine, different room —
# so the extraction question is set by what was handed in.

KIND_BLOCKS = {
    "repo": """This is a REPOSITORY / README. The room is:
- the maintainers who decide whether this merges or gets closed
- security and supply-chain reviewers who decide whether the install is allowed
- downstream developers deciding whether to pip/npm install and adopt it
- the competing project this displaces (say plainly what it replaces)
- the package registry / marketplace that lists it
Judge each on what the file actually promises: install steps, licence, benchmarks,
claims of support, and what it says about the incumbent.""",
    "post": """This is a BLOG POST / ESSAY. The room is:
- the reader who will quote one line back at the author
- the competitor whose position the post attacks
- any party the post names or cites (they will read it)
- the curator/newsletter that decides whether it travels
- the reader who is the actual buyer of the thing described
Judge each on the claims the post makes and the evidence it puts behind them.""",
    "whitepaper": """This is a WHITEPAPER / PAPER / SPEC. The room is:
- the technical reviewer who will check the method and the numbers
- procurement and compliance, who need it to be defensible
- the peer or analyst whose prior work it extends or contradicts
- the implementer who has to build from it
Judge each on rigour: baselines, evaluation, reproducibility, and what is asserted
without evidence.""",
    "case_study": """This is a CASE STUDY. The room is:
- the customer named in it, whose approval to publish is itself a gate
- the buyer persona who will not believe it without a comparable
- procurement, who need the numbers to be auditable
- the competitor in the same evaluation
Judge each on whether the proof is specific enough to survive a skeptical read.""",
    "press": """This is a PRESS RELEASE / ANNOUNCEMENT. The room is:
- the journalist deciding whether it is a story or a mail
- the incumbent it positions against
- the regulator or standards body with standing in this area
- existing customers, who read it as a signal about them
Judge each on the claim that headlines it and the specifics beneath it.""",
    "tweet": """This is a SINGLE SOCIAL POST. The room is:
- the reply-guy who will find the weakest clause
- the quote-tweeter who reframes it for their own audience
- the silent majority who only see the number or the claim
- the account or company it names
Judge each on what can be screenshotted and misread.""",
    "decision": """This is an INTERNAL DECISION / PLAN. The room is the people inside and
outside the company whose reaction decides whether it happens: approvers with a
veto, teams whose work changes, customers, and the market it enters.""",
}


def detect_kind(urls: List[str] | None, text: str = "") -> str:
    """Best guess from the link, then the words. Never guessed into a corner: the
    caller may override, and 'decision' is the honest default."""
    blob = " ".join(urls or []).lower()
    body = (text or "").lower()
    if any(h in blob for h in ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")):
        return "repo"
    if any(h in blob for h in ("x.com/", "twitter.com/", "bsky.app", "threads.net")):
        return "tweet"
    if any(h in blob for h in ("arxiv.org", "doi.org", "ssrn.com")) or blob.endswith(".pdf"):
        return "whitepaper"
    if any(h in blob for h in ("prnewswire", "businesswire", "globenewswire")) or "press release" in body[:600]:
        return "press"
    if "case study" in body[:600] or "case-study" in blob:
        return "case_study"
    if any(h in blob for h in ("/blog/", "medium.com", "substack.com", "/posts/")):
        return "post"
    if body.startswith("readme") or "# installation" in body[:1200]:
        return "repo"
    return "decision"


EXTRACT_PROMPT = """You are extracting the stakeholder landscape from {what}.

{lens}

Read the documents. Identify the people, groups, and orgs whose reaction decides
what happens next (max {max_personas}). For each one give:
- name: short display name (e.g. "Enterprise IT", "The Community")
- role: one word (e.g. "blocker", "champion", "user", "regulator", "competitor")
- stance: -1 (will fight this) to +1 (wants this), based ONLY on what the document says
- capacity: 0.0-1.0, how able this party is to BLOCK or materially change the outcome
  (budget, veto, licence, procurement rule, public position). Use 0.0 for a party
  that has an opinion but no power. Omit the field if the document does not say.
- reasons: 2 to 3 sentences, EACH carrying its own source marker like [evidence ¶2]
  or [decision ¶1]. Two independent reasons beat one long one: the page shows them
  separately, and a claim grounded twice is a claim you can defend. Use the same
  party only once; do not repeat a reason in different words.
- source: which document type and paragraph backs this

Also write the READ: what this artefact actually says, in plain words, using only
what is in it.
- claim: one sentence — the central promise or assertion being made
- displaces: one sentence — what it replaces, undercuts or competes with (or "" if
  it claims no ground)
- opening: one sentence — the opportunity it creates for a reader who wants to
  build on it (or "" if there is none)
Each must be grounded in the text; no marketing adjectives, no advice.

Also list relationships: pairs that oppose or support each other, as [name_a, name_b, label].

Respond with ONLY valid JSON matching this shape:
{{
  "personas": [{{"name": "...", "role": "...", "stance": 0.0, "capacity": 0.0,
                "reasons": ["... [evidence ¶2]", "... [decision ¶1]"], "source": "..."}}],
  "read": {{"claim": "...", "displaces": "...", "opening": "..."}},
  "relationships": [["...", "...", "opposes"]]
}}

DOCUMENTS:
{docs}
"""

WHAT = {
    "repo": "a repository README",
    "post": "a blog post",
    "whitepaper": "a technical paper or spec",
    "case_study": "a case study",
    "press": "a press release",
    "tweet": "a social post",
    "decision": "a decision document",
}

def _docs_block(documents: List[Document]) -> str:
    out = []
    for d in documents:
        label = d.source or d.type.value
        out.append(f"[{d.type.value}] ({label})\n{d.content}")
    return "\n\n".join(out)


def extract_personas(
    documents: List[Document], llm, max_personas: int = 8, kind: str = "decision"
) -> Tuple[List[Persona], List[Tuple[str, str, str]]] | None:
    """documents -> (personas, relationships), or None when the model call failed.

    None means "we do not know" — never "nobody". The engine refuses to invent
    stakeholders when this returns None.
    """
    kind = kind if kind in KIND_BLOCKS else "decision"
    prompt = EXTRACT_PROMPT.format(
        what=WHAT[kind], lens=KIND_BLOCKS[kind],
        max_personas=max_personas, docs=_docs_block(documents))
    global LAST_ERROR
    try:
        raw = llm.complete(prompt)
    except Exception as exc:
        LAST_ERROR = f"{type(exc).__name__}: {exc}"
        return None
    parsed = _parse_json(raw)
    if parsed is None:
        LAST_ERROR = ("the model answered but not as JSON the plugin could read "
                      f"(got: {str(raw)[:160]!r})")
        return None
    global LAST_READ
    LAST_READ = _read(parsed.get("read"))
    personas: List[Persona] = []
    for p in parsed.get("personas", [])[:max_personas]:
        try:
            personas.append(
                Persona(
                    name=str(p.get("name", "Stakeholder")),
                    role=str(p.get("role", "stakeholder")),
                    stance=_clamp(float(p.get("stance", 0.0))),
                    capacity=_unit(p.get("capacity")),
                    reasons=_reasons(p),
                )
            )
        except Exception:
            continue
    rels: List[Tuple[str, str, str]] = []
    for r in parsed.get("relationships", []):
        if isinstance(r, (list, tuple)) and len(r) >= 3:
            rels.append((str(r[0]), str(r[1]), str(r[2])))
    return personas, rels


def _read(raw) -> dict:
    """The three-line interpretation, or {} when the model did not give one.

    Empty is honest: the page hides the block rather than printing a template that
    pretends to have understood something.
    """
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key in ("claim", "displaces", "opening"):
        val = str(raw.get(key) or "").strip()
        if val:
            out[key] = val
    return out if out.get("claim") else {}


def _reasons(p: dict) -> List[str]:
    """2-3 grounded reasons, or one. Never a fabricated second line to fill a slot."""
    out: List[str] = []
    raw = p.get("reasons")
    if isinstance(raw, list):
        out = [str(r).strip() for r in raw if str(r).strip()]
    if not out and p.get("reason"):
        out = [str(p["reason"]).strip()]
    # de-duplicate identical lines, keep order, cap at 3
    seen, kept = set(), []
    for r in out:
        k = r.lower()[:80]
        if k not in seen:
            seen.add(k)
            kept.append(r)
    return kept[:3]


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def _unit(x) -> float | None:
    """0..1 capacity, or None when the document did not say. Never guessed."""
    if x is None or x == "":
        return None
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return None


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
