"""The free-model caveat is a product fact, not a review note.

A user decides whether to press Run on what the form says, so the three claims that
matter are pinned here: which model runs, that a free tier is rate-limited, and what
to do when a run fails. Rewrite the copy and these fail — which is the point.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / "desktop" / "plugin.js"
README = ROOT / "README.md"
MODELS = ROOT / "docs" / "MODELS.md"
ENTRY = ROOT / "docs" / "catalog-entry.draft.yaml"


def test_the_form_says_which_model_runs_and_what_a_free_one_costs():
    js = UI.read_text()
    assert "default model setting" in js
    assert "rate-limited" in js
    assert "a paid model is the recommendation" in js
    assert "change the session to another model and run it again".lower() in js.lower()
    # the atom the form reads is the app's binding for this session, and it can
    # lag the picker — so the copy must say that rather than claim the default
    assert "bound to this session" in js
    assert "prints the model that actually served it" in js


def test_the_form_says_ingestion_is_the_longest_step():
    """The wait a user is most likely to read as "broken" is the ingest, not the
    rounds. It is caused by the links, so the notice lives on the links field."""
    js = UI.read_text()
    assert "longest single step of a run" in js
    assert "Most of that wait is ingestion" in js


def test_the_long_timelines_do_not_claim_to_be_recommended():
    """24h used to read "Recommended. Full reaction cycle." — which contradicts the
    README (positions stop moving after 8-10 rounds) and suggestWindow, which never
    proposes above 12h."""
    js = UI.read_text()
    assert "Recommended. Full reaction cycle." not in js
    assert "Confirmation, not discovery" in js


def test_the_caveat_is_dropped_only_when_the_catalogue_says_paid():
    """A $0.017 paid run was being warned about free tiers. The caveat is now
    conditional on the catalogue's own price for this exact id, and on nothing
    else: an unknown id keeps the warning rather than assuming a model is paid."""
    js = UI.read_text()
    assert "const paidKnown = !!(price && price.found && !price.free)" in js
    assert "Paid model — the free-tier caveat does not apply" in js
    # both branches must still exist: the free one is the default
    assert "This runs on your Hermes model — free tier included, rate limits and all" in js
    assert "a paid model is the recommendation" in js


def test_the_readme_has_the_free_model_section():
    text = README.read_text()
    assert "### Free models: supported, slower, and rate-limited" in text
    assert "default model setting" in text
    assert "a paid model is the recommendation" in text


def test_the_models_doc_states_all_three_facts():
    text = MODELS.read_text()
    for phrase in ("default model setting", "rate-limited", "change the model"):
        assert phrase in text.lower(), phrase


def test_the_install_prompt_carries_the_caveat():
    text = ENTRY.read_text()
    assert "Free models are supported but rate-limited" in text
    assert "change the model in the app and run it again" in text
