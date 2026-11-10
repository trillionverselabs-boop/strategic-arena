from upfront.models import Persona
from upfront.scoring import find_blocker


def test_no_blocker_when_everyone_is_positive():
    assert find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=0.8)]) is None


def test_blocker_when_someone_opposes():
    b = find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=-0.7)])
    assert b is not None and b.name == "b"


def test_blocker_is_the_effective_objector_not_the_angriest():
    """A -1.0 with no lever cannot stop anything; a -0.6 who owns the budget can."""
    personas = [
        Persona(name="Free tier users", stance=-1.0, capacity=0.0),
        Persona(name="Finance", stance=-0.6, capacity=0.9),
    ]
    assert find_blocker(personas).name == "Finance"


def test_unassessed_capacity_gets_the_benefit_of_the_doubt():
    """Unknown power is not zero power — the angriest still wins when nobody's power is known."""
    personas = [
        Persona(name="Loud forum", stance=-0.9, capacity=0.2),
        Persona(name="Unknown party", stance=-0.8),
    ]
    assert find_blocker(personas).name == "Unknown party"


def test_possessive_survives_names_ending_in_s():
    from upfront.models import SimulationResult
    from upfront.scoring import build_counter_moves

    res = SimulationResult(title="t", goal="adoption", rounds=1, personas=[])
    moves = build_counter_moves(Persona(name="Enterprise resellers", stance=-0.8), res)
    assert "Enterprise resellers' core objection" in moves[0]


def test_a_camp_of_powerless_complainers_is_not_a_fight():
    """Two camps where only one has a lever is a contest with winnable ground, not a brawl."""
    from upfront.models import SimulationResult
    from upfront.scoring import sea_state

    res = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=44.5,
        personas=[Persona(name="Finance", stance=-0.5, capacity=0.7),
                  Persona(name="Resellers", stance=-0.4, capacity=0.3)],
        blocker=Persona(name="Finance", stance=-0.5, capacity=0.7),
        camps=[{"name": "F", "members": ["Finance"], "lean": "against"},
               {"name": "R", "members": ["Resellers"], "lean": "against"}],
    )
    assert sea_state(res)["state"] == "purple"


def test_unknown_camp_members_still_count_as_a_fight():
    """Never guess that an unreadable fight is harmless."""
    from upfront.models import SimulationResult
    from upfront.scoring import sea_state

    res = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=40,
        personas=[Persona(name="Finance", stance=-0.5, capacity=0.7)],
        camps=[{"name": "F", "members": ["Finance"], "lean": "against"},
               {"name": "R", "members": ["Someone else"], "lean": "against"}],
    )
    assert sea_state(res)["state"] == "red"
