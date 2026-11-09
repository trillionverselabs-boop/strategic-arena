# Recommendation — the "so what do I actually do" layer.
# Both MiroFish and the Anthropic Founder's Playbook end at an actionable
# recommendation grounded in the analysis. This does the same, but honestly:
# every line is derived from the sim's own output (blocker, camps, friction,
# provenance), framed as guidance — never as a guaranteed outcome, and never
# by inventing facts the input didn't contain.

from __future__ import annotations

from typing import List

from .models import SimulationResult


def build_recommendation(result: SimulationResult) -> str:
    """Plain-language recommendation, derived only from this run's output."""
    b = result.blocker
    lines: List[str] = []

    if b is None or b.stance >= -0.3:
        lines.append(
            "No stakeholder is strongly against this in the simulation, so there is no "
            "blocker to convert before you proceed. Use the graph to see who is merely "
            "undecided, and spend your pre-launch effort checking them rather than defending "
            "against a fight that isn't showing up."
        )
        undecided = [p.name for p in result.personas if -0.3 < p.stance < 0.3]
        if undecided:
            lines.append(f"Undecided, worth winning: {', '.join(undecided)}.")
    else:
        lines.append(
            f"{b.name} is the blocker (stance {b.stance:+.2f}). Every other move in this "
            f"plan is secondary to converting or neutralizing them."
        )
        if b.reasons and b.reasons[0]:
            lines.append(f"Their load-bearing reason, from your own input: {b.reasons[0]}")
        # camps tell you whether the blocker is alone or leads a coalition
        for camp in result.camps:
            if b.name in camp.get("members", []) and len(camp["members"]) > 1:
                others = [m for m in camp["members"] if m != b.name]
                lines.append(
                    f"{b.name} is not alone — they lead a camp with {', '.join(others)}. "
                    f"Winning {b.name} first is the highest-leverage move; the rest of the "
                    f"camp tends to follow."
                )
                break
        for move in result.counter_moves:
            lines.append(f"- {move}")

    # the honest caveat — this is what separates a decision tool from a toy
    unc = result.confidence
    lines.append(
        f"Treat this as a structured hypothesis, not a verdict. Friction "
        f"{result.friction:.0f}/100 (±{result.uncertainty:.0f}, {unc} confidence) is a heuristic "
        f"index built from how your input was grounded — it is not a calibrated probability "
        f"of what will happen. Verify against the frozen log in ~48h: the prediction is "
        f"written down so it can be checked, not just believed."
    )
    return "\n".join(lines)
