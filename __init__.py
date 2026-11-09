# Upfront Prediction plugin — register(ctx) wiring.
# Unified package: agent tools here + desktop/plugin.js (the desktop loader
# scans this folder) + dashboard/plugin_api.py (FastAPI backend namespace).
#
# ctx.llm only exists inside register(ctx) (host-owned model+auth). We bind it
# into the dashboard backend module so /api/plugins/upfront/* can run sims.

from __future__ import annotations

from .llm_adapter import LlmAdapter
from .tools import register_tools


def register(ctx) -> None:
    register_tools(ctx)

    # Bind ctx.llm into the dashboard backend (best effort — the backend is
    # loaded by a separate loader, so import defensively and never crash).
    try:
        from .dashboard import plugin_api  # type: ignore
        plugin_api.set_llm(LlmAdapter(ctx.llm))
    except Exception:
        # dashboard/ may not be importable as a package; the backend's
        # set_llm is bound by the dashboard loader path instead. Non-fatal.
        pass
