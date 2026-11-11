import pytest

from upfront import engine
from upfront.models import Document, DocumentType, Scenario
from fakes import Boom, EmptyExtraction


def _scenario():
    return Scenario(title="t", documents=[Document(type=DocumentType.DECISION, content="Ship it")])


def test_model_failure_raises():
    with pytest.raises(engine.SimulationError, match="model call failed"):
        engine.run_scenario(_scenario(), Boom())


def test_zero_personas_raises():
    with pytest.raises(engine.SimulationError, match="found no stakeholders"):
        engine.run_scenario(_scenario(), EmptyExtraction())


def test_no_documents_raises():
    with pytest.raises(engine.SimulationError, match="at least one document"):
        engine.run_scenario(Scenario(title="t"), Boom())
