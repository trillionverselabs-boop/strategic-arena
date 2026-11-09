# End-to-end smoke test: Arete preset -> full sim -> graph + score + persisted run.
# Runs against the REAL engine with a FAKE llm (no tokens), so we can iterate fast.
# This is the 30-minute proof that the whole pipeline works before touching the UI.

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from upfront.engine import run_scenario
from upfront.models import Scenario
from upfront.reporting import list_runs, load_run


class FakeLLM:
    """Deterministic stub: extraction returns 3 personas; act returns canned moves."""
    def __init__(self):
        self.calls = 0

    def complete(self, prompt):
        self.calls += 1
        # extraction prompt
        if "stakeholder landscape" in prompt.lower() or "extracing" in prompt.lower() or "You are extracting" in prompt:
            return json.dumps({
                "personas": [
                    {"name": "Enterprise IT", "role": "blocker", "stance": -0.7,
                     "reason": "Cannot route inference through external API for compliance [evidence ¶1]",
                     "source": "evidence"},
                    {"name": "The Community", "role": "champion", "stance": 0.8,
                     "reason": "Open-weight downloads tripled; wants training data [decision]",
                     "source": "decision"},
                    {"name": "Regulators", "role": "regulator", "stance": -0.3,
                     "reason": "Wants to see the eval suite before blessing release [evidence ¶1]",
                     "source": "evidence"},
                ],
                "relationships": [["Enterprise IT", "The Community", "opposes"]],
            })
        # agent act prompt
        if "Decide your move" in prompt:
            return json.dumps({"stance_delta": -0.05, "action": "blocks",
                               "text": "We still cannot use an external API here."})
        # reflection
        return "Insight: Community pressure is strong but enterprise compliance is the hard gate."


def main():
    preset = json.loads(Path(__file__).resolve().parent.parent.joinpath("data/presets/arete.json").read_text())
    scenario = Scenario(**preset)
    llm = FakeLLM()

    result = run_scenario(scenario, llm)

    print(f"run_id        : {result.run_id}")
    print(f"title         : {result.title}")
    print(f"friction      : {result.friction:.1f} ±{result.uncertainty:.1f} ({result.confidence})")
    print(f"blocker       : {result.blocker.name if result.blocker else None} ({result.blocker.stance if result.blocker else ''})")
    print(f"personas      : {[(p.name, round(p.stance,2)) for p in result.personas]}")
    print(f"events        : {len(result.events)}")
    print(f"counter-moves : {result.counter_moves}")
    print(f"provenance    : {result.provenance}")
    print(f"llm calls     : {llm.calls}")
    print()
    print("=== HISTORY (look-back / verification) ===")
    runs = list_runs(5)
    for r in runs:
        print(f"  {r['run_id']}  {r['title']}  friction={r.get('friction')}  blocker={r.get('blocker')}")
    print()
    print("=== SAVED RUN GRAPH ===")
    saved = load_run(result.run_id)
    print(json.dumps(saved.get("graph"), indent=1)[:800])
    print()
    print("=== REPORT (first 600 chars) ===")
    print(saved.get("report", "")[:600])

    # assertions — the contract
    assert result.friction > 0, "friction should be > 0"
    assert result.blocker is not None, "should identify a blocker"
    assert result.confidence in ("low", "medium", "high")
    assert len(list_runs()) >= 1, "run must be persisted to history"
    assert saved.get("graph", {}).get("nodes"), "graph must be saved"
    assert "Friction" in saved.get("report", ""), "report must have friction line"
    print("\n✓ ALL ASSERTIONS PASSED — pipeline works end-to-end.")


if __name__ == "__main__":
    main()
