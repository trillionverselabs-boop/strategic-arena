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


class LlmAdapter:
    """Wraps ctx.llm and exposes complete(prompt: str) -> str."""

    def __init__(self, ctx_llm, temperature: float = 0.6, model: str | None = None,
                 allow_override: bool = False):
        self._llm = ctx_llm
        self.temperature = temperature
        self.model = model or "default"
        self.allow_override = allow_override

    def _kwargs(self) -> dict:
        kwargs = {"temperature": self.temperature}
        if self.allow_override and self.model not in (None, "", "default"):
            kwargs["model"] = self.model
        return kwargs

    def complete(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        if self.allow_override and self.model not in (None, "", "default"):
            try:
                result = self._llm.complete(messages, model=self.model,
                                            temperature=self.temperature)
            except Exception:
                result = self._llm.complete(messages, temperature=self.temperature)
        else:
            result = self._llm.complete(messages, temperature=self.temperature)
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
