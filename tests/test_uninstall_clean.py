"""The purge script must actually purge — and must keep run history on request."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "uninstall-clean.py"


def _load():
    spec = importlib.util.spec_from_file_location("uninstall_clean", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def fake_residue(tmp_hermes_home):
    """A machine that looks like it just ran `plugins remove`."""
    home = Path(tmp_hermes_home)
    files = [
        home / "plugins" / "upfront" / "plugin.yaml",
        home / "plugin-data" / "upfront" / "runs" / "abc" / "meta.json",
        home / "installs" / "a" / "environments" / "b" / "venv" / "lib" / "python3.14"
        / "site-packages" / "hermes_upfront-0.3.0.dist-info" / "METADATA",
        home / "cache" / "plugin-update-locks" / "upfront.lock",
        home / "installs" / "a" / "environments" / "b" / "workspace" / "plugin-sources"
        / "upfront-deadbeef" / "plugin.yaml",
    ]
    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x")
    return home


def test_dry_run_changes_nothing(fake_residue):
    mod = _load()
    mod.sys.argv = ["uninstall-clean.py", "upfront", "--dry-run"]
    assert mod.main() == 0
    assert (fake_residue / "plugins" / "upfront" / "plugin.yaml").exists()


def test_purge_leaves_no_trace(fake_residue):
    mod = _load()
    mod.sys.argv = ["uninstall-clean.py", "upfront"]
    assert mod.main() == 0
    assert mod.find_matches(fake_residue, "upfront") == []


def test_keep_data_preserves_run_history(fake_residue):
    mod = _load()
    mod.sys.argv = ["uninstall-clean.py", "upfront", "--keep-data"]
    assert mod.main() == 0
    assert (fake_residue / "plugin-data" / "upfront" / "runs" / "abc" / "meta.json").exists()
    assert not (fake_residue / "plugins" / "upfront").exists()
