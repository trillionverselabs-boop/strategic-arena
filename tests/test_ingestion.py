from upfront import ingestion
from upfront.models import Document, DocumentType
from tests.fakes import Boom, EmptyExtraction


def _docs():
    return [Document(type=DocumentType.DECISION, content="Ship it")]


def test_transport_failure_is_none():
    assert ingestion.extract_personas(_docs(), Boom()) is None


def test_genuinely_empty_is_not_none():
    assert ingestion.extract_personas(_docs(), EmptyExtraction()) == ([], [])
