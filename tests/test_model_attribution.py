"""A run must say which model actually served it — the requested model is not proof.

The host does not raise when it cannot serve the picked model: it routes the call to
whatever is active and reports that model back. Two behaviours depend on knowing
the difference: the report's honesty, and not crying wolf when the catalogue's
"latest" alias (``~deepseek/...``) resolves to a concrete build.
"""

from upfront import engine
from upfront.llm_adapter import LlmAdapter


# ── the alias rule ────────────────────────────────────────────────────

def test_latest_alias_resolving_to_a_concrete_build_is_not_a_substitution():
    assert engine._same_model_family(
        "~deepseek/deepseek-flash-latest", "deepseek/deepseek-v4.1-flash-1017"
    )


def test_exact_match_is_not_a_substitution():
    assert engine._same_model_family(
        "meta-llama/llama-3.1-8b-instruct", "meta-llama/llama-3.1-8b-instruct"
    )


def test_another_vendor_is_a_substitution():
    assert not engine._same_model_family(
        "nonexistent/model-xyz", "meituan/longcat-2.5:free"
    )


def test_a_free_suffix_is_not_a_substitution():
    assert engine._same_model_family(
        "meituan/longcat-2.5", "meituan/longcat-2.5:free"
    )


# ── the adapter surfaces the truth ────────────────────────────────────

class RecordingLLM:
    """Returns a host-shaped result carrying the real destination."""

    def __init__(self, text="ok", provider="nous", model="deepseek/deepseek-v4.1-flash-1017"):
        self.provider = provider
        self.model = model
        self.text = text
        self.calls = 0

    def complete(self, messages, **kwargs):
        self.calls += 1
        return self

    def __getattr__(self, name):  # pragma: no cover - only .text is read
        if name == "text":
            return self.text
        raise AttributeError(name)


def test_adapter_records_the_served_model():
    llm = RecordingLLM()
    adapter = LlmAdapter(llm, model="deepseek/deepseek-v4.1-flash-1017", allow_override=True)
    adapter.complete("hello")
    assert adapter.served_model == "deepseek/deepseek-v4.1-flash-1017"
    assert adapter.served_provider == "nous"
    assert adapter.fallback_note == ""


def test_adapter_says_so_when_it_falls_back():
    class Refuses:
        def complete(self, messages, **kwargs):
            if kwargs.get("model"):
                raise RuntimeError("model not permitted")
            return RecordingLLM(model="meituan/longcat-2.5:free")

    adapter = LlmAdapter(Refuses(), model="nonexistent/model-xyz", allow_override=True)
    adapter.complete("hello")
    assert "nonexistent/model-xyz" in adapter.fallback_note
    assert adapter.served_model == "meituan/longcat-2.5:free"
