"""The dashboard backend must not put its own directory on sys.path.

The plugin ships a top-level ``tools.py``. While the plugin directory was on
``sys.path``, every ``import tools.*`` inside the host resolved to
``upfront/tools.py`` instead of Hermes' own ``tools`` package — so
``agent/gemini_schema.py`` → ``tools.schema_sanitizer`` died with
"attempted relative import with no known parent package" and a review run
surfaced as "Run failed: the model call failed". These tests pin the two things
that have to stay true.
"""

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
API_FILE = PLUGIN_ROOT / "dashboard" / "plugin_api.py"


def _load_api_standalone(name: str = "hermes_dashboard_plugin_upfront_test"):
    """Import plugin_api.py the way the dashboard loader does: by file path, alone."""
    spec = importlib.util.spec_from_file_location(name, API_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_plugin_dir_is_never_on_sys_path():
    """Loading the api module must not add its own directory to sys.path."""
    before = set(sys.path)
    _load_api_standalone()

    added = {str(Path(p).resolve()) for p in sys.path if p not in before}
    assert str(PLUGIN_ROOT.resolve()) not in added
    assert str(PLUGIN_ROOT.parent.resolve()) not in added


def test_engine_is_importable_by_spec():
    """The package loads as a package (relative imports work) without sys.path."""
    before = list(sys.path)
    try:
        mod = _load_api_standalone()
    finally:
        sys.path[:] = before

    assert mod.engine is importlib.import_module("upfront.engine")


def test_tools_import_never_lands_inside_the_plugin():
    """End to end, from a neutral cwd: `import tools` must not pick up the plugin's copy.

    That is exactly the import chain that used to break inside the host. Here the
    host's own ``tools`` package may not be importable at all (it is not on this
    process's path) — which is fine; the point is that the plugin's copy must not
    be reachable as ``tools``.
    """
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('api_probe', {str(API_FILE)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['api_probe'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        "try:\n"
        "    import tools\n"
        "except ImportError:\n"
        "    print('not-found')\n"
        "else:\n"
        "    print(tools.__file__)\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=str(Path(sys.executable).resolve().parents[1]))
    assert out.returncode == 0, out.stderr
    resolved = out.stdout.strip()
    assert resolved == "not-found" or Path(resolved).resolve().parent != PLUGIN_ROOT
