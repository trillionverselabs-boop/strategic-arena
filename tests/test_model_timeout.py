"""A review call needs a timeout the host's 30-second auxiliary default does not give.

The host defaults an aux call to 30s. A free, rate-limited model needs longer
than that for a single stakeholder extraction, and the failure it produced was
misleading ("No LLM provider configured ... provider=auto") because the host's
recovery ladder gave up after the timeout. The adapter must pass its own
generous timeout through every call.
"""

from upfront.llm_adapter import DEFAULT_CALL_TIMEOUT_S, LlmAdapter, _retry_delay


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


def test_a_timeout_is_retried_once_with_a_longer_budget():
    """A free model can outlast one call budget and answer on the next attempt.
    One retry at double the timeout beats losing a run that has already paid for
    twenty rounds."""
    class Flaky:
        def __init__(self):
            self.timeouts = []

        def complete(self, messages, **kwargs):
            self.timeouts.append(kwargs.get("timeout"))
            if len(self.timeouts) == 1:
                raise TimeoutError("read timed out")
            return type("R", (), {"text": "ok", "provider": "nous", "model": "m"})()

    llm = Flaky()
    adapter = LlmAdapter(llm, timeout=10)
    assert adapter.complete("hi") == "ok"
    assert llm.timeouts == [10, 20]


class ServerError(Exception):
    """Shaped like the provider's Cloudflare 502 payload, status in the text."""

    def __str__(self):
        return ("InternalServerError: Error code: 502 - {'title': 'Error 502: Bad gateway', "
                "'status': 502, 'retryable': True, 'retry_after': 60}")


def test_a_5xx_is_retryable_and_obeys_retry_after():
    """The field failure: one Cloudflare 502 killed a whole run before the room
    existed. A bad gateway is the provider's edge, not the user's input."""
    assert _retry_delay(ServerError()) == 60.0        # capped, and it says 60


def test_a_trust_denial_is_never_retried():
    assert _retry_delay(PermissionError("trust gate denied the model override")) is None


def test_a_502_is_retried_and_the_run_continues(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    class Flaky502:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, **kwargs):
            self.calls += 1
            if self.calls < 3:
                raise ServerError()
            return type("R", (), {"text": "ok", "provider": "nous", "model": "m"})()

    llm = Flaky502()
    adapter = LlmAdapter(llm, timeout=10)
    assert adapter.complete("hi") == "ok"
    assert llm.calls == 3


def test_retries_give_up_and_raise_the_real_error(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_: None)
    class Always:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, **kwargs):
            self.calls += 1
            raise ServerError()

    llm = Always()
    adapter = LlmAdapter(llm, timeout=10)
    try:
        adapter.complete("hi")
        assert False, "should have raised"
    except ServerError:
        pass
    assert llm.calls == adapter._max_attempts


def test_a_non_timeout_failure_is_not_retried():
    class Broken:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, **kwargs):
            self.calls += 1
            raise ValueError("trust gate denied")

    llm = Broken()
    adapter = LlmAdapter(llm, timeout=10)
    try:
        adapter.complete("hi")
    except ValueError:
        pass
    assert llm.calls == 1
