from upfront.agents import StakeholderAgent
from upfront.models import Persona
from fakes import Boom


def test_dead_model_holds_stance_and_counts():
    a = StakeholderAgent(Persona(name="Eng", stance=0.2))
    move = a.act("t", {}, 1, Boom())
    assert move["stance_delta"] == 0.0
    assert a.p.stance == 0.2
    assert a.failures == 1
