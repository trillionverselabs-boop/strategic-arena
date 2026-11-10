"""The model for the dashboard routes — through the host's own facade.

Why this exists
---------------
`ctx.llm` only exists inside the agent plugin's `register(ctx)`. In the desktop
deployment the routes can be served by a process that never ran `register()` (the
plugin host and the backend are not guaranteed to be one process), so the routes
need their own handle on the model.

The supported way to get one is `agent.plugin_llm.PluginLlm`, which is *exactly*
what `PluginContext.llm` builds (`hermes_cli/plugins.py` → `self._llm =
PluginLlm(plugin_id=self.plugin_id)`). It carries host-owned credentials, the
per-plugin trust gate, fallback and usage accounting. The plugin never holds a
token.

An earlier version read `~/.hermes/auth.json` and built an OpenAI client — which
breaks catalog admission rule 11 ("a plugin never reads … Hermes's `auth.json` …
or any other credential store directly"). Do not reintroduce it: if the host has
no route for something, ask for one instead of reading around it.
"""

from __future__ import annotations

PLUGIN_ID = "upfront"


class HostLlm:
    """`complete(messages, temperature=..., model=...)` -> object with `.text`.

    A thin shim over `PluginLlm` so the engine keeps its `llm.complete(prompt)`
    shape (see `llm_adapter.LlmAdapter`).
    """

    def __init__(self, plugin_llm, model: str = ""):
        self._llm = plugin_llm
        self.model = model
        self.calls = 0
        # Set when the host refuses a model override. The run then continues on
        # the user's active model, and the note is shown back to them — a picker
        # that silently does nothing is worse than one that says why.
        self.override_denied_note = ""

    class _Result:
        def __init__(self, text: str):
            self.text = text

    def complete(self, messages, temperature=None, model=None, timeout=None, **kwargs):
        self.calls += 1
        temp = 0.6 if temperature is None else temperature
        # timeout=None keeps the host's own default (30s) — the adapter always
        # passes its own, because 30s is far too short for a rate-limited model.
        extra = {} if timeout is None else {"timeout": timeout}
        try:
            res = self._llm.complete(messages, temperature=temp,
                                     model=(model or None), purpose="upfront.review",
                                     **extra)
        except TypeError:
            # a facade without `purpose` — same trust gate either way
            res = self._llm.complete(messages, temperature=temp, model=(model or None),
                                     **extra)
        except Exception as exc:
            if type(exc).__name__ == "PluginLlmTrustError" and model:
                # expected when the host has not opted this plugin into model
                # overrides: drop the override for the rest of the run instead of
                # paying a failed call every time, and say so once.
                self.override_denied_note = (
                    f"Your model choice ({model}) was not permitted by the host, so this "
                    "run used your active model. To enable the picker, set "
                    "plugins.entries.upfront.llm.allow_model_override: true in config.yaml."
                )
                try:
                    from . import paths
                    _dbg = paths.data_root() / "desktop-debug.log"
                    _dbg.parent.mkdir(parents=True, exist_ok=True)
                    with _dbg.open("a", encoding="utf-8") as fh:
                        fh.write(f"{__import__('time').strftime('%Y-%m-%d %H:%M:%S')} "
                                 f"pid={__import__('os').getpid()} model override denied; "
                                 f"falling back to the active model\n")
                except Exception:
                    pass
                res = self._llm.complete(messages, temperature=temp,
                                         purpose="upfront.review", **extra)
                text = getattr(res, "text", None)
                if text is None:
                    text = res if isinstance(res, str) else ""
                if not (text or "").strip():
                    raise RuntimeError("the model returned an empty answer")
                return self._Result(text)
            # surface the real reason: "the model call failed" hides a trust
            # error, an auth problem and a network problem behind one sentence
            try:
                from . import paths
                _dbg = paths.data_root() / "desktop-debug.log"
                _dbg.parent.mkdir(parents=True, exist_ok=True)
                with _dbg.open("a", encoding="utf-8") as fh:
                    fh.write(f"{__import__('time').strftime('%Y-%m-%d %H:%M:%S')} "
                             f"pid={__import__('os').getpid()} model call failed: "
                             f"{type(exc).__name__}: {exc}\n"
                             f"{__import__('traceback').format_exc()}\n")
            except Exception:
                pass
            raise
        text = getattr(res, "text", None)
        if text is None:
            text = res if isinstance(res, str) else ""
        if not (text or "").strip():
            raise RuntimeError("the model returned an empty answer")
        return self._Result(text)


def build_host_llm(model: str = "") -> HostLlm:
    """The host-owned model. Raises with a plain reason outside a Hermes process."""
    try:
        from agent.plugin_llm import PluginLlm  # the host's own facade
    except Exception as exc:  # pragma: no cover - only outside Hermes
        raise RuntimeError(
            "this Hermes build exposes no plugin LLM facade (agent.plugin_llm), "
            f"so the review cannot reach a model: {exc}"
        ) from exc
    return HostLlm(PluginLlm(plugin_id=PLUGIN_ID), model=model)


def available() -> bool:
    """True when the host facade can be constructed — used for a clear health read."""
    try:
        build_host_llm()
        return True
    except Exception:
        return False
