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


# ── public text ────────────────────────────────────────────────────────
def test_the_readme_is_the_product_not_the_old_one():
    assert README.startswith("# Strategic Arena\n")
    assert "Read what it means before it reads you." in README
    for banned in ("rehears", "Upfront Prediction"):
        assert banned.lower() not in README.lower(), banned


def test_the_manifest_is_brand_aligned():
    assert "label: Strategic Arena" in MANIFEST
    assert "Upfront Prediction" not in MANIFEST
    assert "rehearsal" not in MANIFEST.lower()
    # the id is deliberately stable: renaming it breaks installs and the pin
    assert MANIFEST.startswith("name: upfront\n")


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
    for beat in ("The claim", "The price", "The record", "The lens"):
        assert beat in script, beat
    assert "Don't hide the `n`" in script


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


def test_no_third_party_code_is_bundled():
    """Rule 08's spirit: only the SDK, react and jsx-runtime are importable."""
    ui = (ROOT / "desktop" / "plugin.js").read_text()
    specs = set(re.findall(r"from\s+'([^']+)'", ui))
    assert specs <= {"@hermes/plugin-sdk", "react", "react/jsx-runtime"}, specs
