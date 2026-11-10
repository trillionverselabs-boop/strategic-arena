"""Static guards on the shipped desktop UI.

These are cheap and deliberate: the page is one uncompiled ESM file, so a guard
here is the only check that runs without the renderer. Each test pins a *copy
decision* or a *structure decision*, not the whole file — when the wording
changes on purpose, update the guard with it.
"""

from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "desktop" / "plugin.js"


def test_form_recommends_a_first_pass():
    js = UI.read_text()
    assert "For a first pass: a flash-class model at 24h." in js
    assert "Spend on 48h and a bigger model only when the decision is expensive." in js


def test_form_says_what_a_run_costs():
    js = UI.read_text()
    assert "model calls ·" in js


def test_build_stamp_is_the_current_one():
    assert "0.5.6 · ui18" in UI.read_text()


def test_result_page_leads_with_the_answer_not_the_audit():
    """A reader who waited 30 minutes gets the call first, not a wall of prose."""
    js = UI.read_text()
    assert "the call" in js
    assert "who can stop it" in js
    assert "what they need" in js
    assert "your best move" in js
    assert "The call, frozen" in js
    assert "show the full audit" in js


def test_the_room_is_readable_without_a_number_you_cannot_place():
    """Every metric carries a word and a scale. Numbered dots alone were the
    first real user's complaint, so they must never come back."""
    js = UI.read_text()
    assert "The room, in order" in js
    assert "power to stop" in js
    # three named, counted groups instead of a colour legend
    assert "function ZoneStrip(" in js
    assert "can stop you or make it cost" in js
    assert "moves if the reason is good" in js
    assert "already with you" in js
    assert "Bar length = how strongly they back or oppose it" in js
    assert "n.stance >= 0 ?" not in js            # no stance printed inside a dot


def test_the_debate_is_shown_not_just_the_positions():
    """CAMEL's point: the conversation is the artifact. A run's own frozen
    statements are the thing a reader replays."""
    js = UI.read_text()
    assert "What they actually said" in js
    assert "Round ${" in js
    assert "/events/" in js


def test_positions_over_time_are_drawn():
    """OASIS's point: this is a run over time. The movement chart is the only
    place a reader sees that, and its labels must stay legible."""
    js = UI.read_text()
    assert "How positions moved" in js
    assert "fontFamily: 'inherit'" in js
    assert "paintOrder: 'stroke'" in js


def test_the_scorecard_has_a_reason_to_come_back():
    js = UI.read_text()
    assert "hit rate" in js
    assert "scored" in js
    assert "it held" in js
    assert "it broke" in js
    assert "/calibration" in js


def test_a_stale_window_is_told_the_truth_not_a_fairytale():
    """The old card said "press Reload UI". A page reload cannot change a file
    that lives on the machine the window runs on, so that instruction was a
    lie. It now says so, and points at the app's own update path."""
    js = UI.read_text()
    assert "Reload page" in js
    assert "this window is behind" in js
    assert "Open plugin settings" in js
    assert "Reload UI" not in js
    # rule 03: no updater of our own files, see tests/test_no_self_update.py
    assert "Download the UI file" not in js


def test_the_word_rehearsal_is_gone():
    """The user's call: no dress-rehearsal framing anywhere a reader can see it."""
    js = UI.read_text().lower()
    for banned in ("rehearse", "rehearsal", "rehearses", "dress rehearsal"):
        assert banned not in js, banned
    # the room is named, and consistent
    assert "const ARENA = 'Strategic Arena'" in UI.read_text()
    assert "is in session" in UI.read_text()


def test_the_home_screen_says_what_you_get():
    js = UI.read_text()
    assert 'Find out who can stop you — before you commit.' in js
    assert "who can stop you" in js
    assert "what they need" in js
    assert "A scorecard" in js
    assert "nothing is invented" in js


def test_history_does_not_eat_the_page():
    """Every run is one line — title, a mini room, verdict, blocker, heat,
    scored, age — capped at six until asked, and below the content so the top
    can breathe."""
    js = UI.read_text()
    assert "your reviews" in js
    assert "click a row to read it" in js
    assert "show all" in js
    assert "history.slice(0, 6)" in js
    # the mini graph: one dot per party, position and power
    assert "function MiniRoom(" in js
    assert "function RunLine(" in js
    # the old tall cards are gone
    assert "function RunCard(" not in js
    assert "pick up where you left off" not in js


def test_injection_has_a_visible_impact():
    js = UI.read_text()
    assert 'Injected ✓ — "' in js
    assert "Describe the counter-move first" in js


def test_free_model_slowness_is_said_out_loud():
    js = UI.read_text()
    assert "Free models are rate-limited and slow" in js
    assert "eta:" in js


def test_cancel_is_offered_during_a_run():
    js = UI.read_text()
    assert "Cancel run" in js
    assert "Run cancelled" in js
    assert "/cancel/" in js


def test_text_survives_over_a_busy_background():
    """A name drawn on a canvas carries a halo; the bleed-through is a desktop
    setting the user likes, so the text has to survive on top of it."""
    js = UI.read_text()
    assert "paintOrder: 'stroke'" in js
    assert "'#e8ecf2'" in js
    assert "rgba(6,8,12,.86)" in js


def test_the_form_warns_before_a_run_that_model_choice_is_gated():
    js = UI.read_text()
    assert "The host has not granted model choice" in js
    assert "/model-access" in js
    assert "config_key" in js
    assert "Choosing a specific model is a host permission" in js


def test_no_hardcoded_text_colours_that_break_the_theme():
    """`text-(#hex)` is not a valid Tailwind arbitrary-value form; it silently
    renders nothing, which is how the old page lost its grey text."""
    js = UI.read_text()
    assert "text-(#c7cdd6)" not in js
    assert "text-[#c7cdd6]" in js or "var(--ui-text-secondary)" in js
