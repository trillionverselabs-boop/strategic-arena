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

# The host's auxiliary default is 30 seconds. That is fine for a title or a
# one-line summary and hopeless for a review call on a free, rate-limited model
# — the first extraction times out, the recovery ladder finds no fallback and
# the run dies as "the model call failed". A review call is allowed to take
# minutes: there are only a few dozen of them per run.
DEFAULT_CALL_TIMEOUT_S = 180.0


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

    def _kwargs(self) -> dict:
        kwargs = {"temperature": self.temperature}
        if self.allow_override and self.model not in (None, "", "default"):
            kwargs["model"] = self.model
        return kwargs

    def complete(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        extra = {} if self.timeout is None else {"timeout": self.timeout}
        if self.allow_override and self.model not in (None, "", "default"):
            try:
                result = self._llm.complete(messages, model=self.model,
                                            temperature=self.temperature, **extra)
            except Exception as exc:
                # Degrade rather than lose the run — but SAY SO. A silent
                # fallback is how "the picker works" came to be believed while
                # every run was quietly on the active model.
                self.fallback_note = (
                    f"{self.model} could not be reached ({type(exc).__name__}: {exc}); "
                    "this run used your active model instead."
                )
                result = self._llm.complete(messages, temperature=self.temperature, **extra)
        else:
            result = self._llm.complete(messages, temperature=self.temperature, **extra)
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
            schema_name="upfront_output",
        )
        parsed = getattr(result, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        return getattr(result, "text", "") or ""
