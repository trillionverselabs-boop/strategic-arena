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


def test_coalition_claim_does_not_repeat_the_lead_name_and_survives_a_nameless_camp():
    res = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=50.0, uncertainty=10.0,
        personas=[Persona(name="Enterprise IT", stance=-0.7)],
        blocker=Persona(name="Enterprise IT", stance=-0.7),
        camps=[{"name": "Enterprise IT", "members": ["Enterprise IT"], "lean": "against"}],
    )
    claim = [c for c in build_claims(res) if c["kind"] == "coalition"][0]["claim"]
    assert "Enterprise IT (Enterprise IT)" not in claim
    assert "Enterprise IT" in claim

    empty = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=50.0, uncertainty=10.0,
        personas=[Persona(name="Eng", stance=-0.8)],
        blocker=Persona(name="Eng", stance=-0.8),
        camps=[{"name": "?", "members": [], "lean": "against"}],
    )
    kinds = {c["kind"] for c in build_claims(empty)}
    assert "coalition" not in kinds, "a camp with no members must not become a claim"


def test_no_blocker_case_is_still_scorable():
    res = SimulationResult(title="t", goal="adoption", rounds=8, friction=20.0,
                           uncertainty=5.0, personas=[Persona(name="A", stance=0.5)])
    c = build_claims(res)
    assert c[0]["kind"] == "no_veto_player"
    assert len(c) == 2
