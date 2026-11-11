"""What a model costs — read, never chosen.

Why this file exists
--------------------
The form used to carry a model *picker*: a live catalogue plus a host permission
the desktop app does not grant. Both could fail, and when either did the form
said one thing while the run did another. The picker is gone; a run uses the
session's model.

But "which model" and "what will this cost me" are different questions, and the
second one deserves an answer before a user commits half an hour. So this module
answers only that: given a model id, what is its **published** price. It cannot
select a model, it holds no credentials, and every path fails soft — a network
error returns "no published price", never an invented one and never an exception
that could block a run.

The catalogue is the same public endpoint the Portal shows: no auth required,
per-token pricing, ~360 chat models. Cached for six hours under the plugin's data
dir, so a form that opens ten times fetches once.

The number after a run is better than any estimate, and does not come from here:
the host reports real token usage and its own cost estimate per call, which
`plugin_api` records next to the run. This module is only for the before.
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Dict, Optional

from .paths import data_root

CATALOGUE_URL = "https://inference-api.nousresearch.com/v1/models"
CACHE_TTL_S = 6 * 3600
TIMEOUT_S = 8          # a form must not wait on a slow catalogue
_UA = "hermes-strategic-arena/0.6 (+https://github.com/NousResearch/hermes-agent)"

# Embedding / rerank / speech endpoints cannot run a review, so they are not
# prices anyone needs here.
_SKIP = ("embed", "rerank", "whisper", "tts", "moderate", "guard", "ocr",
         "dall", "flux", "stable-diffusion")


def _per_million(value) -> float:
    """The API quotes USD per token; humans read USD per million tokens."""
    try:
        return round(float(value or 0) * 1_000_000, 6)
    except (TypeError, ValueError):
        return 0.0


def _is_chat(entry: dict) -> bool:
    arch = (entry or {}).get("architecture") or {}
    outs = [str(x).lower() for x in (arch.get("output_modalities") or [])]
    if outs:
        return "text" in outs
    name = str((entry or {}).get("id") or "").lower()
    return not any(tag in name for tag in _SKIP)


def _cache_path():
    return data_root() / "prices.json"


def _read_cache() -> dict:
    try:
        return json.loads(_cache_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cache(payload: dict) -> None:
    try:
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass          # a cache that cannot be written is not a run that fails


def parse_catalogue(payload: dict) -> Dict[str, dict]:
    """Raw /v1/models payload -> {model id: {prompt_per_m, completion_per_m, free}}."""
    out: Dict[str, dict] = {}
    for entry in (payload or {}).get("data") or []:
        mid = str(entry.get("id") or "").strip()
        if not mid or not _is_chat(entry):
            continue
        pricing = entry.get("pricing") or {}
        prompt = _per_million(pricing.get("prompt"))
        completion = _per_million(pricing.get("completion"))
        out[mid] = {
            "prompt_per_m": prompt,
            "completion_per_m": completion,
            "free": prompt == 0 and completion == 0,
        }
    return out


def _fetch() -> Dict[str, dict]:
    req = urllib.request.Request(CATALOGUE_URL, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        raw = resp.read(4_000_000)
    return parse_catalogue(json.loads(raw.decode("utf-8", errors="ignore")))


def catalogue(force: bool = False) -> Dict[str, dict]:
    """The price table, cached. Never raises; returns {} when nothing is known."""
    cached = _read_cache()
    fresh = bool(cached) and (time.time() - float(cached.get("fetched_at") or 0)) < CACHE_TTL_S
    if fresh and not force:
        return cached.get("models") or {}
    try:
        models = _fetch()
    except Exception:
        return cached.get("models") or {}      # stale beats nothing; nothing beats guessing
    if models:
        _write_cache({"fetched_at": time.time(), "models": models})
        return models
    return cached.get("models") or {}


def _candidates(model_id: str):
    """The ids a session's model slug might be listed under."""
    mid = (model_id or "").strip()
    if not mid:
        return []
    out = [mid]
    for suffix in (":free", ":latest", ":beta"):
        if mid.lower().endswith(suffix):
            out.append(mid[: -len(suffix)])
            break
    out.append(mid.replace(":", "/"))
    return [c for c in dict.fromkeys(out) if c]


def price_for(model_id: str) -> Optional[dict]:
    """Published price for one model, or None when the catalogue does not know it.

    None is a real answer: a model can be served by a provider whose prices the
    Nous catalogue does not carry. The form then shows tokens and says the price
    is unpublished, rather than multiplying by a number it made up.
    """
    models = catalogue()
    if not models:
        return None
    lowered = {k.lower(): v for k, v in models.items()}
    for cand in _candidates(model_id):
        hit = models.get(cand) or lowered.get(cand.lower())
        if hit:
            return {**hit, "id": cand}
    return None


def estimate_cost(model_id: str, tokens_in: int, tokens_out: int) -> Optional[float]:
    """USD for those tokens at the published price, or None when unpublished."""
    price = price_for(model_id)
    if not price:
        return None
    cost = (tokens_in / 1_000_000) * price["prompt_per_m"] \
        + (tokens_out / 1_000_000) * price["completion_per_m"]
    return round(cost, 4)


# ── what the run actually cost ────────────────────────────────────────
# The host reports real usage (and its own cost estimate) per call; the adapter
# sums it. This is the number the report prints, and it needs no catalogue.

def blank_usage() -> dict:
    return {"calls": 0, "tokens_in": 0, "tokens_out": 0,
            "tokens_total": 0, "cost_usd": 0.0, "cost_known": False}


def add_usage(total: dict, usage) -> dict:
    """Accumulate one call's usage into *total*, tolerating a missing/odd shape."""
    if not usage:
        return total
    get = (lambda name: getattr(usage, name, None)) if not isinstance(usage, dict) \
        else (lambda name: usage.get(name))
    total["calls"] += 1
    for key, name in (("tokens_in", "prompt_tokens"), ("tokens_out", "completion_tokens"),
                      ("tokens_total", "total_tokens")):
        try:
            total[key] += int(get(name) or 0)
        except (TypeError, ValueError):
            pass
    cost = get("cost_usd")
    if cost is not None:
        try:
            total["cost_usd"] = round(float(total["cost_usd"]) + float(cost), 6)
            total["cost_known"] = True
        except (TypeError, ValueError):
            pass
    return total
