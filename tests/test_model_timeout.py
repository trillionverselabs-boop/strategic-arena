"""A review call needs a timeout the host's 30-second auxiliary default does not give.

The host defaults an aux call to 30s. A free, rate-limited model needs longer
than that for a single stakeholder extraction, and the failure it produced was
misleading ("No LLM provider configured ... provider=auto") because the host's
recovery ladder gave up after the timeout. The adapter must pass its own
generous timeout through every call.
"""

from upfront.llm_adapter import DEFAULT_CALL_TIMEOUT_S, LlmAdapter


class RecordingLLM:
    def __init__(self, text="ok"):
        self.calls = []
        self.text = text

    def complete(self, messages, **kwargs):
        self.calls.append(kwargs)
        return self.text


def test_default_timeout_is_far_beyond_the_host_default():
    assert DEFAULT_CALL_TIMEOUT_S >= 120


def test_complete_passes_the_timeout():
    llm = RecordingLLM()
    adapter = LlmAdapter(llm, temperature=0.4, model="some/model", allow_override=True)
    assert adapter.complete("hello") == "ok"
    assert llm.calls, "the model was never called"
    for call in llm.calls:
        assert call.get("timeout") == DEFAULT_CALL_TIMEOUT_S


def test_retry_after_a_refused_override_still_carries_the_timeout():
    class RefusesFirst:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise PermissionError("cannot override the model")
            return "ok"

    llm = RefusesFirst()
    adapter = LlmAdapter(llm, temperature=0.4, model="some/model", allow_override=True)
    assert adapter.complete("hello") == "ok"
    assert llm.calls == 2


def test_timeout_can_be_turned_off():
    llm = RecordingLLM()
    adapter = LlmAdapter(llm, temperature=0.4, timeout=None)
    adapter.complete("hello")
    assert "timeout" not in llm.calls[0]
