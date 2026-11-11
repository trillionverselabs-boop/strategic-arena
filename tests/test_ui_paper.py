"""The paper lens has to explain itself in the interface.

A research paper is the one artefact someone can hand this tool expecting a peer
review, or expecting a market forecast, and get neither. Both misreadings are the
product's fault, not the user's — so the lens states what it is and what it
refuses to do *on the form*, before a run costs anyone 20 minutes. These are
static guards because the page ships as one uncompiled ESM file.
"""

from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "desktop" / "plugin.js").read_text()


def test_the_paper_lens_is_offered_separately_from_a_whitepaper():
    """A whitepaper is judged on whether the method is defensible. A paper is
    judged on what product it implies. Two questions, two rooms — one entry point
    for both would guarantee the wrong room half the time."""
    assert "{ v: 'paper', label: 'Research paper" in JS
    assert "{ v: 'whitepaper', label: 'Whitepaper" in JS
    assert "paper: \"the incumbent it attacks, the fast follower" in JS


def test_the_form_explains_the_lens_before_the_run():
    assert "function PaperLensNote" in JS
    assert "kind === 'paper' ? jsx(PaperLensNote, {}) : null" in JS
    assert "Reading a paper as a product" in JS


def test_the_explainer_says_what_it_is_not():
    """The refusal is the trust: no peer review, no revenue forecast. Deleting
    this line would turn an honest read into a claim it cannot support."""
    assert "Not a peer review" in JS
    assert "does not predict" in JS
    assert "market share" in JS


def test_the_explainer_promises_exactly_the_three_things_it_delivers():
    for promised in ("the product", "the clock", "the room"):
        assert f"['{promised}'," in JS or f"['{promised}'" in JS
    assert "the buyer who actually signs" in JS
    assert "rebuild it from the text" in JS


def test_the_result_leads_with_the_clock_before_the_room():
    """The clock is the answer to 'how would the market take it', so it sits above
    what-it-means and the room."""
    assert JS.index("jsx(PaperRead, { moat: result.moat })") < JS.index(
        "jsx(WhatItMeans, { read: result.read, kind: result.kind })")


def test_an_unknown_clock_is_printed_as_unknown():
    assert "no basis for a number" in JS
    assert "unknown" in JS
    # never a placeholder number dressed up as data
    assert "~0 months" not in JS


def test_a_failed_decode_says_so_instead_of_vanishing():
    assert "The paper decode did not complete" in JS
    assert "Re-run to decode it" in JS
