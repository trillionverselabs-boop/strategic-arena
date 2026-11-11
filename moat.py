"""Moat decode — a research paper read as a product, not as a citation.

A paper is the one artifact where **the document is the moat giveaway**. Publication
converts the technique into a public good, so "how will the market take this?" stops
being a question about sentiment and becomes a question about two clocks:

    how long until a funded competitor can rebuild it from the text  vs
    how long until you can ship it

Everything here is decoded from the paper's own text and reported with its evidential
basis. Nothing is estimated by eye, and a field the paper does not support is left
empty rather than filled with a plausible number — an invented replication clock is
worse than no clock, because it looks like data.

The clock is *computed* from the decoded fields (``clock_for``), never asked of the
model. Same discipline as leverage.py: the model supplies facts, the code supplies
the judgement, so two runs of the same paper cannot disagree about the band.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from pydantic import BaseModel, Field

# ── what a decode returns ──────────────────────────────────────────────

class Moat(BaseModel):
    """The product reading of one paper."""

    # the product thesis — the paper does not contain a product, so this is the
    # conversion step and it is the first thing a reader needs
    product: str = ""        # what a team could build from this, one sentence
    buyer: str = ""          # who signs the cheque — a role, not a category
    replaces: str = ""       # what it displaces, or "" when it displaces nothing

    # the clock inputs
    disclosed: List[str] = Field(default_factory=list)   # rebuildable from the text
    tacit: List[str] = Field(default_factory=list)       # what the text does NOT give
    replication_months: Optional[float] = None           # None = the paper does not say
    replication_basis: str = ""      # the evidence for that number, in one clause
    scale_dependence: str = ""       # does it only hold at resources few labs have
    nearest_prior_art: str = ""      # who is already one paper away
    authors_position: str = ""       # are the authors themselves the first competitor

    # derived, never asked
    clock: str = "unknown"           # commodity / contested / protected / unknown
    clock_why: str = ""

    confidence: str = "low"
    error: str = ""                  # why the decode did not happen, when it did not

    def brief(self) -> str:
        """The decode as a document the room can stand on.

        Fed back in as a CONTEXT document so the stakeholders arguing about the
        product know what the public already knows — which is the whole point:
        a competitor in the room has read this.
        """
        bits = ["MOAT DECODE — what the publication itself gives away."]
        if self.product:
            bits.append(f"Product that could be built: {self.product}")
        if self.buyer:
            bits.append(f"Who pays: {self.buyer}")
        if self.replaces:
            bits.append(f"What it displaces: {self.replaces}")
        if self.disclosed:
            bits.append("Reproducible from the text alone: " + "; ".join(self.disclosed))
        if self.tacit:
            bits.append("NOT in the paper: " + "; ".join(self.tacit))
        if self.replication_months is not None:
            bits.append(f"Replication time for a funded team: ~{self.replication_months:.0f} "
                        f"months ({self.replication_basis or 'basis not stated'})")
        else:
            bits.append("Replication time: not stated by the paper — unassessed.")
        if self.scale_dependence:
            bits.append(f"Scale dependence: {self.scale_dependence}")
        if self.nearest_prior_art:
            bits.append(f"Nearest prior art: {self.nearest_prior_art}")
        if self.authors_position:
            bits.append(f"Authors' own position: {self.authors_position}")
        bits.append(f"Moat clock: {self.clock}"
                    + (f" — {self.clock_why}" if self.clock_why else ""))
        return "\n".join(bits)


# ── the clock, computed ────────────────────────────────────────────────

COMMODITY_MONTHS = 3.0    # a release cycle: a feature, not a company
CONTESTED_MONTHS = 9.0    # a real head start, if you spend it well


def clock_for(months: Optional[float], tacit: List[str], scale: str) -> tuple[str, str]:
    """(band, why) — the judgement, made once, in code.

    ``None`` is not "protected". An unstated replication time is unknown, and a run
    that prints "protected" on an unassessed field would be the same failure the sea
    read refuses to make when it declines to print blue ocean for an empty room.
    """
    if months is None:
        return "unknown", "the paper does not state enough to estimate replication time"
    months = max(0.0, float(months))
    if months <= COMMODITY_MONTHS:
        return ("commodity",
                f"~{months:.0f} months to rebuild — inside a normal release cycle, so the "
                "technique will ship as a feature in an incumbent's product")
    if months <= CONTESTED_MONTHS:
        held = "tacit work and " if tacit else ""
        return ("contested",
                f"~{months:.0f} months to rebuild — a real head start, but it is "
                f"{held}execution that keeps it, not the paper")
    # long replication is only a moat when something explains it
    if tacit or (scale or "").strip().lower() not in ("", "none", "low"):
        return ("protected",
                f"~{months:.0f} months to rebuild — the gap is held by "
                + ("undisclosed method" if tacit else "")
                + (" and " if tacit and scale else "")
                + (f"resources ({scale})" if scale else ""))
    return ("contested",
            f"~{months:.0f} months to rebuild, but the paper discloses no tacit advantage "
            "to explain the gap — treat the estimate as soft")


# ── the decode ─────────────────────────────────────────────────────────

DECODE_PROMPT = """You are reading a research paper the way a founder reads it: not for
whether it is good, but for what product it makes possible and how long the advantage
would last once it is published.

Read the documents. Publication is the moat giveaway: anything written down can be
rebuilt by anyone. Your job is to separate what the paper GIVES AWAY from what it
holds back, and to state the clock that follows.

Answer these, and give an empty string or an empty list wherever the paper does not
support an answer. Never guess a number to fill a field — an invented replication
time is worse than none, because it looks like data.

- product: what a competent team could actually build and sell from this. One
  sentence, concrete, naming the thing a buyer would pay for. If it is a measurement
  or a caution rather than a technique, say so — "a verification gate that ..." is a
  product; "a better method" is not.
- buyer: the role that signs the cheque (e.g. "the inference-platform lead", "the
  procurement officer at an integrator") — not a market category.
- replaces: what existing product, line item or workflow this displaces, or "".
- disclosed: up to 4 things a stranger can rebuild from the text alone — algorithm,
  architecture, loss, recipe. Short noun phrases.
- tacit: up to 4 things the paper does NOT give, that a rebuilder would still need —
  data pipeline, hyperparameters, eval harness, hardware recipe, undocumented
  preprocessing. Empty when the paper is genuinely complete.
- replication_months: months for a funded, competent team to reproduce the headline
  result from the text as published. A number. Use null when the paper gives no basis
  for one (this is common and is the honest answer).
- replication_basis: one clause naming the evidence for that number ("three backbones
  re-trained on 180s video per the appendix").
- scale_dependence: does the result hold at a fraction of the compute/data, or does it
  need resources only a few labs have? One sentence, quote the magnitude if given.
- nearest_prior_art: who is already one paper or one release away from this.
- authors_position: are the authors themselves the first competitor — employed by a
  lab that ships products, funded by one, or already commercialising? One sentence,
  grounded in affiliations or acknowledgements, or "".
- confidence: "high" when the paper state disclosure, method and results plainly;
  "medium" when some is missing; "low" when the paper is thin or mostly a survey.

Respond with ONLY valid JSON:
{{
  "product": "...", "buyer": "...", "replaces": "...",
  "disclosed": ["..."], "tacit": ["..."],
  "replication_months": null, "replication_basis": "...",
  "scale_dependence": "...", "nearest_prior_art": "...",
  "authors_position": "...", "confidence": "low"
}}

DOCUMENTS:
{docs}
"""

MAX_CHARS = 24000   # a decode needs the method and results, not the whole appendix


def _docs_block(documents) -> str:
    out, total = [], 0
    for d in documents:
        label = getattr(d, "source", "") or getattr(getattr(d, "type", None), "value", "doc")
        body = str(getattr(d, "content", "") or "")
        chunk = f"[{label}]\n{body}"
        if total + len(chunk) > MAX_CHARS:
            chunk = chunk[: max(0, MAX_CHARS - total)]
        if chunk.strip():
            out.append(chunk)
            total += len(chunk)
        if total >= MAX_CHARS:
            break
    return "\n\n".join(out)


def decode(documents, llm) -> Moat:
    """documents -> Moat. Always returns a Moat; ``error`` says so when it failed.

    Never raises: a paper run without a decode is still a valid market read, and the
    page hides the card rather than printing a template that pretends to have one.
    """
    if not documents:
        return Moat(error="nothing to read")
    try:
        raw = llm.complete(DECODE_PROMPT.format(docs=_docs_block(documents)))
    except Exception as exc:                       # noqa: BLE001 — reported, not raised
        return Moat(error=f"{type(exc).__name__}: {exc}")

    data = _parse_json(raw)
    if data is None:
        return Moat(error=f"the model answered but not as JSON (got: {str(raw)[:160]!r})")

    months = _months(data.get("replication_months"))
    tacit = _strings(data.get("tacit"))
    scale = str(data.get("scale_dependence") or "").strip()
    band, why = clock_for(months, tacit, scale)

    conf = str(data.get("confidence") or "").strip().lower()
    if conf not in ("high", "medium", "low"):
        conf = "low"

    return Moat(
        product=_one(data.get("product")),
        buyer=_one(data.get("buyer")),
        replaces=_one(data.get("replaces")),
        disclosed=_strings(data.get("disclosed")),
        tacit=tacit,
        replication_months=months,
        replication_basis=_one(data.get("replication_basis")),
        scale_dependence=scale,
        nearest_prior_art=_one(data.get("nearest_prior_art")),
        authors_position=_one(data.get("authors_position")),
        clock=band, clock_why=why,
        confidence=conf,
    )


# ── parsing ────────────────────────────────────────────────────────────

def _one(value) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in ("null", "none", "n/a") else text


def _strings(value, limit: int = 4) -> List[str]:
    if isinstance(value, str):
        value = [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    out, seen = [], set()
    for item in value:
        text = _one(item)
        key = text.lower()[:60]
        if text and key not in seen:
            seen.add(key)
            out.append(text)
    return out[:limit]


MONTHS_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _months(value) -> Optional[float]:
    """A plausible replication time, or None. Rejects nonsense rather than clamping it.

    Models answer this field as "6 months", "9m", "12+" as often as they answer 6.
    Pull the first number out and then judge it — reading "6 months" as unparseable
    would throw away the one field the whole clock depends on.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        num = float(value)
    else:
        found = MONTHS_RE.search(str(value))
        if not found:
            return None
        num = float(found.group(0))
    if num != num or num < 0 or num > 120:      # NaN, negative, absurd
        return None
    return num


def _parse_json(raw):
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    text = str(raw)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None
