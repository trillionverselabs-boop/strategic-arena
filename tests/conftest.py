import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO.parent))   # makes `import upfront` work


@pytest.fixture(autouse=True)
def tmp_hermes_home(tmp_path, monkeypatch):
    """Never let a test write into the real ~/.hermes."""
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home
