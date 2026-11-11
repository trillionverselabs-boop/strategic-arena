"""The UI must not render an off-axis sea state as an unclassified axis.

An off-axis read (currently 'insufficient') is the absence of a read, not a
point on the competition scale. The panel says why instead of lighting a pill.
"""
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "desktop" / "plugin.js").read_text()


def test_an_off_axis_read_is_not_drawn_as_a_point_on_the_scale():
    assert "sea && !seaDef" in JS
    assert "SEA[sea.state]" in JS


def test_the_reason_is_shown_not_just_the_colour():
    assert "competition read:" in JS
    assert "insufficient input" in JS


def test_the_named_sea_still_carries_its_meaning():
    """The bands are named, and the name has to be readable by a person who has
    never heard "blue ocean" — the reader asked what it meant, twice."""
    assert "Red ocean" in JS
    assert "Purple ocean" in JS
    assert "Nobody is fighting this yet" in JS
    assert "the risk here is indifference, not opposition" in JS
