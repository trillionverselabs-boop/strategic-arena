"""Static guards on the shipped desktop UI.

These are cheap and deliberate: the page is one uncompiled ESM file, so a guard
here is the only check that runs without the renderer. Each test pins a *copy
decision* or a *structure decision*, not the whole file — when the wording
changes on purpose, update the guard with it.
"""

from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "desktop" / "plugin.js"


def test_the_form_shows_the_session_model_and_what_a_run_will_cost():
    """A picker needed a live catalogue and a host permission the app never
    grants. A readout needs neither: the model comes from the app's own state and
    the numbers are arithmetic over rounds and prompt size."""
    js = UI.read_text()
    assert "host.state.model" in js            # the real model, not a copy of it
    assert "tokens in" in js and "tokens out" in js
    assert "modelId" not in js
    assert "/models" not in js


def test_the_timeline_suggests_a_length_and_says_why():
    """Seven options with no recommendation is a coin flip. The suggestion is
    about the input, and the long end is honest about what it buys."""
    js = UI.read_text()
    assert "function suggestWindow(" in js
    low = js.lower()
    assert "suggested for this input" in low
    assert "stops moving after 8" in js
    assert "rarely needed" in low


def test_the_run_says_what_it_actually_cost():
    """Estimated money before (published price for THIS model) and real money
    after (the host's own usage), and neither can be a made-up number."""
    js = UI.read_text()
    assert "/price?" in js
    assert "at the published price" in js
    assert "cost_known" in js
    assert "spent" in js


def test_the_evidence_is_three_tabs_not_three_screens():
    """Stacked, the ledger, the movement chart and the transcript were most of the
    page's scroll. They answer different questions at different moments, so they
    are tabs — and each tab carries its size, so the reader knows what is in it
    without opening it."""
    js = UI.read_text()
    assert "TabsList" in js and "TabsTrigger" in js
    for tab in ("over time", "the ledger", "what they said"):
        assert tab in js, tab
    assert "evidenceTab === 'moves'" in js
    assert "evidenceTab === 'ledger'" in js
    assert "evidenceTab === 'words'" in js
    # each of the three renders exactly once now — no duplicate stacked copies
    assert js.count("jsx(Transcript, {") == 1
    assert js.count("jsx(MovementChartCard, {") == 1
    assert js.count("jsx(HeatLedger, { lev:") == 1


def test_the_answer_comes_before_the_evidence():
    """The reader's complaint was ordering: six sections of evidence before the
    answer. Five lines at the top, two lines each, then the proof."""
    js = UI.read_text()
    assert "function AnswerCard(" in js
    for row in ("you could build", "who pays", "lead time", "the market", "what to do"):
        assert row in js, row
    # the card reads the decoded moat, and states the standpoint it answers from
    assert "read as an entrepreneur deciding whether to build it" in js
    assert "jsx(AnswerCard" in js
    assert js.index("jsx(AnswerCard") < js.index("jsx(PaperRead")
    assert js.index("jsx(AnswerCard") < js.index("jsx(VerdictPanel")
    # nothing in it may become a paragraph again
    assert "WebkitLineClamp: 2" in js
    assert "function firstSentence(" in js


def test_the_paper_evidence_is_opt_in():
    """Gives-away / holds-back is evidence for the clock; it used to print two
    bullet lists and three paragraphs unconditionally."""
    js = UI.read_text()
    assert "How long the lead lasts" in js
    assert "'show the evidence'" in js
    assert "things a rebuilder gets free from the PDF" in js


def test_build_stamp_is_the_current_one():
    assert "0.6.3 · ui36" in UI.read_text()


def test_the_live_run_shows_a_blue_live_pill_and_the_word_live_once():
    """The status is a pill, not a button: a control there would compete with
    Cancel run, and the pill has to survive every theme as brand blue.
    """
    js = UI.read_text()
    assert "${ARENA} - LIVE" in js
    assert "${ARENA} · live" not in js
    assert ("const SUBTITLE = 'Understand the landscape before investing valuable resources'"
            in js)


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
    assert 'Read what it means before it reads you.' in js
    # the output contract: an artifact goes in, a landscape read comes out
    for tile in ("What it means", "The room", "Who decides", "The field",
                 "The price", "The record"):
        assert tile in js, tile
    assert "a repo README, a blog link, a launch post, a whitepaper, a case study" in js


def test_the_input_is_an_artifact_not_a_decision_form():
    """The product reads what you are about to publish, not a plan you filed."""
    js = UI.read_text()
    assert "Add what you want evaluated" in js
    assert "a README, a post, a whitepaper, an announcement" in js
    assert "nothing is invented" in js
    # the lens is offered, and the buttons agree with each other
    assert "const KINDS = [" in js
    assert "const KIND_ROOM = {" in js
    assert js.count("Start arena session") >= 2


def test_the_result_leads_with_meaning_and_the_agreement_case():
    """'What it means' comes before the verdict; the supporters are priced too."""
    js = UI.read_text()
    assert "function WhatItMeans(" in js
    assert "function OnYourSide(" in js
    assert "'What it means'" in js
    assert "What's already on your side" in js
    assert "points of heat out of the room" in js    # no jargon: heat, not "cooling"
    # meaning first, then the call, then the good news, then the friction math:
    # a reader needs their baseline support before the arithmetic of what it costs
    assert js.index("jsx(WhatItMeans") < js.index("jsx(VerdictPanel")
    assert js.index("jsx(VerdictPanel") < js.index("jsx(OnYourSide")
    assert js.index("jsx(OnYourSide") < js.index("jsx(HeatLedger")
    # a supporter's own words carry the argument, not a paraphrase
    assert "(p.reasons || [])[0]" in js


def test_the_wait_is_alive_and_reload_is_internal():
    """A 30-60s first round must not look like a hang, and "Reload page" must
    re-render this view rather than tear down the webview."""
    js = UI.read_text()
    assert "function WorkingBar(" in js
    assert "repeatCount: 'indefinite'" in js          # the shimmer actually moves
    assert "is the slow one" in js                      # and says why
    assert "window.location.reload()" not in js         # no webview teardown
    assert "setReloadNonce(n => n + 1)" in js           # remount the body instead
    # one accent per surface: header CTA is the light action, in-panel stays blue
    assert "function LightAction(" in js
    assert "jsx(PrimaryAction, { onClick: inject" in js
    # the label follows the contract vocabulary
    assert "children: 'counter-moves'" in js
    assert "change the situation" not in js.lower()


def test_the_demo_path_is_one_click_from_a_cold_start():
    """A judge has sixty seconds: the first thing they can do is read a finished,
    scored session, not fill in a form."""
    js = UI.read_text()
    assert "function DemoCard(" in js
    assert "function DemoReview(" in js
    assert "start here — a finished session" in js
    assert "See the finished review" in js
    # it sits on the idle home, above the output contract
    assert js.index("jsx(DemoCard") < js.index("jsx(WhatYouGet")
    # the condensed view can always escape to the full session or a new one
    assert "the full session" in js
    # scored sessions are preferred: the point is that this thing can be wrong
    assert "h.verified && h.verified.verdict" in js
    # the demo carries the graded claim, not just the verdict
    assert "frozen before the answer was known" in js


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


def test_a_long_run_announces_itself_before_it_starts():
    """Anything that visibly takes minutes says so, in the accent colour, or a
    reviewer watches a spinner and decides the plugin is broken."""
    js = UI.read_text()
    assert "longWait" in js
    assert "that is normal, not a hang" in js
    assert "tl.rounds >= 12 || kind === 'paper'" in js
    assert "you can stop it between rounds" in js
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


def test_the_model_choice_cannot_be_gated_because_it_is_not_offered():
    """The old form warned that a choice would be refused. The honest fix was to
    stop offering the choice, so neither the warning nor its route survives."""
    js = UI.read_text()
    assert "/model-access" not in js
    assert "allow_model_override" not in js
    assert "The host has not granted model choice" not in js


def test_no_hardcoded_text_colours_that_break_the_theme():
    """`text-(#hex)` is not a valid Tailwind arbitrary-value form; it silently
    renders nothing, which is how the old page lost its grey text."""
    js = UI.read_text()
    assert "text-(#c7cdd6)" not in js
    assert "text-[#c7cdd6]" in js or "var(--ui-text-secondary)" in js
