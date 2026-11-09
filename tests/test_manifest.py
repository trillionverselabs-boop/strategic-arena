import json

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from tests.fakes import FakeLLM


def test_manifest_is_first_line_of_log():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it", source="memo")])
    res = engine.run_scenario(sc, FakeLLM())
    lines = (reporting.runs_dir() / res.run_id / "log.jsonl").read_text().splitlines()
    first = json.loads(lines[0])
    assert first["type"] == "manifest"
    assert first["model"] == "fake"
    assert first["documents"][0]["chars"] == len("Ship it")
    assert len(first["extract_prompt_sha"]) == 12
    assert first["code_commit"]
