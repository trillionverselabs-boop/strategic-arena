from upfront.models import Persona
from upfront.scoring import find_blocker


def test_no_blocker_when_everyone_is_positive():
    assert find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=0.8)]) is None


def test_blocker_when_someone_opposes():
    b = find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=-0.7)])
    assert b is not None and b.name == "b"
