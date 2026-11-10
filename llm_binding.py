"""Process-wide model binding for the Upfront plugin.

Why this file exists
--------------------
There are two importers of this plugin in a running Hermes process:

1. the **agent half** (`upfront/__init__.py`), loaded by the agent plugin loader
   under one module name, where `ctx.llm` exists;
2. the **dashboard namespace** (`upfront/dashboard/plugin_api.py`), which the
   dashboard loader imports *standalone from its file path* under a different
   module name, and where the FastAPI routes live.

Those are two different module objects, so a module-level `_LLM = ...` in either
one is invisible to the other — which is exactly how every review failed with
"LLM not bound in backend".

`sys.modules` is process-wide and shared by *every* import name, so a synthetic
holder module stored there under a fixed key is the one piece of state both
halves can see no matter how they were imported. Do not replace this with a
plain module global: it will silently break the moment the import names differ.
"""

from __future__ import annotations

import sys
import types

_HOLDER_KEY = "_upfront_llm_binding"   # not a real module name: pure shared state


def _holder() -> types.ModuleType:
    mod = sys.modules.get(_HOLDER_KEY)
    if mod is None:
        mod = types.ModuleType(_HOLDER_KEY)
        sys.modules[_HOLDER_KEY] = mod
    return mod


def set_llm(llm) -> None:
    """Bind the host-owned LLM (the only place it exists is the agent half)."""
    _holder().llm = llm


def get_llm():
    """The bound LLM, or None when the agent half has not loaded."""
    return getattr(_holder(), "llm", None)


def clear_llm() -> None:
    """Test helper — unbind."""
    if hasattr(_holder(), "llm"):
        delattr(_holder(), "llm")
