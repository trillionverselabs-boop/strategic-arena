"""Where this plugin is allowed to write.

Hermes gives every plugin a durable, profile-scoped data root
(`plugins.plugin_storage.plugin_data_dir`) that survives `plugins update` and
(`plugins remove`). Use it. Fall back to $HERMES_HOME/strategic-arena outside Hermes.
"""

from __future__ import annotations

import os
from pathlib import Path


def _hermes_home() -> Path:
    """The active profile's Hermes home.

    `hermes_constants.get_hermes_home()` follows the active profile (context
    override -> `$HERMES_HOME` -> platform default); the env var alone is a
    legacy read that misses the override. Fall back to the env var, then
    `~/.hermes`, when the host module is not importable (standalone runs, tests).
    """
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home())
    except Exception:
        return Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))


def data_root() -> Path:
    """`<hermes home>/plugin-data/strategic-arena`, or `<hermes home>/strategic-arena` as a fallback."""
    home = _hermes_home()
    try:
        from plugins.plugin_storage import plugin_data_dir  # type: ignore

        p = Path(plugin_data_dir("strategic-arena"))
        if str(p).startswith(str(home)):      # never escape the active home
            return p
    except Exception:
        pass
    return home / "strategic-arena"


def runs_dir() -> Path:
    return data_root() / "runs"


def graph_path() -> Path:
    return data_root() / "graph.json"
