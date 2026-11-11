"""Catalog admission guards.

Rule 11: a plugin never reads .env, Hermes's auth.json, another tool's login, or
any other credential store directly — secrets come through Hermes. These tests
keep the plugin on the right side of that line, because a human reviewer reads
the pinned tree and a violation is a decline, not a warning.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# Plugin runtime + packaged surfaces. Tests and docs are excluded: they are not
# shipped, and docs must be able to describe the rule.
SCAN_DIRS = ["dashboard", "tools"]
SCAN_FILES = ["__init__.py", "host_llm.py", "llm_adapter.py", "engine.py",
              "moat.py", "reporting.py"]


def _sources():
    out = []
    for d in SCAN_DIRS:
        for p in (REPO / d).rglob("*.py"):
            out.append(p)
    out += [REPO / f for f in SCAN_FILES]
    return out


def _code_only(path):
    """The file's string literals, minus docstrings.

    A docstring may describe the rule ("we must not read auth.json"); a real read
    is a string used in code. Only the latter may fail the test.
    """
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]
    return "\n".join(literals)


@pytest.mark.parametrize("path", _sources(), ids=lambda p: str(p.relative_to(REPO)))
def test_no_credential_store_reads(path):
    text = _code_only(path).lower()
    assert "auth.json" not in text, f"{path.name} reads Hermes's auth.json"
    assert ".env" not in text, f"{path.name} reads a .env file"
    assert "agent_key" not in text, f"{path.name} touches an OAuth agent key"
    assert "access_token" not in text, f"{path.name} touches an OAuth token"
    assert "bearer " not in text, f"{path.name} builds an Authorization header itself"


def test_the_model_comes_from_the_host_facade():
    src = (REPO / "host_llm.py").read_text(encoding="utf-8")
    assert "from agent.plugin_llm import PluginLlm" in src
    assert "PluginLlm(plugin_id=" in src


def test_no_subprocess_or_eval_in_runtime_code():
    for p in _sources():
        text = p.read_text(encoding="utf-8")
        assert "subprocess" not in text, f"{p.name} shells out"
        assert "os.system" not in text, f"{p.name} shells out"
        assert "eval(" not in text, f"{p.name} uses eval"
