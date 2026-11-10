"""I switched model and it still didn't take.

The permission was read once, when the plugin registered, and baked into the
adapter. Granting it afterwards changed `/model-access` but not the run — the
worst kind of bug, because the UI said "allowed" while every call quietly used
the active model.

The fix is one rule: resolve the permission per call, in one place, so the
picker and the run cannot disagree.
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "dashboard" / "plugin_api.py"


def _api():
    spec = importlib.util.spec_from_file_location("upfront_dashboard_model_gate", API)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RecordingLlm:
    """Host facade stand-in: records the model kwarg it was asked for."""

    def __init__(self):
        self.calls = []

    def complete(self, messages, **kwargs):
        self.calls.append(kwargs)
        return type("R", (), {"text": "ok", "provider": "p", "model": kwargs.get("model", "active")})()


class Base:
    """What `_llm()` returns: an adapter around the host facade."""

    def __init__(self, allow_override=False):
        self._llm = RecordingLlm()
        self.allow_override = allow_override


def _scenario(model):
    from upfront.models import Document, DocumentType, Scenario

    return Scenario(title="t", model=model,
                    documents=[Document(type=DocumentType.DECISION, content="Ship it")])


def test_the_permission_is_read_per_call_not_per_session(monkeypatch):
    api = _api()
    monkeypatch.setattr(api, "_override_allowed", lambda: True)
    base = Base(allow_override=False)          # registered when it was denied
    llm = api._run_llm(base, _scenario("nous/free-model"))
    assert llm.allow_override is True
    llm.complete("hi")
    assert base._llm.calls[-1]["model"] == "nous/free-model"


def test_a_denied_permission_never_asks_for_the_model(monkeypatch):
    api = _api()
    monkeypatch.setattr(api, "_override_allowed", lambda: False)
    base = Base(allow_override=False)
    llm = api._run_llm(base, _scenario("nous/free-model"))
    assert llm.allow_override is False
    llm.complete("hi")
    assert "model" not in base._llm.calls[-1]


def test_the_active_model_is_used_without_a_pick():
    api = _api()
    base = Base(allow_override=True)
    assert api._run_llm(base, _scenario("default")) is base


def test_both_readers_use_the_same_helper():
    """`/model-access` and the run must not answer from different sources."""
    src = API.read_text()
    assert src.count("_override_allowed()") >= 2
    assert "_override_allowed() or getattr(base" in src
    # the old per-session read must not come back
    assert 'allow_override=getattr(base, "allow_override", False),\n' not in src
