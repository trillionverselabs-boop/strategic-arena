import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# The Python package is `upfront` — a hyphen cannot be a package name — while the
# repository is `strategic-arena`, so a contributor's checkout arrives under a name the
# interpreter cannot import. Give sys.path a directory that contains the package under
# its real name: `import upfront` then works as a normal package import, including the
# relative imports inside `__init__.py` (a path-loaded module breaks on those).
if REPO.name == "upfront":
    sys.path.insert(0, str(REPO.parent))
else:
    _shim = Path(tempfile.mkdtemp(prefix="sa-import-"))
    _link = _shim / "upfront"
    if not _link.exists():
        _link.symlink_to(REPO, target_is_directory=True)
    sys.path.insert(0, str(_shim))


@pytest.fixture(autouse=True)
def tmp_hermes_home(tmp_path, monkeypatch):
    """Never let a test write into the real ~/.hermes."""
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home
