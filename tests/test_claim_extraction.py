import json

from upfront.claims import extract_claims
from upfront.models import Document, DocumentType, SimulationResult
from fakes import Boom


def _res():
    return SimulationResult(title="t", goal="adoption", rounds=8, personas=[])


def test_extracted_claims_carry_sources():
    docs = [Document(type=DocumentType.EVIDENCE, content="61% of CIOs block external routing")]
    out = extract_claims(_res(), __import__("tests.fakes", fromlist=["FakeLLM"]).FakeLLM(), docs)
    assert out[0]["kind"] == "extracted"
    assert "CIO" in out[0]["source"]


def test_failure_is_silent_and_empty():
    assert extract_claims(_res(), Boom(), []) == []
