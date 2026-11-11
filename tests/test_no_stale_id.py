"""The pre-rename id must not be able to answer for this plugin.

The plugin was renamed `upfront` → `strategic-arena`. While the backend
registered its modules under the fixed name `upfront`, a leftover copy on disk —
or a stale `upfront.models` already in `sys.modules` from an earlier load in the
same process — could satisfy `from upfront.models import ArtifactKind` and hand
back the OLD class table. The run then died with
"cannot import name 'ArtifactKind' from 'upfront.models'", which is exactly what
the user saw: a new page talking to an old engine.

The fix is that nothing in the shipped plugin imports or registers that name.
These tests pin it behaviourally, not by grepping for a word.
"""

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
API_FILE = ROOT / "dashboard" / "plugin_api.py"


def _load_api_standalone(name="hermes_dashboard_plugin_stale_probe"):
    """Import plugin_api.py the way the dashboard loader does: by file path, alone."""
    spec = importlib.util.spec_from_file_location(name, API_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def stale_upfront(tmp_path, monkeypatch):
    """A leftover pre-rename install: on sys.path, already imported, old models.

    This is the field condition — a copy of the plugin from before the rename,
    still importable as `upfront`, with a `models.py` that predates ArtifactKind.
    """
    # Other test modules import the real plugin through the conftest shim, which
    # also answers to `upfront`. Evict it so this fixture really loads the stale
    # copy, exactly as a leftover install on disk would be loaded.
    for name in [n for n in sys.modules if n == "upfront" or n.startswith("upfront.")]:
        monkeypatch.delitem(sys.modules, name, raising=False)

    pkg = tmp_path / "upfront"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "models.py").write_text("# pre-rename copy: no ArtifactKind here\n")
    monkeypatch.syspath_prepend(str(tmp_path))

    import upfront  # noqa: F401  (the stale copy)
    import upfront.models as stale_models

    assert not hasattr(stale_models, "ArtifactKind"), "test fixture is not actually stale"
    return stale_models


def test_a_stale_upfront_copy_cannot_answer_for_this_plugin(stale_upfront):
    """Loading the backend must get THIS plugin's models, not the stale copy's."""
    api = _load_api_standalone()

    models = api._sub("models")
    assert hasattr(models, "ArtifactKind"), "the real models.py must be the one loaded"
    assert Path(models.__file__).resolve().parent == ROOT
    assert models is not stale_upfront


def test_the_stale_copy_does_not_break_a_run(stale_upfront):
    """End to end: `_scenario_from` builds a real Scenario under the stale copy."""
    api = _load_api_standalone()
    scenario = api._scenario_from({
        "title": "t",
        "documents": [{"type": "decision", "content": "Ship it"}],
    })
    assert scenario.title == "t"
    assert scenario.kind == "auto"


def test_the_backend_registers_no_fixed_module_name():
    """The package must be loaded under a path-derived name, not a hardcoded one."""
    src = API_FILE.read_text()
    assert '_PKG = "upfront"' not in src
    assert "hashlib.sha256" in src, "the module name must be derived from the install path"
    assert "from upfront" not in src
    assert "import upfront" not in src
