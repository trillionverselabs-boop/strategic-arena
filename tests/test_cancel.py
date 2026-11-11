"""Cancel must stop a live run and write nothing partial to history."""

import pytest

from upfront import engine
from upfront.models import Scenario
from fakes import FakeLLM


def _scenario():
    return Scenario(title="t", goal="adoption", window="30m",
                    documents=[{"type": "decision", "content": "We are doing the thing."}])


def test_cancel_refuses_a_run_that_is_not_live():
    assert engine.cancel("no-such-run") is False


def test_cancel_marks_a_live_run():
    engine._PROGRESS["r1"] = {"status": "running"}
    assert engine.cancel("r1") is True
    assert engine._cancelled("r1") is True
    engine._CANCEL.pop("r1", None)


def test_a_cancelled_run_raises_and_records_the_state():
    llm = FakeLLM()
    engine._PROGRESS["r2"] = {"status": "running"}
    engine._CANCEL["r2"] = True
    with pytest.raises(engine.SimulationCancelled):
        engine.run_scenario_progress(_scenario(), llm, run_id="r2")
    assert engine.get_progress("r2")["status"] == "cancelled"


def test_a_cancelled_run_leaves_no_saved_run(tmp_path):
    llm = FakeLLM()
    before = set(p.name for p in engine.reporting.runs_dir().glob("*")) if engine.reporting.runs_dir().exists() else set()
    engine._PROGRESS["r3"] = {"status": "running"}
    engine._CANCEL["r3"] = True
    with pytest.raises(engine.SimulationCancelled):
        engine.run_scenario_progress(_scenario(), llm, run_id="r3")
    after = set(p.name for p in engine.reporting.runs_dir().glob("*")) if engine.reporting.runs_dir().exists() else set()
    assert after == before, "a cancelled run must not write to history"
