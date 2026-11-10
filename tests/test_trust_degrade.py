"""A refused model override must degrade, not fail the run.

The host gates model overrides behind `plugins.entries.<id>.llm.allow_model_override`,
which the consent screen's `granted_capabilities` does not always set. The plugin
must then run on the active model and say why — a picker that silently does
nothing is worse than one that explains itself.
"""

from upfront.host_llm import HostLlm


class TrustGateDenies:
    """Mirrors PluginLlm: raises on a model override, works without one."""

    def __init__(self):
        self.calls = []

    def complete(self, messages, **kw):
        self.calls.append(kw)

        class R:
            text = "ok without override"

        if kw.get("model"):
            raise type("PluginLlmTrustError", (PermissionError,), {})(
                "Plugin 'upfront' cannot override the model")
        return R()


def test_override_denial_falls_back_and_explains():
    inner = TrustGateDenies()
    llm = HostLlm(inner)

    result = llm.complete([{"role": "user", "content": "hi"}], temperature=0.2,
                          model="deepseek/some-model")

    assert result.text == "ok without override"
    assert inner.calls[-1].get("model") is None, "the fallback must drop the override"
    assert "not permitted" in llm.override_denied_note
    assert "allow_model_override" in llm.override_denied_note


def test_no_override_means_no_note():
    llm = HostLlm(TrustGateDenies())
    assert llm.complete([{"role": "user", "content": "hi"}]).text == "ok without override"
    assert llm.override_denied_note == ""
