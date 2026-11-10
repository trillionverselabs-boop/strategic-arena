"""Leverage must add up, or it is just another number on a page.

These tests hold the three properties that make the ledger trustworthy: it
decomposes the heat exactly, it is order-independent (that is what Shapley
buys us), and it never silently invents a party who was not in the room.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from upfront import leverage  # noqa: E402


def room(*pairs):
    return [{"name": n, "stance": s, "capacity": c} for n, s, c in pairs]


# the Arete-shaped room used in the design mockup
ARETE = room(
    ("Federal procurement", -0.75, 0.9),
    ("Alibaba / Qwen", -0.35, 0.65),
    ("Frontier labs", -0.55, 0.4),
    ("Enterprise security", -0.15, 0.55),
    ("Open-weight community", 0.85, 0.15),
    ("Our users", 0.60, 0.10),
)


def test_the_ledger_decomposes_the_heat_exactly():
    """sum(party values) == total - baseline, to the last decimal."""
    led = leverage.ledger(ARETE)
    assert led["available"]
    got = round(sum(p["value"] for p in led["parties"]), 1)
    assert got == pytest.approx(led["attributable"], abs=0.11)
    assert led["total"] == pytest.approx(
        leverage.friction([p["stance"] for p in ARETE]), abs=0.05)


def test_a_neutral_room_has_no_attributable_heat():
    """Six undecided parties still score 35 — that floor is not anyone's."""
    led = leverage.ledger(room(*[(f"p{i}", 0.0, 0.5) for i in range(6)]))
    assert led["baseline"] == 35.0
    assert led["attributable"] == 0.0
    assert all(abs(p["value"]) < 0.05 for p in led["parties"])


def test_shapley_is_order_independent():
    """Same parties in any order → same numbers. The whole point of Shapley."""
    a = [p["value"] for p in leverage.ledger(ARETE)["parties"]]
    shuffled = ARETE[::-1]
    b = [p["value"] for p in leverage.ledger(shuffled)["parties"]]
    assert sorted(x for x in a) == pytest.approx(sorted(x for x in b), abs=0.11)


def test_the_hostile_party_outranks_the_mild_one():
    """Legal-shaped (-0.75, capacity .9) must be worth more than a mild -0.15."""
    led = leverage.ledger(ARETE)
    by = {p["name"]: p["value"] for p in led["parties"]}
    assert by["Federal procurement"] > by["Enterprise security"]
    assert by["Federal procurement"] > 0


def test_a_supporter_cools_the_room():
    """A party who is for it takes heat out. Shown as cooling, never a bar."""
    led = leverage.ledger(ARETE)
    for name in ("Open-weight community", "Our users"):
        row = next(p for p in led["parties"] if p["name"] == name)
        assert row["cools"] is True
        assert row["value"] < 0


def test_counterfactuals_move_the_call_and_keep_the_room_size():
    """Satisfying a party is a real second reading, not a guess."""
    led = leverage.ledger(ARETE)
    assert led["total"] > led["baseline"]
    for cf in led["counterfactuals"]:
        assert cf["friction"] <= led["total"] + 0.01, cf
        assert cf["band"]["key"] in ("quiet", "contested", "open_war")


def test_satisfying_the_blocker_removes_the_veto():
    led = leverage.ledger(ARETE)
    blocker = next(p for p in led["parties"] if p["veto"])
    cf = next(c for c in led["counterfactuals"] if c["label"] == blocker["name"])
    assert cf["friction"] < led["total"]
    assert cf["veto_left"] != blocker["name"]


def test_a_coalition_is_named_by_what_it_actually_does():
    """Two kinds, both computed: it costs more heat together, or it is the only
    pairing that clears the veto. This heat function is additive in stances, so
    the second kind is the usual one — and inventing the first would be lying."""
    led = leverage.ledger(ARETE)
    assert led["pairs"], "the Arete room has a federal+licence pair"
    for pair in led["pairs"]:
        assert pair["kind"] in ("heat", "veto")
        if pair["kind"] == "heat":
            assert pair["interaction"] >= 0.5
            assert pair["together"] > pair["apart"]
        else:
            assert pair["interaction"] == 0.0
            assert "veto" in pair["line"]


def test_the_same_scenario_is_not_printed_twice():
    labels = [c["label"] for c in leverage.ledger(ARETE)["counterfactuals"]]
    assert len(labels) == len(set(labels))


def test_an_empty_room_says_so_instead_of_zero():
    led = leverage.ledger([])
    assert led["available"] is False
    assert "why" in led


def test_parties_without_a_stance_are_skipped_not_priced():
    led = leverage.ledger([{"name": "Ghost"}, dict(ARETE[0])])
    assert [p["name"] for p in led["parties"]] == ["Federal procurement"]


def test_the_same_run_reads_the_same_twice():
    """A ledger that changes when you reopen it is not a ledger."""
    a, b = leverage.ledger(ARETE), leverage.ledger(ARETE)
    assert a == b


def test_the_method_line_reports_the_real_number_of_subsets():
    led = leverage.ledger(ARETE)
    assert led["subsets"] == 64      # 2^6 parties
    assert "Shapley" in led["method"]
