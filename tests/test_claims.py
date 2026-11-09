from upfront.claims import build_claims
from upfront.models import Persona, SimulationResult


def test_three_claims_with_a_blocker_and_a_camp():
    res = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=50.0, uncertainty=10.0,
        personas=[Persona(name="Eng", stance=-0.8, reasons=["compliance"])],
        blocker=Persona(name="Eng", stance=-0.8, reasons=["compliance"]),
        camps=[{"name": "Eng + 1", "members": ["Eng", "Ops"], "lean": "against"}],
    )
    c = build_claims(res)
    kinds = {x["kind"] for x in c}
    assert kinds == {"veto_player", "friction_band", "coalition"}
    assert c[1]["expected"] == {"lo": 40.0, "hi": 60.0, "point": 50.0}
    assert all(x["id"] for x in c)


def test_no_blocker_case_is_still_scorable():
    res = SimulationResult(title="t", goal="adoption", rounds=8, friction=20.0,
                           uncertainty=5.0, personas=[Persona(name="A", stance=0.5)])
    c = build_claims(res)
    assert c[0]["kind"] == "no_veto_player"
    assert len(c) == 2
