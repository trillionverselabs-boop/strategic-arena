# Real end-to-end run: Arete preset with the LIVE model via Hermes' PluginLlm bridge.
# This is exactly how the gateway will call it (ctx.llm), so it proves the real path.

import json
import sys
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN.parent))   # exposes the `upfront` package
sys.path.insert(0, str(PLUGIN))

from upfront.engine import run_scenario
from upfront.llm_adapter import LlmAdapter
from upfront.models import Scenario
from upfront.reporting import list_runs, load_run


def make_real_llm():
    from agent.plugin_llm import PluginLlm
    return LlmAdapter(PluginLlm(plugin_id="upfront"))


def main():
    preset = json.loads((PLUGIN / "data/presets/arete-real.json").read_text())
    scenario = Scenario(**preset)
    # 48h = 20 rounds; that's ~67 live calls. For a snappier proof use 24h (16).
    scenario.window = scenario.window  # keep preset window
    llm = make_real_llm()

    start = time.time()
    def on_round(snap):
        print(f"  round {snap.round:2d}  stances: " +
              ", ".join(f"{k}={v:+.2f}" for k, v in snap.stances.items()), flush=True)

    print(f"Running '{scenario.title}'  goal={scenario.goal.value}  rounds={scenario.rounds}")
    print("Model: your active model (reflection/beam-1.0 via Nous)\n")

    # run with progress
    from upfront import engine
    result = engine.run_scenario_progress(scenario, llm, on_round=on_round)
    elapsed = time.time() - start

    print(f"\n=== RESULT ({elapsed:.0f}s) ===")
    print(f"run_id        : {result.run_id}")
    print(f"friction      : {result.friction:.1f} ±{result.uncertainty:.1f} ({result.confidence})")
    print(f"blocker       : {result.blocker.name} ({result.blocker.stance:+.2f})" if result.blocker else "blocker       : none")
    print(f"personas      : {[(p.name, round(p.stance,2)) for p in result.personas]}")
    print(f"events        : {len(result.events)}")
    print(f"counter-moves :")
    for m in result.counter_moves:
        print(f"  - {m}")
    print(f"provenance    :")
    for p in result.provenance:
        print(f"  - {p}")

    saved = load_run(result.run_id)
    print(f"\nreport saved  : {bool(saved.get('report'))}   graph nodes: {len(saved.get('graph',{}).get('nodes',[]))}")
    print("\n=== FULL REPORT ===")
    print(saved.get("report", ""))

    print("\n=== HISTORY (verify later) ===")
    for r in list_runs(5):
        print(f"  {r['run_id']}  {r['title'][:40]:40s} friction={r.get('friction')} blocker={r.get('blocker')}")

    assert result.blocker is not None
    assert saved.get("graph", {}).get("nodes")
    print("\n✓ REAL RUN COMPLETE — graph + blocker + persisted history all produced by the live model.")


if __name__ == "__main__":
    main()
