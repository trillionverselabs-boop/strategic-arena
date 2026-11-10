"""The plugin must stay a tooling-only project, or a non-interactive install aborts.

Hermes' installer counts any of these in ``pyproject.toml`` as "installs packages":
a non-empty ``[project].dependencies``, a ``[build-system]`` table, optional-dependencies,
dependency-groups (pm/plugin_declarations.py, ``installs = ("build-system" in document ...)``).
When it counts one, install asks a dependency-consent question — and the desktop app's
Install from Git / reinstall dialog runs WITH NO TTY, so it refuses and the whole install dies:

    Plugin 'upfront' was not published: Reinstall declined:
    dependency install skipped (non-interactive).

This plugin needs no packages of its own (pydantic and fastapi are Hermes core requirements),
so it must declare none. These tests fail the moment that changes, before it reaches a user.
"""

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PYPROJECT = REPO / "pyproject.toml"


def _doc() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_no_build_system_table():
    """A [build-system] table alone is enough to trigger the consent gate."""
    assert "build-system" not in _doc()


def test_no_declared_dependencies():
    assert _doc()["project"]["dependencies"] == []


def test_no_extras_or_dependency_groups():
    doc = _doc()
    assert not any(doc.get("project", {}).get("optional-dependencies", {}).values())
    assert not any(doc.get("dependency-groups", {}).values())
    assert doc.get("tool", {}).get("uv", {}).get("package") is not True


def test_nothing_else_in_the_project_declares_python_dependencies():
    """``python_dependencies`` in plugin.yaml would hit the same gate."""
    import yaml

    manifest = yaml.safe_load((REPO / "plugin.yaml").read_text(encoding="utf-8"))
    assert not manifest.get("python_dependencies")
    assert not (REPO / "requirements.txt").exists()
