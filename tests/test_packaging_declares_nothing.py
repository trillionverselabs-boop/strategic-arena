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

import ast
import re
import sys
import tomllib
from pathlib import Path

import pytest

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


# ── the other half: nothing MAY be undeclared either ──────────────────
# "declares nothing" is only defensible if what the code actually imports is
# already in Hermes's own environment. So the set of third-party modules the
# shipped code imports is pinned, and each one is checked against Hermes's own
# dependency list when a Hermes checkout is available. A reviewer's question
# (rule 10) gets an answer the repo can prove, not a paragraph in a PR.

# What the shipped runtime is allowed to import from outside the stdlib. Both are
# Hermes core requirements, pinned by Hermes itself (pydantic==2.14.1,
# fastapi>=0.104,<1), which is precisely why the plugin must not restate them:
# a plugin's pins cannot move Hermes's, and a non-empty list breaks the install.
ALLOWED_THIRD_PARTY = {"pydantic", "fastapi"}

# Hermes's own documented surfaces, per the plugin developer guide: `ctx.llm`
# is `agent.plugin_llm.PluginLlm`, `plugin_data_dir` is
# `plugins.plugin_storage`, and `get_default_hermes_root` is
# `hermes_constants`. Importing these is the supported path, not a private reach.
ALLOWED_HERMES_CORE = {"agent", "plugins", "hermes_constants"}


def _shipped_sources():
    for path in sorted(REPO.rglob("*.py")):
        rel = path.relative_to(REPO)
        if rel.parts[0] in ("tests", "scripts", "docs") or "__pycache__" in rel.parts:
            continue
        yield rel, path


def _imported_roots(source: str):
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_only_third_party_imports_are_hermes_core_requirements():
    stdlib = set(sys.stdlib_module_names)
    seen = set()
    for rel, path in _shipped_sources():
        for root in _imported_roots(path.read_text(encoding="utf-8")):
            if root in stdlib or root in {"__future__"}:
                continue
            # the plugin's own package modules, imported relatively or by name
            if root in {"upfront", "dashboard"}:
                continue
            if (REPO / f"{root}.py").exists() or (REPO / root).is_dir():
                continue
            seen.add(root)
    assert seen == ALLOWED_THIRD_PARTY | ALLOWED_HERMES_CORE, (
        f"shipped code imports {sorted(seen)}; the manifest declares nothing, so "
        f"every third-party module must be a Hermes core requirement. If this is a "
        f"new one, it has to be declared — with a floor AND an upper bound — and the "
        f"install-consent tradeoff re-examined (see this file's docstring)."
    )


def test_those_modules_are_in_hermes_own_dependency_list():
    """Proves the claim instead of asserting it: read Hermes's pyproject, if we
    can find one. Skipped (not failed) on a machine with no Hermes checkout —
    catalog CI runs `hermes plugins validate`, which does its own check."""
    candidates = [
        Path.home() / ".hermes" / "hermes-agent" / "pyproject.toml",
        Path("/usr/local/lib/hermes-agent/pyproject.toml"),
    ]
    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        pytest.skip("no Hermes checkout on this machine to compare against")
    text = found.read_text(encoding="utf-8")
    declared = set(re.findall(r'^\s*"([a-zA-Z0-9_.-]+)', text, re.M))
    missing = ALLOWED_THIRD_PARTY - declared
    assert not missing, f"Hermes does not appear to require {sorted(missing)}"
