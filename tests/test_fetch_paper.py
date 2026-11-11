"""Fetching a paper: three URLs, two of them text.

arXiv serves the same paper at /abs/, /html/ and /pdf/. Only the first two are
text. Decoding PDF bytes as UTF-8 produces a page of compressed-stream noise that
is *full of word-shaped tokens*, so it passes the prose gate and the model gets
binary as its "paper" — worse than failing, because the run still looks healthy.
These tests pin the rewrite and the refusal.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from upfront import fetch  # noqa: E402


def test_the_pdf_link_is_rewritten_to_a_text_version(monkeypatch):
    seen = []

    def fake_get_text(url):
        seen.append(url)
        return "Paper body text " * 20

    monkeypatch.setattr(fetch, "_get_text", fake_get_text)
    doc = fetch.fetch_url("https://arxiv.org/pdf/2611.14051")

    assert doc is not None
    assert seen[0] == "https://arxiv.org/html/2611.14051"
    assert doc.source == "https://arxiv.org/pdf/2611.14051", "provenance keeps what was pasted"


def test_the_html_rendering_is_preferred_over_the_abstract(monkeypatch):
    calls = []

    def fake_get_text(url):
        calls.append(url)
        return None if "/html/" in url else "Abstract only"

    monkeypatch.setattr(fetch, "_get_text", fake_get_text)
    doc = fetch.fetch_url("https://arxiv.org/abs/2611.14051")
    assert doc.content == "Abstract only"
    assert calls == ["https://arxiv.org/html/2611.14051",
                     "https://arxiv.org/abs/2611.14051"]


def test_a_pdf_never_reaches_the_model_as_text():
    """Magic bytes and content-type are both checked: a page served as
    application/pdf but decoded as a string is the failure this prevents."""
    assert fetch._extract_text(b"%PDF-1.7 stream xWn6...", "application/pdf") is None
    assert fetch._extract_text(b"%PDF-1.7 stream xWn6...", "") is None
    assert fetch._extract_text(b"ordinary prose " * 30, "text/plain") is not None


def test_a_link_that_cannot_be_read_is_recorded_not_dropped(monkeypatch):
    monkeypatch.setattr(fetch, "_get_text", lambda url: None)
    docs = fetch.fetch_urls(["https://example.com/report.pdf"])
    assert docs == []
    assert fetch.LAST_SKIPPED and fetch.LAST_SKIPPED[0][0] == "https://example.com/report.pdf"
    assert "no readable text" in fetch.LAST_SKIPPED[0][1]


def test_the_run_reports_what_it_skipped(monkeypatch):
    """Reviewing two documents when three were handed in is a silent downgrade."""
    from upfront import engine
    from upfront.models import Document, DocumentType, Scenario

    class Stub:
        model = "fake"
        temperature = 0.6

        def complete(self, prompt):
            if "stakeholder landscape" in prompt or "You are extracting" in prompt:
                return ('{"personas":[{"name":"Eng","role":"blocker","stance":-0.5,'
                        '"reasons":["no [context 1]"]}],"relationships":[]}')
            if "Decide your move" in prompt:
                return '{"stance_delta":0.0,"action":"waits","text":""}'
            return '{"claims":[]}'

    def boom(urls):
        fetch.LAST_SKIPPED[:] = [("https://example.com/x.pdf", "no readable text")]
        return []

    monkeypatch.setattr(engine, "fetch_urls", boom)
    res = engine.run_scenario(
        Scenario(title="t", window="30m", urls=["https://example.com/x.pdf"],
                 documents=[Document(type=DocumentType.DECISION, content="ship it")]),
        Stub())
    assert any(line.startswith("SKIPPED https://example.com/x.pdf") for line in res.provenance)
