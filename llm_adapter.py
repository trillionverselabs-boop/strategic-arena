# LLM adapter — bridges the engine's simple `complete(prompt) -> str` interface
# to Hermes' real `ctx.llm` surface.
#
# Real ctx.llm (agent/plugin_llm.py PluginLlm):
#   complete(messages: list[dict], *, provider=None, model=None, temperature=None, ...)
#     -> PluginLlmCompleteResult(text=..., provider=..., model=..., usage=...)
#
# Choosing a model for host-owned calls is a consent-gated capability
# (`llm.model_override`). If the user has not granted it, the adapter silently
# runs on the active model — never fails, never asks again.

from __future__ import annotations

from . import prices

# The host's auxiliary default is 30 seconds. That is fine for a title or a
# one-line summary and hopeless for a review call on a free, rate-limited model
# — the first extraction times out, the recovery ladder finds no fallback and
# the run dies as "the model call failed". A review call is allowed to take
# minutes: there are only a few dozen of them per run.
DEFAULT_CALL_TIMEOUT_S = 180.0


# The provider fails transiently in ways that are not timeouts: a Cloudflare 502
# when its origin is overloaded, a 503 during a deploy, a 429 when a free tier is
# busy. All of them are retryable and all of them used to end the run on the spot.
_RETRY_STATUS = {429, 500, 502, 503, 504}


def _retry_delay(exc: Exception) -> float | None:
    """How long to wait before retrying, or None when this failure is not retryable.

    None is also the answer for a trust denial or a bad key: retrying those only
    doubles the wait before the same honest error.
    """
    import re

    text = str(exc)
    status = getattr(exc, "status_code", None)
    if status is None:
        m = re.search(r"(?:Error code|['\"]status['\"])\s*[:=]\s*(\d{3})", text)
        status = int(m.group(1)) if m else None
    timeoutish = "timeout" in type(exc).__name__.lower() or "timeout" in text.lower()
    if not timeoutish and status not in _RETRY_STATUS:
        return None
    # the provider usually tells us how long to wait; obey it, capped so a run is
    # never parked for minutes on one round
    ra = re.search(r"['\"]retry_after['\"]\s*:\s*(\d+)", text)
    if ra:
        return min(65.0, float(ra.group(1)))
    return 2.0 if timeoutish else 5.0


class LlmAdapter:
    """Wraps ctx.llm and exposes complete(prompt: str) -> str."""

    def __init__(self, ctx_llm, temperature: float = 0.6, model: str | None = None,
                 allow_override: bool = False, timeout: float | None = DEFAULT_CALL_TIMEOUT_S):
        self._llm = ctx_llm
        self.temperature = temperature
        self.model = model or "default"
        self.allow_override = allow_override
        self.timeout = timeout
        # what the host actually served, and why it may not be the model asked for
        self.served_provider = ""
        self.served_model = ""
        self.fallback_note = ""
        # real usage, summed from the host's report — the number the run prints
        self.usage = prices.blank_usage()
        # one retry by default; the paper setup path can raise it because those two
        # calls are the ones a transient 502 kills the whole run on
        self._max_attempts = 3

    def _kwargs(self) -> dict:
        kwargs = {"temperature": self.temperature}
        if self.allow_override and self.model not in (None, "", "default"):
            kwargs["model"] = self.model
        return kwargs

    def _once(self, messages, extra):
        """One host call, retried twice on a *transient* failure.

        A run that has already paid for twenty rounds must not die because the
        provider's edge returned a 502 for one call. Timeouts get a longer budget;
        5xx and 429 get a short backoff, honouring the provider's `retry_after`.
        A trust denial or a bad key is raised immediately — retrying those only
        delays the same honest error.
        """
        import time as _time

        attempts = 0
        while True:
            attempts += 1
            try:
                return self._llm.complete(messages, **extra)
            except Exception as exc:
                delay = _retry_delay(exc)
                if delay is None or attempts >= self._max_attempts:
                    raise
                _time.sleep(delay)
                nxt = dict(extra)
                if self.timeout:
                    nxt["timeout"] = self.timeout * 2
                extra = nxt

    def complete(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        extra = {} if self.timeout is None else {"timeout": self.timeout}
        if self.allow_override and self.model not in (None, "", "default"):
            try:
                result = self._once(messages, dict(model=self.model,
                                                   temperature=self.temperature, **extra))
            except Exception as exc:
                # Degrade rather than lose the run — but SAY SO. A silent
                # fallback is how "the picker works" came to be believed while
                # every run was quietly on the active model.
                self.fallback_note = (
                    f"{self.model} could not be reached ({type(exc).__name__}: {exc}); "
                    "this run used your active model instead."
                )
                result = self._once(messages, dict(temperature=self.temperature, **extra))
        else:
            result = self._once(messages, dict(temperature=self.temperature, **extra))
        prices.add_usage(self.usage, getattr(result, "usage", None))
        self.served_provider = getattr(result, "provider", "") or ""
        self.served_model = getattr(result, "model", "") or ""
        if isinstance(result, str):
            return result
        return getattr(result, "text", "") or ""

    def complete_json(self, prompt: str, schema: dict | None = None) -> dict:
        """Structured call — returns the parsed dict (no string parsing)."""
        result = self._llm.complete_structured(
            instructions=prompt,
            input=[{"type": "text", "text": prompt}],
            json_mode=True,
            json_schema=schema,
            schema_name="strategic_arena_output",
        )
        parsed = getattr(result, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        return getattr(result, "text", "") or ""
