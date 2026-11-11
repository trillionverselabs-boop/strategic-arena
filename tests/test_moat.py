"""The moat decode — a paper read as a product with a clock on it.

Two things are load-bearing and tested here:

1. The **clock is computed from decoded facts, never asked of the model**, so the
   same paper cannot land in two different bands depending on how the model felt.
2. An **unassessed field stays unassessed**. A paper that states no replication
   time returns "unknown", not "protected" — the same discipline the sea read uses
   when it refuses to print blue ocean for an empty room.
"""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from upfront import moat  # noqa: E402
from upfront.models import Document, DocumentType  # noqa: E402


def paper(text="We present a method. Results follow."):
    return [Document(type=DocumentType.DECISION, content=text, source="paper")]


class Say:
    """Answers with whatever it was given, as JSON."""

    model = "fake"
    temperature = 0.6

    def __init__(self, payload):
        self.payload = payload
        self.prompt = ""

    def complete(self, prompt):
        self.prompt = prompt
        return json.dumps(self.payload) if not isinstance(self.payload, str) else self.payload


# ── the clock, computed ────────────────────────────────────────────────

@pytest.mark.parametrize("months,band", [
    (0.5, "commodity"),
    (3.0, "commodity"),      # the boundary: still inside a release cycle
    (3.1, "contested"),
    (9.0, "contested"),
])
def test_a_short_clock_is_a_feature_not_a_company(months, band):
    band_out, why = moat.clock_for(months, ["tacit thing"], "low")
    assert band_out == band
    assert why


def test_a_long_clock_is_only_a_moat_when_something_explains_it():
    """Twelve months of silence is not twelve months of protection. If the paper
    discloses everything and needs no unusual resources, the gap has no cause and
    the estimate is soft — so it is contested, not protected."""
    band, why = moat.clock_for(18.0, [], "")
    assert band == "contested"
    assert "soft" in why

    band, _ = moat.clock_for(18.0, ["undocumented data pipeline"], "")
    assert band == "protected"

    band, _ = moat.clock_for(18.0, [], "needs ~10^4 GPU-days")
    assert band == "protected"


def test_an_unstated_clock_is_unknown_not_protected():
    """The failure mode this guards against is a confident 'protected' resting on
    a number nobody gave."""
    band, why = moat.clock_for(None, ["tacit"], "high")
    assert band == "unknown"
    assert "does not state" in why


# ── the decode ─────────────────────────────────────────────────────────

def test_a_decode_fills_the_thesis_and_computes_the_band():
    llm = Say({
        "product": "A continuity gate that certifies a reused cache still behaves.",
        "buyer": "the inference-platform lead",
        "replaces": "recomputing the whole prefix after every model update",
        "disclosed": ["direct cache reuse", "functional cache divergence metric"],
        "tacit": ["the four update checkpoints", "the long-prefix QA set"],
        "replication_months": 2,
        "replication_basis": "measurement only, no training",
        "scale_dependence": "holds at a fraction of training compute",
        "nearest_prior_art": "cache-reuse work in agent communication",
        "authors_position": "academic authors with no shipping product",
        "confidence": "high",
    })
    m = moat.decode(paper(), llm)
    assert not m.error
    assert m.buyer.startswith("the inference")
    assert m.clock == "commodity"
    assert m.replication_months == 2
    assert m.confidence == "high"
    assert any("functional cache divergence" in d for d in m.disclosed)


def test_the_prompt_forbids_inventing_a_number():
    llm = Say({"product": "x", "confidence": "low"})
    moat.decode(paper(), llm)
    assert "Never guess a number to fill a field" in llm.prompt
    assert "replication_months" in llm.prompt


def test_a_failed_call_is_reported_not_raised():
    """A paper run without a decode is still a valid market read."""
    class Boom:
        model = "fake"
        temperature = 0.6

        def complete(self, prompt):
            raise RuntimeError("provider down")

    m = moat.decode(paper(), Boom())
    assert m.error and "provider down" in m.error
    assert m.product == ""
    assert m.clock == "unknown"


def test_a_prose_answer_is_an_error_not_a_guess():
    m = moat.decode(paper(), Say("I think this is probably quite defensible."))
    assert m.error
    assert "not as JSON" in m.error


def test_an_empty_decode_invents_nothing():
    m = moat.decode(paper(), Say({}))
    assert not m.error
    assert m.product == "" and m.buyer == ""
    assert m.clock == "unknown"
    assert m.replication_months is None


@pytest.mark.parametrize("value,expected", [
    (3, 3.0), ("4", 4.0), ("6 months", 6.0), ("9m", 9.0), ("12+", 12.0),
    (None, None), ("", None), ("n/a", None), (-2, None), ("soon", None), (1e9, None),
])
def test_a_plausible_replication_time_or_none(value, expected):
    assert moat._months(value) == expected


def test_the_brief_carries_what_the_room_needs_to_know():
    """The decode is fed back in as a document, so a competitor in the room can be
    argued about as someone who has read the same public paper."""
    m = moat.Moat(product="a verification gate", buyer="the router",
                  tacit=["undocumented eval harness"], replication_months=2,
                  clock="commodity", clock_why="inside a release cycle")
    brief = m.brief()
    assert "MOAT DECODE" in brief
    assert "a verification gate" in brief
    assert "undocumented eval harness" in brief
    assert "2 months" in brief
    assert "commodity" in brief


def test_a_missing_clock_says_unassessed_in_the_brief():
    brief = moat.Moat(product="p").brief()
    assert "not stated by the paper" in brief
