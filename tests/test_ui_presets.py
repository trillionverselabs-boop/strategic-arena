"""R4 — model-aware presets: the form recommends a sensible first pass.

A cheap static guard: the guidance must actually be in the shipped UI, and the build
stamp must still be the one the test protocol looks for.
"""

from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "desktop" / "plugin.js"


def test_form_recommends_a_first_pass():
    js = UI.read_text()
    assert "For a first pass: a flash-class model at 24h." in js
    assert "Spend on 48h and a bigger model only when the decision is expensive." in js


def test_recommendation_sits_below_the_cost_line():
    lines = UI.read_text().splitlines()
    cost = next(i for i, l in enumerate(lines) if "model calls ·" in l)
    rec = next(i for i, l in enumerate(lines) if "For a first pass" in l)
    assert rec == cost + 1, "the preset must read directly under the cost line"


def test_build_stamp_is_the_test_protocol_one():
    assert "0.3.3 · ui4" in UI.read_text()
