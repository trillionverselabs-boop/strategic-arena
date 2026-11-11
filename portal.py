"""Live model catalogue from the Nous inference API.

`https://inference-api.nousresearch.com/v1/models` is public: it needs no
credentials, returns every model with per-token pricing, and is the same list
the Portal shows. That is why we can present real prices instead of a
hardcoded table nobody can verify — and why the plugin never touches a secret
to do it.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import List

from .paths import data_root

CATALOGUE_URL = "https://inference-api.nousresearch.com/v1/models"
CACHE_TTL_S = 6 * 3600
TIMEOUT_S = 20
_UA = "hermes-strategic-arena/0.6"


def _per_million(value) -> float:
    """The API quotes USD per token; humans read USD per million tokens."""
    try:
        return round(float(value or 0) * 1_000_000, 4)
    except (TypeError, ValueError):
        return 0.0


# The catalogue also lists embedding / rerank / speech endpoints. They cannot
# run a stakeholder review, so keep them out of the picker.
_NON_CHAT = re.compile(r"embed|rerank|whisper|tts|moderat|guard|ocr|image|video|dall|flux", re.I)


def is_chat(model: dict) -> bool:
    """True when the model can answer with text (the only thing a review needs).

    The catalogue states this precisely in architecture.output_modalities
    ("text->embeddings" is an embedding model, not a chat model).
    """
    arch = (model or {}).get("architecture") or {}
    outs = [str(x).lower() for x in (arch.get("output_modalities") or [])]
    if outs:
        return "text" in outs
    return not _NON_CHAT.search(str((model or {}).get("id") or ""))


def normalize(payload: dict) -> List[dict]:
    """Raw API payload -> the compact list the desktop form renders."""
    out: List[dict] = []
    for m in (payload or {}).get("data", []) or []:
        pricing = m.get("pricing") or {}
        prompt = _per_million(pricing.get("prompt"))
        completion = _per_million(pricing.get("completion"))
        if not is_chat(m):
            continue
        mid = str(m.get("id") or "")
        out.append({
            "id": mid,
            "name": str(m.get("name") or mid),
            "context": int(m.get("context_length") or 0),
            "prompt_per_m": prompt,
            "completion_per_m": completion,
            "free": prompt == 0 and completion == 0,
            "reasoning": bool(m.get("reasoning")),
            "limits": m.get("per_request_limits") or {},
        })
    out.sort(key=lambda r: (not r["free"], r["prompt_per_m"], r["name"]))
    return out


def estimate_cost(model: dict, calls: int, in_tokens: int = 700,
                  out_tokens: int = 120) -> float:
    """Rough USD for a run: calls x (in x prompt price + out x completion price)."""
    prompt = float(model.get("prompt_per_m") or 0)
    completion = float(model.get("completion_per_m") or 0)
    per_call = (in_tokens / 1_000_000.0) * prompt + (out_tokens / 1_000_000.0) * completion
    return round(per_call * max(0, calls), 4)


def _cache_path():
    return data_root() / "models-cache.json"


def catalogue(force: bool = False) -> dict:
    """Cached live catalogue: {models, fetched_at, source, error?}."""
    path = _cache_path()
    cached = None
    if path.exists() and not force:
        try:
            cached = json.loads(path.read_text())
            if time.time() - float(cached.get("fetched_ts", 0)) < CACHE_TTL_S:
                return cached
        except Exception:
            cached = None

    try:
        req = urllib.request.Request(CATALOGUE_URL, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode("utf-8", "ignore"))
        models = normalize(payload)
        out = {
            "models": models,
            "count": len(models),
            "total_listed": len((payload or {}).get("data", []) or []),
            "free_count": sum(1 for m in models if m["free"]),
            "fetched_ts": time.time(),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": CATALOGUE_URL,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out))
        return out
    except Exception as exc:
        if cached:
            cached["error"] = f"live fetch failed ({exc}); showing cached list"
            return cached
        return {"models": [], "count": 0, "free_count": 0, "fetched_ts": 0,
                "fetched_at": "", "source": CATALOGUE_URL,
                "error": f"could not reach the model catalogue: {exc}"}
