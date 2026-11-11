import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# Import the plugin package *by path*, under a fixed module name, so the suite passes
# whatever the checkout directory is called. A clone arrives as `strategic-arena`, and
# `import strategic_arena` would need the folder to be spelled that way; a plain
# `sys.path` insert only works when the folder happens to be named `upfront`.
if "upfront" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "upfront", REPO / "__init__.py", submodule_search_locations=[str(REPO)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["upfront"] = module
    spec.loader.exec_module(module)  # noqa: S301 — our own file
sys.path.insert(0, str(REPO))


@pytest.fixture(autouse=True)
def tmp_hermes_home(tmp_path, monkeypatch):
    """Never let a test write into the real ~/.hermes."""
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home
