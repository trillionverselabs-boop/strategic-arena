from upfront import ingestion
from upfront.models import Document, DocumentType


def test_a_huge_document_is_windowed_before_it_reaches_the_model():
    """The field failure: an arXiv HTML page is ~50k characters, and the persona
    call shipped all of it. Two prompts that size per run, on a free model, is
    how a paper run dies before the room exists."""
    text = "Abstract\n" + ("sentence about the method. " * 5000) + "\nLIMITATIONS: none stated."
    out = ingestion.excerpt(text)
    assert len(out) <= ingestion.PROMPT_BUDGET + 200
    assert out.startswith("Abstract")
    assert "LIMITATIONS" in out                      # the tail is where the limits live
    assert "omitted from the middle" in out


def test_the_arxiv_table_of_contents_is_dropped():
    """arXiv's HTML puts a TOC, a theme switcher and a PDF link before the
    Abstract — and the TOC's own first line is the word "Abstract", so a naive
    first-match cut keeps the entire contents list. The real heading is the last
    standalone "Abstract" near the top."""
    page = ("Skip to main content\n\nContents\nAbstract\n1 Introduction\n"
            "2 Methodology\n3 Experiment\n" + "x" * 60 +
            "\n\nAbstract\nThe real abstract sentence about KV cache.\n\n1 Introduction\nbody")
    out = ingestion.excerpt(page, budget=10_000).lstrip()
    assert out.startswith("Abstract\nThe real abstract sentence"), out[:80]


def test_the_bibliography_is_cut_so_the_tail_is_the_conclusion():
    """The tail of the window is where a replication clock comes from; on an arXiv
    page that tail used to be the reference list."""
    body = "Abstract\nclaim.\n\n6 Conclusion\nWe did not release the data.\n" + "y" * 6_000
    page = body + "\nReferences\n[1] Someone et al. 2018.\n" + "z" * 6_000
    out = ingestion.excerpt(page, budget=4_000)
    assert "We did not release the data" in out
    assert "Someone et al. 2018" not in out


def test_the_budget_is_per_call_not_per_document():
    """One paper and five short notes must cost the same prompt."""
    docs = [Document(type=DocumentType.CONTEXT, content="Abstract\n" + "word " * 30_000)
            for _ in range(2)]
    block = ingestion._docs_block(docs)
    assert len(block) <= ingestion.PROMPT_BUDGET + 600
from fakes import Boom, EmptyExtraction


def _docs():
    return [Document(type=DocumentType.DECISION, content="Ship it")]


def test_transport_failure_is_none():
    assert ingestion.extract_personas(_docs(), Boom()) is None


def test_genuinely_empty_is_not_none():
    assert ingestion.extract_personas(_docs(), EmptyExtraction()) == ([], [])
