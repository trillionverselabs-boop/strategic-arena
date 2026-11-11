"""The model is the session's, and nothing else.

The picker offered a choice that needed a live catalogue fetched over the network
*and* a host permission (`plugins.entries.<id>.llm.allow_model_override`) the app
does not grant — so a run could be started on a model the host then refused, and
the form could only ever be wrong about something Hermes had already decided.

The picker is gone. A run uses the adapter this process already bound. This file
used to test the gate's per-call resolution; it now pins the gate's absence, so
the picker cannot come back in through the side door.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "dashboard" / "plugin_api.py"


def _api():
    spec = importlib.util.spec_from_file_location("upfront_dashboard_model_gate", API)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_model_picker_routes():
    src = API.read_text()
    assert "/models" not in src
    assert "/model-access" not in src


def test_no_override_plumbing_survives():
    src = API.read_text()
    assert "_run_llm" not in src
    assert "_override_allowed" not in src
    assert "allow_override=True" not in src


def test_a_run_uses_the_adapter_the_process_already_bound(monkeypatch):
    """The route must not build a second adapter around a model it picked."""
    api = _api()
    sentinel = object()
    monkeypatch.setattr(api, "_llm", lambda: sentinel)
    assert api._llm() is sentinel
