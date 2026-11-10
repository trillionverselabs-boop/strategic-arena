"""The model must be visible to the dashboard routes, not just the agent half.

In a running Hermes process the plugin is imported twice under different names:
the agent half by the plugin loader, and `dashboard/plugin_api.py` standalone
from its file path by the dashboard loader. Module globals are *not* shared
between those two objects, so binding one left the routes raising
"LLM not bound in backend" — the exact failure seen in the desktop app.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from upfront import llm_binding

class HostLlmStub:
    """Minimal stand-in for host_llm.HostLlm (same call shape)."""

    def complete(self, messages, temperature=None, model=None, **kwargs):
        return "stub"


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
API_FILE = PLUGIN_ROOT / "dashboard" / "plugin_api.py"


def _load_api_standalone(name: str):
    """Import plugin_api.py the way the dashboard loader does: by file path, alone."""
    spec = importlib.util.spec_from_file_location(name, API_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _unbind():
    llm_binding.clear_llm()
    yield
    llm_binding.clear_llm()


def test_binding_is_visible_to_a_standalone_import():
    sentinel = object()
    llm_binding.set_llm(sentinel)          # what register(ctx) now does

    api = _load_api_standalone("upfront_api_standalone_probe")
    assert api._llm() is sentinel


def test_health_reports_the_binding():
    api = _load_api_standalone("upfront_api_health_probe")
    llm_binding.set_llm(object())
    assert api.llm_binding.get_llm() is not None


def test_compat_set_llm_still_binds_the_same_holder():
    api = _load_api_standalone("upfront_api_compat_probe")
    sentinel = object()
    api.set_llm(sentinel)
    assert llm_binding.get_llm() is sentinel
    assert api._llm() is sentinel


def test_unbound_falls_back_to_the_local_provider(monkeypatch):
    """No agent binding in this process must not mean 'no run' — use local config."""
    from upfront import host_llm

    class Fake(HostLlmStub):
        pass

    monkeypatch.setattr(host_llm, "build_host_llm", lambda *a, **k: Fake())
    api = _load_api_standalone("upfront_api_fallback_probe")
    llm_binding.clear_llm()
    bound, source = api._resolve_llm()
    assert source == "host-config"
    assert bound.complete("hi") == "stub"


def test_no_model_at_all_raises_a_plain_message(monkeypatch):
    from upfront import host_llm

    def boom(*a, **k):
        raise RuntimeError("no model credentials found")

    monkeypatch.setattr(host_llm, "build_host_llm", boom)
    api = _load_api_standalone("upfront_api_nomodel_probe")
    llm_binding.clear_llm()
    with pytest.raises(RuntimeError) as err:
        api._llm()
    assert "No model available" in str(err.value)


def test_register_binds_the_host_model_for_the_routes():
    """The whole chain: register(ctx) -> routes can call the model."""
    from unittest.mock import MagicMock

    import upfront as plugin_pkg
    from upfront.llm_adapter import LlmAdapter

    ctx = MagicMock()
    ctx.has_capability.return_value = False
    ctx.llm = MagicMock()

    plugin_pkg.register(ctx)

    api = _load_api_standalone("upfront_api_register_probe")
    bound = api._llm()
    assert isinstance(bound, LlmAdapter)
    assert bound._llm is ctx.llm
