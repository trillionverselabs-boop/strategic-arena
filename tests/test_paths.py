import pytest

from upfront import paths


def test_data_root_follows_hermes_home(tmp_hermes_home):
    root = paths.data_root()
    assert str(root).startswith(str(tmp_hermes_home))
    assert paths.runs_dir() == root / "runs"
    assert paths.graph_path() == root / "graph.json"


def test_hermes_home_prefers_the_host_constant(monkeypatch, tmp_hermes_home):
    hc = pytest.importorskip("hermes_constants")
    sentinel = tmp_hermes_home / "from-host-constant"
    monkeypatch.setattr(hc, "get_hermes_home", lambda: sentinel)
    assert paths._hermes_home() == sentinel
