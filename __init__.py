# Upfront — register(ctx) wiring.
# Unified package: agent tools here + desktop/plugin.js (the desktop loader
# scans this folder) + dashboard/plugin_api.py (FastAPI backend namespace).
#
# ctx.llm only exists inside register(ctx) (host-owned model+auth). We bind it
# into the dashboard backend module so /api/plugins/strategic-arena/* can run reviews.
# Choosing a model for those calls needs the consent-gated `llm.model_override`
# capability; we probe it and degrade to the active model when it is absent.

from __future__ import annotations

import sys as _sys
from pathlib import Path
from pathlib import Path as _Path

# Hermes loads this file as the plugin package (`__init__.py` at the plugin root).
# pytest's root collector instead imports it as a *top-level module* named
# `__init__` — which a repository gets when its root is a package — and the
# relative imports below then fail with "attempted relative import with no known
# parent package". Registering the plugin directory under a real package name
# keeps both loaders working; nothing in the plugin depends on the name it was
# loaded under, so this is a loader accommodation, not a dependency.
if __package__ in (None, ""):
    __package__ = "strategic_arena"
    _self = _sys.modules.setdefault(__package__, _sys.modules[__name__])
    _self.__path__ = [str(_Path(__file__).resolve().parent)]

from .llm_adapter import LlmAdapter
from .tools import register_tools

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def _register_skills(ctx) -> None:
    """Ship the preset packs as plugin skills (`strategic-arena:<name>`), not copies in ~/.hermes/skills.

    Skills are a normal surface — no extra capability, no manifest change. A skill that
    fails to register is logged and skipped: it must never take the plugin down.
    """
    if not SKILLS_DIR.is_dir():
        return
    for child in sorted(SKILLS_DIR.iterdir()):
        md = child / "SKILL.md"
        if not (child.is_dir() and md.exists()):
            continue
        try:
            ctx.register_skill(child.name, md)
        except Exception as exc:  # older host, bad frontmatter — the rest still load
            try:
                ctx.log(f"strategic-arena: skill {child.name} skipped: {exc}")
            except Exception:
                pass


def register(ctx) -> None:
    register_tools(ctx)
    _register_skills(ctx)

    # Bind the model where the dashboard routes can see it. The routes are a
    # *different module object* (the dashboard loader imports plugin_api.py
    # standalone from its path), so this goes through the process-wide holder in
    # llm_binding rather than a module global — see that file's docstring.
    try:
        from .llm_binding import set_llm

        set_llm(LlmAdapter(ctx.llm))
    except Exception as exc:
        try:
            ctx.log(f"strategic-arena: could not bind the model for the dashboard: {exc}")
        except Exception:
            pass
