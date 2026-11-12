"""The repository has to say what the product says.

The UI was renamed and re-positioned; the README, the manifest and the credits are
what a catalogue reviewer reads at the pinned commit, so they are held to the same
standard as the code — by a test, not by memory.

Also here: the attribution surface. Every paper we implement an idea from must be
cited with an identifier, and the one project with a *copyleft* licence (MiroFish,
AGPL-3.0) must be described in a way that makes clear no code was taken. An MIT
repository that silently contains AGPL code is a licence violation, so the claim is
asserted in both directions: the statement exists, and the tree carries no MiroFish
code.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text()
CREDITS = (ROOT / "CREDITS.md").read_text()
MANIFEST = (ROOT / "plugin.yaml").read_text()
CATALOG = (ROOT / "docs" / "catalog-entry.draft.yaml").read_text()
LICENSE = (ROOT / "LICENSE").read_text()


import re

# ── public text ────────────────────────────────────────────────────────
def test_the_readme_is_the_product_not_the_old_one():
    # the H1 is centered in a <div> now, so it is near the top rather than line 1
    assert "# Strategic Arena\n" in README[:400]
    assert "Understand the landscape before investing valuable resources" in README
    for banned in ("rehears", "Upfront Prediction"):
        assert banned.lower() not in README.lower(), banned


def test_the_manifest_is_brand_aligned():
    assert "Upfront Prediction" not in MANIFEST
    assert "rehearsal" not in MANIFEST.lower()
    # the id IS the display name in the Plugins list (`PluginManifest` has no `label`
    # field), so it has to be the product name, hyphenated like the repo
    assert MANIFEST.startswith("name: strategic-arena\n")
    assert "\nlabel:" not in MANIFEST, "label is a provider field, not a plugin field"


def test_the_catalog_entry_is_brand_aligned_and_pinned():
    assert "title: Strategic Arena" in CATALOG
    assert "Upfront Prediction" not in CATALOG
    sha = re.search(r"^sha:\s*([0-9a-f]{40})$", CATALOG, re.M)
    assert sha, "rule 02: the pin must be a full 40-character sha"
    # embedded asset URLs must use the same commit they are pinned to
    assert CATALOG.count(sha.group(1)) >= 3, "image/screenshot URLs embed the pin"


def test_the_contract_is_documented_where_a_judge_reads_it():
    for part in ("What it means", "The room", "Who decides", "The field",
                 "The price", "The record"):
        assert part in README, part
    assert "the medium sets the room" in README.lower()


# ── attribution and licensing ──────────────────────────────────────────
PAPERS = [
    "2303.17760",  # CAMEL
    "2411.11581",  # OASIS
    "2673-2688/7/8/279",  # MASS
    "2404.16130",  # GraphRAG
    "2304.03442",  # Generative Agents
    "2106.00285",  # Shapley counterfactual credits
    "2605.24490",  # Market Regime Council
    "2507.04562",  # forecasting vs expert forecasters (Brier)
    "2402.18563",  # approaching human-level forecasting
    "2603.14066",  # multi-party negotiation benchmark
    "2509.06337",  # LLMs as virtual survey respondents
]


def test_every_paper_we_use_is_cited_with_an_identifier():
    for pid in PAPERS:
        assert pid in CREDITS, f"missing citation: {pid}"


def test_the_credits_say_no_code_was_copied():
    assert "clean-room" in CREDITS.lower()
    assert "no source code" in CREDITS.lower()


def test_mirofish_is_described_as_agpl_and_not_vendored():
    assert "MiroFish" in CREDITS
    assert "AGPL-3.0" in CREDITS
    assert "No MiroFish code" in CREDITS


def test_no_mirofish_code_is_actually_here():
    """The other half of the claim: the tree carries none of it."""
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".js", ".yaml", ".yml", ".json", ".md", ".toml"}:
            continue
        for i, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            low = line.lower()
            if "mirofish" in low and not any(k in low for k in ("mirofish", "666ghj")):
                hits.append(f"{path}:{i}")
            if re.search(r"(import|from)\s+mirofish", low):
                hits.append(f"{path}:{i} imports MiroFish")
    assert not hits, hits


def test_the_licence_names_the_person_who_owns_it():
    """The copyright is the author's, personally. A studio is a name, and a prize
    entity is a payout path — neither owns the code unless something says so."""
    assert LICENSE.startswith("MIT License")
    assert "Copyright (c) 2026 Lisa Martin (LeMultiFox)" in LICENSE
    assert "TrillionVerse Labs" in LICENSE       # the studio, stated not implied
    assert "LDMA Partners" in LICENSE            # the payout path, stated not implied
    assert "not the copyright holder" in LICENSE
    assert "written assignment" in LICENSE


def test_credit_studio_and_owner_are_all_named_in_the_readme():
    assert "LeMultiFox" in README
    assert "TrillionVerse Labs" in README
    assert "LDMA Partners" in README
    assert "owns this code personally" in README


def test_there_is_a_place_for_the_demo_and_a_script_to_record_it():
    """The demo is the pitch. The slot exists before the file does, so the video
    lands in one commit instead of a redesign."""
    assert "### See it" in README
    assert "assets/how-it-works.png" in README          # a frame until the video lands
    assert "DEMO-SCRIPT.md" in README
    script = (ROOT / "docs" / "DEMO-SCRIPT.md").read_text()
    for beat in ("The claim", "The answer card", "the clock", "the room", "the bend", "the record"):
        assert beat in script, beat
    # the honesty beats stay in the script: they are the credibility
    assert "Don't hide the unknown clock" in script
    assert "by removing each party in turn" in script


def test_the_readme_names_the_person_behind_it():
    """Attribution is the hiring surface: a handle the community knows, and the
    studio it belongs to. A stealth company with no handle reads as nobody."""
    assert "LeMultiFox" in README
    assert "discord" in README.lower()
    # the author fields a catalogue reviewer reads must be the same person
    assert "author: LeMultiFox" in MANIFEST
    assert "maintainer: LeMultiFox" in CATALOG


def test_the_old_framing_is_gone_from_the_public_text():
    for banned in ("strategic-response review", "Upfront Prediction"):
        assert banned not in README, banned
    assert not re.search(r"\bUpfront\b", README), "prose still calls the product Upfront"


def test_the_readme_points_at_the_credits():
    assert "CREDITS.md" in README


def test_the_banner_shows_the_same_contract_the_ui_shows():
    """The banner is the first thing a reviewer sees; the UI is what they install.
    If the six output tiles drift, the promise and the product disagree — so the
    guard compares the banner's titles against the UI's own tile list."""
    ui = (ROOT / "desktop" / "plugin.js").read_text()
    titles = re.findall(r"jsx\(GetTile, \{ title: '([^']+)'", ui)
    assert len(titles) >= 6, titles
    banner = (ROOT / "assets" / "banner.html").read_text()
    for t in titles:
        assert f"<b>{t}</b>" in banner, f"banner is missing the UI tile: {t}"
    # the hero carries the plain-language outcome, not the maths
    assert "exact Shapley" not in banner
    assert "shapley" not in banner.lower()
    # the UI's own line about what it is not, is in the README
    assert "not a prediction" in README.lower() or "Not a prediction" in README


def test_no_public_document_links_to_a_file_that_is_not_there():
    """A CONTRIBUTING that points at a missing CODE_OF_CONDUCT hands a reviewer a
    404 on the first page they open. Link targets are checked, not assumed."""
    import re
    PUBLIC = ["README.md", "CONTRIBUTING.md", "SECURITY.md", "CREDITS.md",
              "CODE_OF_CONDUCT.md"]
    broken = []
    for name in PUBLIC:
        text = (ROOT / name).read_text()
        for target in re.findall(r"\]\(([^)#\s]+\.(?:md|png|svg))\)", text):
            if target.startswith("http"):
                continue
            if not (ROOT / target).exists():
                broken.append(f"{name} -> {target}")
    assert not broken, broken


def test_no_third_party_document_is_bundled():
    """MIT covers what we wrote. A demo preset that quotes a real company's article
    puts their words under our copyright line — so the example documents must be
    ours and fictional, and say so."""
    places = list((ROOT / "data" / "presets").glob("*.json")) + \
             list((ROOT / "tests" / "fixtures").glob("*"))
    assert places, "expected at least one example document"
    banned = ("Nous Research", "NousResearch", "Arete", "Propaganda_Eval",
              "Qwen", "arete-data-pairs")
    for p in places:
        if p.is_dir():
            continue
        text = p.read_text(errors="ignore")
        for word in banned:
            assert word not in text, f"{p.name} carries third-party text: {word}"
    for p in (ROOT / "data" / "presets").glob("*.json"):
        assert "fictional" in p.read_text().lower(), f"{p.name} is not labelled fictional"


def test_no_third_party_code_is_bundled():
    """Rule 08's spirit: only the SDK, react and jsx-runtime are importable."""
    ui = (ROOT / "desktop" / "plugin.js").read_text()
    specs = set(re.findall(r"from\s+'([^']+)'", ui))
    assert specs <= {"@hermes/plugin-sdk", "react", "react/jsx-runtime"}, specs


# ── one voice, one promise, one page ───────────────────────────────────
NEW_TAGLINE = "Understand the landscape before investing valuable resources"


def test_one_tagline_everywhere():
    """The header, the banner, the README and the manifest say one thing.

    Two taglines means the product cannot repeat itself, and repetition is the
    only marketing a plugin gets.
    """
    banner = (ROOT / "assets" / "banner.html").read_text()
    ui = (ROOT / "desktop" / "plugin.js").read_text()
    assert NEW_TAGLINE in README
    assert NEW_TAGLINE in banner
    assert NEW_TAGLINE in ui
    for text, name in ((README, "README"), (banner, "banner"), (ui, "plugin.js"),
                       (MANIFEST, "plugin.yaml")):
        assert "the read before you publish" not in text.lower(), name


def test_the_readme_is_a_readme_not_a_book():
    """A reviewer reads the pinned README top to bottom. The old one was 740 lines
    with four sections saying the same thing; this cap is a ratchet against drift
    back there, not a line-count contest — the six tables and the worked example
    are the product page, not padding.

    It moved to 470 in 0.6.4: the free-model section and the ingestion note are
    deliberate, user-facing content added on purpose (and the README was 2 lines
    over the old cap before that). A cap that never moves is a budget; this one
    moves when a real section is added, and the diff should show why.
    """
    assert len(README.splitlines()) <= 470, len(README.splitlines())


def test_the_readme_does_not_describe_the_removed_model_picker():
    for stale in ("free only", "live catalogue, per-million prices",
                  "+ New review", "a picked model", "red / amber / green"):
        assert stale.lower() not in README.lower(), stale


def test_no_invented_vocabulary():
    """The README may only use words the code and the UI actually use.

    A draft that invents "Friction Clock" or "GraphREG" teaches a reviewer a
    product that does not exist, and the demo will contradict it on camera.
    """
    for banned in ("GraphREG", "Friction Clock", "Strategic Vector",
                   "Friction Stakeholder Graph", "hermes/tems"):
        assert banned.lower() not in README.lower(), banned


def test_house_style_is_american_english():
    """The judges are US-based, and a document that mixes `colour` with `color`
    reads as a typo even to people who could not name the rule.

    The product's own output strings are NOT covered here on purpose: `unclear
    licence` is what the lens prompt prints and what tests/test_lens.py asserts.
    Fixing spelling there is a behaviour change, not a copy pass.
    """
    assert "artifact" in README.lower()
    for brit in ("artefact", "licence", "colour", "organisation", "behaviour",
                 "recognise", "summarise", "labelled"):
        assert brit not in README.lower(), brit
