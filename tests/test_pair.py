from upfront import engine, reporting
from upfront.models import Document, DocumentType, Intervention, Scenario
from fakes import InterventionAware


def test_pair_reports_a_delta():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    pair = engine.run_pair(sc, InterventionAware(),
                           Intervention(name="Publish evals", description="Publish eval suite first"),
                           "ab1ab1ab1ab1", "ab2ab2ab2ab2")
    assert (reporting.runs_dir() / "ab1ab1ab1ab1" / "pair.json").exists()
    assert pair["verdict"] in ("counter-move works", "counter-move did not help")
    assert "friction_delta" in pair
