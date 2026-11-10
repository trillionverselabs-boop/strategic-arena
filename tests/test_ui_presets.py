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
    assert "0.4.5 · ui10" in UI.read_text()


def test_result_page_leads_with_the_answer_not_the_audit():
    """A reader who waited 30 minutes gets the 'so what' first, not a wall of prose."""
    js = UI.read_text()
    assert "What the rehearsal found" in js
    assert "Who can challenge this" in js
    assert "So what do I do" in js
    assert "show the full audit" in js
    assert "Nobody in this room can stop it." in js


def test_graph_explains_itself():
    js = UI.read_text()
    assert "Position: how much each party backs your move" in js
    assert "bigger = more power to stop it" in js
    assert "coalitions that formed" in js


def test_injection_has_a_visible_impact():
    js = UI.read_text()
    assert "Injected ✓ — " in js
    assert "Describe the counter-move first" in js
    assert "disabled: !injectText.trim()" not in js


def test_free_model_slowness_is_said_out_loud():
    js = UI.read_text()
    assert "Free models are rate-limited and slow" in js
    assert "eta:" in js


def test_cancel_is_offered_during_a_run():
    js = UI.read_text()
    assert "Cancel run" in js
    assert "Run cancelled" in js
    assert "/cancel/" in js


def test_the_run_screen_is_readable_over_a_busy_background():
    """Node labels carry a halo and near-white fill — the bleed-through is a
    desktop setting the user likes, so the text has to survive on top of it."""
    js = UI.read_text()
    assert "paintOrder: 'stroke'" in js
    assert "#f2f4f7" in js
    assert "text-(#c7cdd6)" in js


def test_the_form_warns_before_a_run_that_model_choice_is_gated():
    js = UI.read_text()
    assert "The host has not granted model choice" in js
    assert "/model-access" in js
    assert "config_key" in js
    assert "Choosing a specific model is a host permission" in js
