# Upfront — register(ctx) wiring.
# Unified package: agent tools here + desktop/plugin.js (the desktop loader
# scans this folder) + dashboard/plugin_api.py (FastAPI backend namespace).
#
# ctx.llm only exists inside register(ctx) (host-owned model+auth). We bind it
# into the dashboard backend module so /api/plugins/upfront/* can run reviews.
# Choosing a model for those calls needs the consent-gated `llm.model_override`
# capability; we probe it and degrade to the active model when it is absent.

from __future__ import annotations

from .llm_adapter import LlmAdapter
from .tools import register_tools


def register(ctx) -> None:
    allow_override = False
    try:
        allow_override = bool(ctx.has_capability("llm.model_override"))
    except Exception:
        allow_override = False

    register_tools(ctx, allow_model_override=allow_override)

    try:
        from .dashboard import plugin_api  # type: ignore

        plugin_api.set_llm(LlmAdapter(ctx.llm, allow_override=allow_override))
    except Exception:
        # dashboard/ may not be importable as a package; the backend's
        # set_llm is bound by the dashboard loader path instead. Non-fatal.
        pass
