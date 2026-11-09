#!/usr/bin/env python3
"""Probe the Nous inference API and pick a free model that can actually do the job.

Three things this script answers, in order — each one cost a run to learn:

  1. Which models are genuinely $0?   (pricing.prompt == pricing.completion == 0)
  2. Will it answer at all?           (trivial probe; catches capacity 429s)
  3. Can it hold our JSON contract?   (strict json_schema + span verification)

Usage:
    python tools/probe_free_models.py                # list zero-priced models
    python tools/probe_free_models.py --probe        # trivial probe on each
    python tools/probe_free_models.py --extract FILE # span-verified Brief on FILE

Reads the Nous credential from Hermes's auth store (never prints it).
Docs: docs/MODELS.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

AUTH = Path.home() / ".hermes" / "auth.json"
DEFAULT_BASE = "https://inference-api.nousresearch.com/v1"
REPORT_MODEL = "reflection/beam-1.0-501b-a23b:free"
CHEAP_MODEL = "upstage/solar-mini4:free"

# Reasoning is mandatory on the report model and bills against max_tokens, so the
# budget must cover thinking *and* the answer. 2,600 returned content:null.
MAX_TOKENS = 8000


def _creds() -> tuple[str, str]:
    try:
        nous = json.loads(AUTH.read_text())["providers"]["nous"]
    except Exception as exc:  # noqa: BLE001 - any failure means "no credential"
        sys.exit(f"No Nous credential at {AUTH} ({exc}). Run: hermes auth add nous")
    key = nous.get("agent_key") or nous.get("access_token")
    if not key:
        sys.exit("Nous credential present but carries no token.")
    return key, (nous.get("inference_base_url") or DEFAULT_BASE).rstrip("/")


def _post(path: str, body: dict, timeout: int = 300) -> dict:
    key, base = _creds()
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def _get(path: str, timeout: int = 60) -> dict:
    key, base = _creds()
    req = urllib.request.Request(base + path, headers={"Authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def _is_free(m: dict) -> bool:
    p = m.get("pricing") or {}
    prompt, completion = p.get("prompt"), p.get("completion")
    if prompt is None or completion is None:
        return False
    try:
        return float(prompt) == 0 and float(completion) == 0
    except (TypeError, ValueError):
        return False


def list_free() -> list[dict]:
    items = _get("/models").get("data", [])
    free = sorted((m for m in items if _is_free(m)), key=lambda m: -(m.get("context_length") or 0))
    print(f"{len(items)} models on the endpoint, {len(free)} zero-priced:\n")
    for m in free:
        caps = m.get("supported_parameters") or []
        print(
            f"  {m['id']:<45} ctx={m.get('context_length'):>8}  "
            f"structured={'yes' if 'structured_outputs' in caps else 'NO'}  "
            f"expires={m.get('expiration_date') or '-'}"
        )
    return free


def probe(model: str) -> bool:
    """One trivial call. Catches capacity 429s and endpoints that ignore input."""
    try:
        r = _post(
            "/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": "Reply with exactly this token and nothing else: ZEBRA-47"}],
                "max_tokens": 80,
                "temperature": 0,
            },
            timeout=120,
        )
        out = (r["choices"][0]["message"].get("content") or "").strip()
        ok = "ZEBRA-47" in out
        print(f"  {model:<45} {'OK' if ok else 'BAD OUTPUT'}  {out[:40]!r}")
        return ok
    except Exception as exc:  # noqa: BLE001 - report, never crash the sweep
        print(f"  {model:<45} ERROR {str(exc)[:90]}")
        return False


BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["move", "actor", "claims", "actors", "constraints"],
    "properties": {
        # Field meaning goes in `description`, not only the prompt: without it the
        # model echoed the instruction verb ("extract") into `move`.
        "move": {"type": "string", "description": "The decision or action the document announces, one sentence."},
        "actor": {"type": "string", "description": "The organisation or person making the move."},
        "claims": {
            "type": "array",
            "description": "Factual assertions the document makes that could later be checked.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "span"],
                "properties": {
                    "text": {"type": "string", "description": "The claim restated plainly."},
                    "span": {"type": "string", "description": "Verbatim quote from the document, 10-25 words."},
                },
            },
        },
        "actors": {
            "type": "array",
            "description": "Every named organisation or person in the document.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "role", "span"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string", "description": "What they do in this document."},
                    "span": {"type": "string", "description": "Verbatim quote naming them."},
                },
            },
        },
        "constraints": {
            "type": "array",
            "description": "Stated limits: licence, law, budget, policy, physics.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "span"],
                "properties": {
                    "text": {"type": "string"},
                    "span": {"type": "string", "description": "Verbatim quote stating the limit."},
                },
            },
        },
    },
}

PROMPT = (
    "You are reading a document on behalf of a strategist.\n"
    "Fill these fields:\n"
    "  move        — the decision or action the document announces, one sentence, in the document's own framing\n"
    "  actor       — the name of the organisation or person making the move (a name, not a page title)\n"
    "  claims      — factual assertions the document makes that could later be checked\n"
    "  actors      — every named organisation or person, with what they do here\n"
    "  constraints — limits the document states: licence, law, budget, policy\n"
    "HARD RULE: every 'span' is copied word for word from the document, 10-25 words. "
    "If a field cannot be quoted, omit that item. Never paraphrase inside a span.\n\nDOCUMENT:\n"
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _locate(doc_norm: str, span: str, anchor_words: int = 6) -> str | None:
    """Return the document's own wording for a quote, or None if it isn't there.

    Exact match first. Otherwise anchor on the opening words: models paraphrase a
    word or two mid-quote, and a repaired span must be the document's text, not
    the model's reconstruction of it.
    """
    s = _norm(span)
    if not s:
        return None
    i = doc_norm.find(s)
    if i >= 0:
        return doc_norm[i : i + len(s)]
    words = s.split()
    if len(words) <= anchor_words:
        return None
    anchor = " ".join(words[:anchor_words])
    j = doc_norm.find(anchor)
    if j < 0:
        return None
    window = doc_norm[j : j + len(s) + 40]
    tail = " ".join(words[-3:])
    return window if tail in window else None


def _spans(brief: dict) -> list[tuple[str, str]]:
    return (
        [("claim", c["span"]) for c in brief["claims"]]
        + [("actor", a["span"]) for a in brief["actors"]]
        + [("constraint", c["span"]) for c in brief["constraints"]]
    )


def verify(brief: dict, doc_norm: str) -> dict:
    """Rewrite every span to the document's own wording; drop what can't be found.

    Dropping beats failing the whole brief: an item with no quote is not evidence,
    and a brief that silently keeps it is the fiction this gate exists to stop.
    """
    repaired, dropped = 0, []
    for bucket, key in (("claims", "claims"), ("actors", "actors"), ("constraints", "constraints")):
        kept = []
        for item in brief.get(bucket, []):
            found = _locate(doc_norm, item.get("span", ""))
            if found is None:
                dropped.append({"bucket": bucket, "text": item.get("text") or item.get("name") or "", "span": item.get("span", "")})
                continue
            if found != _norm(item["span"]):
                repaired += 1
            item["span"] = found
            kept.append(item)
        brief[bucket] = kept
    brief["_verification"] = {"repaired": repaired, "dropped": dropped}
    return brief


def extract(text: str, model: str = REPORT_MODEL, attempts: int = 2) -> dict | None:
    """Extract a Brief, verifying every span. None if the model returns no answer.

    A single unverifiable response is not assumed to be the model's fault: one
    real call returned a flawless Brief about an unrelated film, 0/3 spans, then
    five retries were correct. Hence one retry, then give up loudly.
    """
    doc_norm = _norm(text)
    for n in range(1, attempts + 1):
        r = _post(
            "/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": PROMPT + text[:26000]}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "upfront_brief", "strict": True, "schema": BRIEF_SCHEMA},
                },
                "max_tokens": MAX_TOKENS,
                "temperature": 0,
                "reasoning_effort": "low",
            },
        )
        content = r["choices"][0]["message"].get("content")
        if not content:
            # A "successful" response can carry no answer when reasoning ate the budget.
            print(f"  attempt {n}: content is null (finish={r['choices'][0].get('finish_reason')}) — retrying")
            continue
        brief = verify(json.loads(content), doc_norm)
        v = brief["_verification"]
        total = len(_spans(brief)) + len(v["dropped"])
        usage = r.get("usage") or {}
        print(
            f"  attempt {n}: {total - len(v['dropped'])}/{total} spans verified "
            f"({v['repaired']} repaired) · {usage.get('total_tokens')} tok · "
            f"${(usage.get('cost_details') or {}).get('cost', 0)}"
        )
        for d in v["dropped"][:4]:
            print(f"    dropped {d['bucket']}: {d['span'][:90]}")
        if brief["move"] and brief["claims"]:
            return brief
    print("  no usable brief — the run must be reported degraded, never written up.")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="trivial probe on every zero-priced model")
    ap.add_argument("--extract", metavar="FILE", help="span-verified Brief from a text file")
    ap.add_argument("--model", default=REPORT_MODEL)
    args = ap.parse_args()

    if args.extract:
        text = Path(args.extract).read_text(encoding="utf-8")
        print(f"extracting from {args.extract} ({len(text)} chars) with {args.model}")
        brief = extract(text, args.model)
        if brief is None:
            return 1
        print(json.dumps(brief, indent=1, ensure_ascii=False))
        return 0

    free = list_free()
    if args.probe:
        print("\nprobe:")
        for m in free:
            probe(m["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
