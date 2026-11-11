# Upfront — register(ctx) wiring.
# Unified package: agent tools here + desktop/plugin.js (the desktop loader
# scans this folder) + dashboard/plugin_api.py (FastAPI backend namespace).
#
# ctx.llm only exists inside register(ctx) (host-owned model+auth). We bind it
# into the dashboard backend module so /api/plugins/strategic-arena/* can run reviews.
# Choosing a model for those calls needs the consent-gated `llm.model_override`
# capability; we probe it and degrade to the active model when it is absent.

from __future__ import annotations

from pathlib import Path

from .llm_adapter import LlmAdapter
from .tools import register_tools

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def _register_skills(ctx) -> None:
    """Ship the preset packs as plugin skills (`upfront:<name>`), not copies in ~/.hermes/skills.

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
                ctx.log(f"upfront: skill {child.name} skipped: {exc}")
            except Exception:
                pass


def register(ctx) -> None:
    allow_override = False
    try:
        allow_override = bool(ctx.has_capability("llm.model_override"))
    except Exception:
        allow_override = False

    register_tools(ctx, allow_model_override=allow_override)
    _register_skills(ctx)

    # Bind the model where the dashboard routes can see it. The routes are a
    # *different module object* (the dashboard loader imports plugin_api.py
    # standalone from its path), so this goes through the process-wide holder in
    # llm_binding rather than a module global — see that file's docstring.
    try:
        from .llm_binding import set_llm

        set_llm(LlmAdapter(ctx.llm, allow_override=allow_override))
    except Exception as exc:
        try:
            ctx.log(f"upfront: could not bind the model for the dashboard: {exc}")
        except Exception:
            pass
