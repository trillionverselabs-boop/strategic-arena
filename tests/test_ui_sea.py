"""The UI must not render an off-axis sea state as an unclassified axis."""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "desktop" / "plugin.js").read_text()


def test_ui_handles_a_state_that_is_not_on_the_axis():
    assert "SEA_ORDER.includes(sea.state)" in JS
    assert "insufficient input" in JS


def test_ui_shows_the_reason_not_just_the_colour():
    assert "sea.why || ''" in JS or 'sea.why' in JS
