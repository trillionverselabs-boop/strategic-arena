# Ingestion — documents -> stakeholders (personas) + relationships.
# The LLM extracts entities/relationships. Every extracted item carries a source
# ref so the report can tell the user *why* the sim thinks someone is against them.

from __future__ import annotations

import json
import re
from typing import List, Tuple

from .models import Document, Persona

# The real reason the last extraction failed, so the report can say "trust gate
# denied the model override" instead of "the model call failed".
LAST_ERROR = ""

# What the extraction understood the artifact to *say*, in three plain lines. Same
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
    "paper": """This is a RESEARCH PAPER (arXiv, DOI, journal, conference). The question is
NOT "is the method defensible" — that is the whitepaper lens. The question is: what
product does this make possible, and how will the market and the competitors take it?

The room is the market, not the reviewers:
- the incumbent whose revenue or roadmap the resulting product attacks
- the fast follower: a well-resourced competitor who has read the same paper and can
  ship it, and who already has distribution you do not
- the buyer who controls the budget for the resulting product — the person who signs,
  not the person who evaluates
- the integrator or platform owner, whose switching cost and compatibility rules are
  usually the real moat in this market
- the channel or marketplace that decides whether the product is even visible
- the authors, their lab, or their funder — for a published result these are the most
  likely first competitor, and they are usually omitted by mistake
- a regulator or standards body, only when the paper's claims create a compliance
  obligation for a buyer

Judge each party on the paper's actual content: what it discloses, what it withholds,
the magnitude of the claimed gain, what it is measured against, and whether the result
depends on resources only a few organisations have. ``capacity`` here means the ability
to REBUILD OR SHIP the product this paper implies — not to review it.""",
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
    # A research paper is read for a market question, a vendor whitepaper for a
    # defensibility question — so the hosts that only ever serve research papers
    # resolve to the paper lens. A bare .pdf stays whitepaper: it could be either,
    # and guessing "paper" would silently swap the room.
    if any(h in blob for h in ("arxiv.org", "doi.org", "ssrn.com", "biorxiv.org",
                               "medrxiv.org", "openreview.net", "aclanthology.org",
                               "proceedings.mlr.press", "openaccess.thecvf.com")):
        return "paper"
    if blob.endswith(".pdf"):
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

Also write the READ: what this artifact actually says, in plain words, using only
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
    "whitepaper": "a technical whitepaper or spec",
    "paper": "a research paper, read for the product it implies",
    "case_study": "a case study",
    "press": "a press release",
    "tweet": "a social post",
    "decision": "a decision document",
}

# ── prompt budget ─────────────────────────────────────────────────────
# An arXiv HTML page is up to 50k characters, of which the first ~2k is a table
# of contents and a theme switcher. Two calls read that blob before the room
# exists (the moat decode, then the persona extraction), on a free model — and a
# paper run never once completed in the field while decision runs did. The model
# does not need the whole paper for either question: it needs the claim, the
# setup, the results and the limitations. So a document is windowed head and
# tail, and the middle is dropped with an honest marker.
PROMPT_BUDGET = 12_000


# A paper's last pages are a bibliography: thousands of characters of names and
# dates that carry no claim, sitting exactly where the window's tail is.
_REF_HEADING = re.compile(r"^\s*(References|Bibliography|REFERENCES)\s*$", re.M)


def _drop_toc(text: str) -> str:
    """Start at the *real* Abstract heading.

    arXiv's HTML opens with a table of contents that lists "Abstract" as its
    first line — so the first match is the TOC, not the section. The heading we
    want is the last standalone "Abstract" near the top of the page; the TOC
    comes before it.
    """
    matches = [m for m in re.finditer(r"^Abstract\s*$", text, re.M) if m.start() < 8_000]
    if matches:
        return text[matches[-1].start():]
    return text


def _cut_references(text: str) -> str:
    """Drop the bibliography, so the tail is conclusions and limitations.

    Guarded by position: a "References" line inside the table of contents sits
    early in the page, and cutting there would throw the paper away.
    """
    m = _REF_HEADING.search(text)
    if m and m.start() > len(text) * 0.4:
        return text[:m.start()]
    return text


def excerpt(text: str, budget: int = PROMPT_BUDGET) -> str:
    """A prompt-sized window: head (claim, setup) + tail (results, limits).

    Head-heavy on purpose — a paper's opening states the claim and the setup;
    its ending states what it could not do, which is what a replication clock is
    made of. The middle of a paper is derivation the reader can live without.
    """
    text = _cut_references(_drop_toc(text or ""))
    if len(text) <= budget:
        return text
    head_n = int(budget * 0.6)
    tail_n = budget - head_n
    dropped = len(text) - head_n - tail_n
    return (text[:head_n].rstrip()
            + f"\n\n[... {dropped} characters omitted from the middle of this document ...]\n\n"
            + text[-tail_n:].lstrip())


def _docs_block(documents: List[Document], budget: int = PROMPT_BUDGET) -> str:
    """Documents as one prompt block, each windowed to its share of the budget.

    The budget is per *call*, split evenly: one 50k paper and five short
    documents must cost the same prompt.
    """
    per = max(1_500, budget // max(1, len(documents)))
    out = []
    for d in documents:
        label = d.source or d.type.value
        out.append(f"[{d.type.value}] ({label})\n{excerpt(d.content, per)}")
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
