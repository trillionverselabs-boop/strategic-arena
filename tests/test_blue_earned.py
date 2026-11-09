"""Blue must be earned.

The Arete run printed "Blue ocean" for a document that named no opponent at all:
`sea_state` read "nobody in the room objected" as "uncontested market". Those are
different claims, and only the second one is worth printing.

Rule: blue is only printable when the run names at least one party who *could*
contest the move and the report can say why they don't. No such party, or no
assessment of anyone's capacity to contest → "insufficient", never blue.
"""
from upfront.models import Persona, SimulationResult
from upfront.scoring import sea_state


def _res(friction=20.0, personas=None, blocker_stance=None, camps=None):
    return SimulationResult(
        title="t", goal="adoption", rounds=8, friction=friction,
        personas=personas or [],
        blocker=Persona(name="Eng", stance=blocker_stance) if blocker_stance is not None else None,
        camps=camps or [],
    )


def test_no_named_party_cannot_be_blue():
    """An empty room is not open water."""
    s = sea_state(_res(personas=[]))
    assert s["state"] == "insufficient"
    assert s["label"] == "Insufficient input"
    assert "nobody" in s["why"].lower() or "no party" in s["why"].lower()


def test_aligned_party_with_capacity_earns_blue():
    """Someone could have stopped this and chose not to — that is open water."""
    s = sea_state(_res(personas=[Persona(name="Procurement", stance=0.6, capacity=0.8)]))
    assert s["state"] == "blue"
    assert "Procurement" in s["why"]


def test_powerless_supporter_does_not_earn_blue():
    """A fan who could not stop anything is not evidence of an open field."""
    s = sea_state(_res(personas=[Persona(name="Enthusiast", stance=0.9, capacity=0.0)]))
    assert s["state"] == "insufficient"


def test_unassessed_capacity_does_not_earn_blue():
    """Unknown capacity is not the same as no threat."""
    s = sea_state(_res(personas=[Persona(name="Analyst", stance=0.5)]))
    assert s["state"] == "insufficient"
    assert "capacity" in s["why"].lower()


def test_capacity_never_rescues_a_red_read():
    """The gate only restrains blue; opponents still dominate."""
    s = sea_state(_res(friction=80.0, personas=[Persona(name="Union", stance=-0.9, capacity=0.9)],
                       blocker_stance=-0.9))
    assert s["state"] == "red"


def test_blue_names_the_reason_not_just_the_colour():
    s = sea_state(_res(personas=[Persona(name="Regulator", stance=0.2, capacity=0.7)]))
    assert s["state"] == "blue"
    assert s["why"] and s["why"] != "no blocking camp"


def test_insufficient_is_not_on_the_red_purple_blue_axis():
    """The axis is a competition scale; 'insufficient' is the absence of a read."""
    s = sea_state(_res(personas=[]))
    assert s["state"] not in s["order"]
