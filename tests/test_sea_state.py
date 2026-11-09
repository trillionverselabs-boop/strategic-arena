from upfront.models import Persona, SimulationResult
from upfront.scoring import sea_state


def _res(friction, blocker_stance=None, camps=None):
    return SimulationResult(
        title="t", goal="adoption", rounds=8, friction=friction, personas=[],
        blocker=Persona(name="Eng", stance=blocker_stance) if blocker_stance is not None else None,
        camps=camps or [],
    )


def test_blue_when_quiet():
    s = sea_state(_res(20, -0.1))
    assert s["state"] == "blue"
    assert s["level"] == "low"


def test_red_on_hard_veto():
    s = sea_state(_res(50, -0.8))
    assert s["state"] == "red"
    assert s["level"] == "high"


def test_red_on_two_blocking_camps():
    camps = [{"name": "A", "members": ["a"], "lean": "against"},
             {"name": "B", "members": ["b"], "lean": "against"}]
    assert sea_state(_res(40, None, camps))["state"] == "red"


def test_purple_in_the_middle():
    s = sea_state(_res(48, -0.4, [{"name": "A", "members": ["a"], "lean": "against"}]))
    assert s["state"] == "purple"
    assert s["level"] == "medium"


def test_axis_order_is_red_then_blue():
    assert sea_state(_res(20, -0.1))["order"] == ["red", "purple", "blue"]
