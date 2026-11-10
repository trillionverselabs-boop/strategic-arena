"""The lens: what was handed in decides who could possibly react.

A README is judged by maintainers deciding whether to merge and security reviewers
deciding whether the install is allowed. A tweet is judged by the people who quote
it. Same engine, different room — so the extraction question is set by the medium,
and the prompt must actually carry that.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from upfront import ingestion  # noqa: E402
from upfront.models import Document, DocumentType  # noqa: E402


def docs(text="Ship the thing."):
    return [Document(type=DocumentType.DECISION, content=text)]


class Recorder:
    """Captures the prompt, answers with a fixed extraction."""

    def __init__(self, payload=None):
        self.prompt = ""
        self.payload = payload or {"personas": [], "relationships": []}

    def complete(self, prompt, **kw):
        self.prompt = prompt
        return self.payload


@pytest.mark.parametrize("url,kind", [
    ("https://github.com/owner/repo", "repo"),
    ("https://gitlab.com/owner/repo/-/blob/main/README.md", "repo"),
    ("https://x.com/nousresearch/status/1", "tweet"),
    ("https://arxiv.org/abs/2402.16130", "whitepaper"),
    ("https://example.com/whitepaper.pdf", "whitepaper"),
    ("https://www.prnewswire.com/news/x", "press"),
    ("https://example.com/blog/why-we-built-this", "post"),
    ("https://medium.com/@x/a-post", "post"),
])
def test_the_link_names_the_medium(url, kind):
    assert ingestion.detect_kind([url], "") == kind


def test_an_unknown_link_falls_back_to_the_honest_default():
    """Never guessed into a corner: an unrecognised input is a decision document,
    which is the widest room, not a confident wrong answer."""
    assert ingestion.detect_kind(["https://example.com"], "") == "decision"
    assert ingestion.detect_kind([], "Some notes about a plan") == "decision"


def test_a_readme_in_the_text_is_recognised_without_a_link():
    assert ingestion.detect_kind([], "# Installation\n\npip install thing") == "repo"


@pytest.mark.parametrize("kind,phrase", [
    ("repo", "the maintainers who decide whether this merges"),
    ("tweet", "the reply-guy who will find the weakest clause"),
    ("whitepaper", "the technical reviewer who will check the method"),
    ("case_study", "the customer named in it"),
    ("press", "the journalist deciding whether it is a story"),
    ("post", "the reader who will quote one line back"),
])
def test_each_medium_brings_its_own_room(kind, phrase):
    rec = Recorder()
    ingestion.extract_personas(docs(), rec, kind=kind)
    assert phrase in rec.prompt


def test_a_repo_prompt_asks_about_what_the_readme_promises():
    rec = Recorder()
    ingestion.extract_personas(docs(), rec, kind="repo")
    assert "install steps, licence, benchmarks" in rec.prompt
    assert "whether this merges" in rec.prompt


def test_two_or_three_reasons_are_kept_and_duplicates_dropped():
    rec = Recorder({"personas": [{
        "name": "Security review", "role": "blocker", "stance": -0.6, "capacity": 0.8,
        "reasons": ["no pinned deps [decision ¶1]", "no pinned deps [decision ¶1]",
                    "unclear licence [decision ¶2]", "no tests [evidence ¶1]"],
    }], "relationships": []})
    personas, _ = ingestion.extract_personas(docs(), rec, kind="repo")
    assert len(personas[0].reasons) == 3
    assert personas[0].reasons[0] == "no pinned deps [decision ¶1]"
    assert "unclear licence" in personas[0].reasons[1]


def test_a_single_reason_still_works():
    """An older extraction shape (one `reason`) must not lose its evidence."""
    rec = Recorder({"personas": [{
        "name": "Legal", "role": "blocker", "stance": -0.5,
        "reason": "needs the licences cleared [evidence ¶2]",
    }], "relationships": []})
    personas, _ = ingestion.extract_personas(docs(), rec)
    assert personas[0].reasons == ["needs the licences cleared [evidence ¶2]"]


def test_the_prompt_asks_for_a_cited_reason_per_line():
    """Depth is asked for, not assumed: two independent reasons beat one long one."""
    rec = Recorder()
    ingestion.extract_personas(docs(), rec, kind="post")
    assert "2 to 3 sentences" in rec.prompt
    assert "EACH carrying its own source marker" in rec.prompt
