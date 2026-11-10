"""The ledger's honesty rules, pinned as copy guards.

The design mockup showed a "+6 coalition interaction" in the heat. This engine's
friction is additive, so that number cannot exist — and a number you cannot
compute must not appear on the page. These guards keep it off.
"""

from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "desktop" / "plugin.js"


def js() -> str:
    return UI.read_text()


def test_the_page_reads_the_ledger_from_the_backend():
    """It is arithmetic, so it is computed once, server-side, and fetched."""
    assert "ctx.rest(`/leverage/${runId}`)" in js()
    assert "function HeatLedger(" in js()
    assert "function HeatWaterfall(" in js()


def test_heat_and_power_are_never_conflated():
    assert "Points are heat, not power" in js()
    assert "The veto column is the lever" in js()


def test_the_method_is_named_on_the_page():
    assert "lev.method" in js()
    assert "neutralising each party in turn" in js()


def test_no_invented_coalition_interaction():
    """The mockup's hatched "+6" is gone; only the computed kinds remain."""
    src = js()
    assert "'heat'" in src and "'veto'" in src          # both kinds, both computed
    assert "+6 interaction" not in src
    assert "pr.line" in src            # every coalition sentence comes from the server


def test_a_supporter_is_shown_as_cooling_never_a_negative_bar():
    assert "pp.cools" in js()
    assert "repeating-linear-gradient" in js()


def test_the_palette_is_the_brand_blue_not_a_stoplight():
    src = js()
    assert "'#4c9bf0'" in src
    assert "#46a758" not in src and "#e5484d" not in src


def test_the_accent_is_scoped_to_this_page():
    """The blue button comes from scoping --ui-accent here, not from patching core."""
    assert "'--ui-accent': BRAND.blue" in js()
