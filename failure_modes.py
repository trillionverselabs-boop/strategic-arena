# Failure modes — MASS (Qian et al., "MASS: Optimizing Multi-Agent Systems with
# Enhanced Prompts and Topologies") 8 naive-baseline failure modes, used as a
# quality checklist.
# This is a real, defensible quality signal: for a given run, report which known
# failure modes the run's structure avoided vs whether any are suspected.
# It does NOT claim the simulation is "accurate" — that's a separate, honest no.

from __future__ import annotations

from typing import List

from .models import SimulationResult

# The MASS 8 (paraphrased from the multi-agent-social-simulation skill reference):
# each has a concrete control that our engine implements.
FAILURE_MODES = [
    {
        "id": "unbounded_repetition",
        "name": "Unbounded repetition",
        "control": "Fixed rounds + reflection cadence (reflections only when memory "
                   "is large enough; bounded stance deltas).",
        "holds": True,
    },
    {
        "id": "role_collapse",
        "name": "Role collapse (all agents converge to one voice)",
        "control": "Each agent acts from its own persona stance and grounded reasons; "
                   "stance is clamped, delegation refused.",
    },
    {
        "id": "missing_grounding",
        "name": "Missing grounding (agents hallucinate context)",
        "control": "Stances carry source attribution from the input documents; the report "
                   "separates 'grounded' from 'speculated'.",
    },
    {
        "id": "no_information_boundary",
        "name": "No information boundary (agents share everything)",
        "control": "Agents observe broadcast events but act from their own memory stream "
                   "and stance; they do not pool knowledge.",
    },
    {
        "id": "unstructured_conversation",
        "name": "Unstructured conversation (no protocol)",
        "control": "Each round is a structured observe → retrieve → act step with a typed "
                   "JSON move (stance_delta, action, text).",
    },
    {
        "id": "unstaged_time",
        "name": "Unstaged time (no temporal structure)",
        "control": "Rounds are staged; interventions inject at a specific round; "
                   "snapshots are frozen per round.",
    },
    {
        "id": "unbounded_agent_set",
        "name": "Unbounded agent set",
        "control": "max_personas caps the stakeholder count (3–16) before simulation.",
    },
    {
        "id": "silent_failures",
        "name": "Silent failures (errors swallowed)",
        "control": "The engine and its fallbacks are explicit (e.g. a fallback persona set "
                   "when extraction returns nothing), and the report says when it fires.",
    },
]


def evaluate_run(result: SimulationResult) -> List[dict]:
    """Return the 8 failure modes with a per-run verdict.
    `holds` is a structural property of the engine; `suspected` is a per-run signal."""
    suspected = _suspected_modes(result)
    out = []
    for mode in FAILURE_MODES:
        out.append({
            "id": mode["id"], "name": mode["name"], "control": mode["control"],
            "holds": mode.get("holds", True),
            "suspected": mode["id"] in suspected,
        })
    return out


def _suspected_modes(result: SimulationResult) -> set:
    """Cheap, local heuristics for per-run signals — no extra LLM calls."""
    suspected = set()
    personas = result.personas
    # role collapse: every persona at the same extreme stance
    if len(personas) >= 2:
        stances = [round(p.stance, 1) for p in personas]
        if len(set(stances)) == 1 and stances[0] in (1.0, -1.0):
            suspected.add("role_collapse")
    # missing grounding: no persona carries a source-attributed reason
    if personas and not any((p.reasons and p.reasons[0]) for p in personas):
        suspected.add("missing_grounding")
    # silent failure fallback fired
    if any(p.name.startswith("Stakeholder ") for p in personas):
        suspected.add("silent_failures")
    # unstructured drift: stance variance exploded exactly to the clamp on most actors
    extremes = sum(1 for p in personas if abs(p.stance) >= 0.99)
    if personas and extremes / len(personas) > 0.8:
        suspected.add("unbounded_repetition")
    return suspected
