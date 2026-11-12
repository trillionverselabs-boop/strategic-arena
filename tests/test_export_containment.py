"""`out_dir` comes from the model; the export must stay in the plugin data dir."""

import pytest

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from upfront.paths import data_root
from fakes import FakeLLM


def _run():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


def test_an_absolute_out_dir_outside_the_data_root_is_refused(tmp_hermes_home):
    res = _run()
    escape = tmp_hermes_home / "escape"
    with pytest.raises(ValueError):
        reporting.export_decision(res.run_id, out_dir=str(escape))
    assert not escape.exists(), "nothing may be written outside the data root"


def test_a_parent_traversal_out_dir_is_refused():
    res = _run()
    escape = data_root().resolve().parent.parent / "escape"
    with pytest.raises(ValueError):
        reporting.export_decision(res.run_id, out_dir="../../escape")
    assert not escape.exists()


def test_a_relative_out_dir_inside_the_data_root_still_works():
    res = _run()
    path = reporting.export_decision(res.run_id, out_dir="decisions/2026-11")
    assert "decisions/2026-11" in path
    assert __import__("pathlib").Path(path).resolve().is_relative_to(data_root().resolve())


def test_an_absolute_out_dir_inside_the_data_root_is_allowed():
    res = _run()
    path = reporting.export_decision(res.run_id, out_dir=str(data_root() / "decisions"))
    assert __import__("pathlib").Path(path).resolve().is_relative_to(data_root().resolve())
