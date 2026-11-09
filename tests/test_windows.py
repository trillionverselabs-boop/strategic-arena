from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario, Window
from tests.fakes import FakeLLM

ORDER = ["30m", "1h", "4h", "6h", "12h", "24h", "48h"]


def test_timeline_options_and_rounds():
    rounds = [Window(w).rounds for w in ORDER]
    assert rounds == sorted(rounds), "more time must never mean fewer rounds"
    assert Window("30m").rounds == 3
    assert Window("48h").rounds == 20


def test_compare_across_timelines():
    docs = [Document(type=DocumentType.DECISION, content="Open-weight Arete")]
    a = engine.run_scenario(Scenario(title="Same decision", window="30m", documents=docs), FakeLLM())
    b = engine.run_scenario(Scenario(title="Same decision", window="24h", documents=docs), FakeLLM())
    cmp = reporting.compare_runs("same decision")
    assert cmp["runs"] == 2
    assert cmp["friction_spread"] is not None
    assert cmp["blocker_stable"] is True
    assert set(cmp["drift_between"]) == {a.run_id, b.run_id}
    assert cmp["reading"]
