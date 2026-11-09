from upfront import paths


def test_data_root_follows_hermes_home(tmp_hermes_home):
    root = paths.data_root()
    assert str(root).startswith(str(tmp_hermes_home))
    assert paths.runs_dir() == root / "runs"
    assert paths.graph_path() == root / "graph.json"
