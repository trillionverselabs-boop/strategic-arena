# LLM adapter — bridges the engine's simple `complete(prompt) -> str` interface
# to Hermes' real `ctx.llm` surface.
#
# Real ctx.llm (agent/plugin_llm.py PluginLlm):
#   complete(messages: list[dict], *, provider=None, model=None, temperature=None, ...)
#     -> PluginLlmCompleteResult(text=..., provider=..., model=..., usage=...)
#   complete_structured(*, instructions, input=[...], json_schema=None, json_mode=False, ...)
#     -> PluginLlmStructuredResult(parsed=..., text=..., content_type=...)
#
# The engine was written against `llm.complete(prompt) -> str`. This adapter keeps
# that contract while calling the real API correctly. It also normalizes the
# result to a plain string, which the engine's JSON parsing already handles.

from __future__ import annotations


class LlmAdapter:
    """Wraps ctx.llm and exposes complete(prompt: str) -> str."""

    def __init__(self, ctx_llm, temperature: float = 0.6):
        self._llm = ctx_llm
        self.temperature = temperature

    def complete(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        result = self._llm.complete(
            messages,
            temperature=self.temperature,
        )
        # PluginLlmCompleteResult has .text; tolerate a raw string just in case.
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
        # fall back to text parsing (engine's _parse_json handles it)
        return getattr(result, "text", "") or ""
