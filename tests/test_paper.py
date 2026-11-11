"""The paper lens — one artifact, two questions, and only one of them is optional.

A research paper is read as a product (moat decode) *and* as a market (the room).
The decode is not decoration: its facts go back in as a document, because every
party in the market room has read the same public paper. These tests hold that
wire up, and they hold the failure behaviour: a decode that fails degrades the
read, it never kills the run.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from upfront import engine
from upfront.models import Document, DocumentType, Scenario

# ── a model that answers both questions, and remembers what it was asked ──

DECODE_MARK = "the way a founder reads it"
EXTRACT_MARK = "stakeholder landscape"


class PaperLLM:
    model = "fake"
    temperature = 0.6

    def __init__(self, moat_payload=None, fail_decode=False):
        self.prompts = []
        self.moat_payload = moat_payload if moat_payload is not None else {
            "product": "A continuity gate that certifies a reused KV cache still behaves.",
            "buyer": "the inference-platform lead",
            "replaces": "recomputing the prefix after every model update",
            "disclosed": ["direct cache reuse"],
            "tacit": ["the update checkpoints", "the long-prefix QA set"],
            "replication_months": 2,
            "replication_basis": "measurement only — no training",
            "scale_dependence": "holds at a fraction of training compute",
            "nearest_prior_art": "cache reuse in agent communication",
            "authors_position": "no shipping product",
            "confidence": "high",
        }
        self.fail_decode = fail_decode

    def complete(self, prompt):
        self.prompts.append(prompt)
        if DECODE_MARK in prompt:
            if self.fail_decode:
                raise RuntimeError("provider down")
            return json.dumps(self.moat_payload)
        if EXTRACT_MARK in prompt or "You are extracting" in prompt:
            return json.dumps({
                "personas": [
                    {"name": "Inference platform", "role": "blocker", "stance": -0.6,
                     "capacity": 0.9, "reasons": ["cannot certify the cache [paper ¶1]"]},
                    {"name": "The authors' lab", "role": "competitor", "stance": -0.2,
                     "capacity": 0.8, "reasons": ["already ships the model [paper ¶2]"]},
                ],
                "relationships": [["Inference platform", "The authors' lab", "opposes"]],
            })
        if "Decide your move" in prompt:
            return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})
        return json.dumps({"claims": []})


def _paper_scenario(kind="paper"):
    return Scenario(
        title="KV cache reuse", kind=kind, window="30m",
        documents=[Document(type=DocumentType.DECISION,
                            content="Abstract: caches retain task information without "
                                    "reproducing the updated model's behavior.",
                            source="arxiv 2611.14051")],
    )


# ── the decode drives the room ─────────────────────────────────────────

def test_a_paper_run_decodes_the_moat_and_hands_it_to_the_room():
    llm = PaperLLM()
    res = engine.run_scenario(_paper_scenario(), llm)

    assert res.kind == "paper"
    assert res.moat["product"].startswith("A continuity gate")
    assert res.moat["clock"] == "commodity"          # 2 months, computed
    assert res.moat["replication_months"] == 2

    extract_prompts = [p for p in llm.prompts if EXTRACT_MARK in p]
    assert extract_prompts, "the room must still be drawn"
    assert "MOAT DECODE" in extract_prompts[0], (
        "the decode has to reach the extraction: a competitor in this room has read "
        "the same paper, and the room is wrong if it argues with a citation instead"
    )
    assert "2 months" in extract_prompts[0]


def test_the_decode_is_asked_before_the_room_is_drawn():
    llm = PaperLLM()
    engine.run_scenario(_paper_scenario(), llm)
    order = [DECODE_MARK in p for p in llm.prompts]
    first_decode = order.index(True)
    first_extract = next(i for i, p in enumerate(llm.prompts) if EXTRACT_MARK in p)
    assert first_decode < first_extract


def test_only_the_paper_lens_decodes_a_moat():
    """A README does not have a replication clock, and inventing one would be the
    same failure as printing blue ocean for an empty room."""
    llm = PaperLLM()
    res = engine.run_scenario(_paper_scenario(kind="repo"), llm)
    assert res.moat == {}
    assert not any(DECODE_MARK in p for p in llm.prompts)


def test_a_failed_decode_degrades_the_read_and_says_so():
    llm = PaperLLM(fail_decode=True)
    res = engine.run_scenario(_paper_scenario(), llm)

    assert res.moat.get("error"), "a failed decode must be recorded, not swallowed"
    assert res.moat.get("product", "") == ""
    assert res.personas, "the market read still runs without the clock"


def test_an_empty_decode_leaves_no_card_to_misread():
    """No product and no error is 'nothing to say', not 'no moat'."""
    llm = PaperLLM(moat_payload={})
    res = engine.run_scenario(_paper_scenario(), llm)
    assert res.moat == {}


# ── the lens reaches the engine from the API ───────────────────────────

def _api():
    path = Path(__file__).resolve().parent.parent / "dashboard" / "plugin_api.py"
    spec = importlib.util.spec_from_file_location("upfront_dashboard_paper_api", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_chosen_lens_is_not_dropped_at_the_route():
    """Regression: the form sent `kind`, the route ignored it, so a chosen room
    silently became whatever the link happened to look like."""
    mod = _api()
    scenario = mod._scenario_from({"title": "t", "kind": "paper",
                                   "documents": [{"type": "decision", "content": "x"}]})
    assert scenario.kind.value == "paper"

    auto = mod._scenario_from({"title": "t",
                               "documents": [{"type": "decision", "content": "x"}]})
    assert auto.kind.value == "auto"


def test_an_unknown_lens_is_a_400_not_a_quiet_room_swap():
    from fastapi import HTTPException

    mod = _api()
    with pytest.raises(HTTPException) as err:
        mod._scenario_from({"title": "t", "kind": "research-ish",
                            "documents": [{"type": "decision", "content": "x"}]})
    assert err.value.status_code == 400
    assert "paper" in err.value.detail


def test_the_report_shows_the_clock_for_a_paper():
    from upfront import reporting

    llm = PaperLLM()
    res = engine.run_scenario(_paper_scenario(), llm)
    md = reporting.write_report(res)
    assert "The paper, read as a product" in md
    assert "Replication clock: ~2 months" in md
    assert "Gives away" in md
    assert "Holds back" in md


def test_a_repo_report_has_no_paper_section():
    from upfront import reporting

    res = engine.run_scenario(_paper_scenario(kind="repo"), PaperLLM())
    assert "The paper, read as a product" not in reporting.write_report(res)
