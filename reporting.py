# Reporting — the user-facing markdown report, the frozen JSONL prediction log,
# and the run-history index (so the user can look back and verify results later).

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .models import SimulationResult

RUNS_DIR = Path.home() / ".hermes" / "upfront" / "runs"


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def write_report(result: SimulationResult) -> str:
    """Markdown report. Returns the text; caller writes it via the store."""
    bl = result.blocker
    lines = []
    lines.append(f"# {result.title}")
    lines.append(f"_Goal: {result.goal.value} · {result.rounds} rounds · run {result.run_id}_")
    lines.append("")
    lines.append(f"**Friction: {result.friction:.0f}/100** (±{result.uncertainty:.0f}, {result.confidence} confidence)")
    lines.append("")
    if bl:
        lines.append(f"## Blocker: {bl.name} (stance {bl.stance:+.2f})")
        if bl.reasons:
            lines.append(f"- Why (grounded): {bl.reasons[0]}")
        lines.append("")
    if result.counter_moves:
        lines.append("## Counter-moves")
        for m in result.counter_moves:
            lines.append(f"- {m}")
        lines.append("")
    if result.recommendation:
        lines.append("## Recommendation — what to actually do")
        lines.append(result.recommendation)
        lines.append("")
    if result.camps:
        lines.append("## Stakeholder camps (GraphRAG community structure)")
        for c in result.camps:
            lines.append(f"- **{c['name']}** ({c['lean']}): {', '.join(c['members'])}")
        lines.append("")
    lines.append("## Stakeholders")
    for p in sorted(result.personas, key=lambda x: x.stance):
        bar = "🔴" if p.stance < -0.3 else ("🟢" if p.stance > 0.3 else "🟡")
        reason = p.reasons[0] if p.reasons else "(simulated)"
        lines.append(f"- {bar} {p.name} ({p.stance:+.2f}) — {reason}")
    lines.append("")
    if result.provenance:
        lines.append("## Provenance (why we think what we think)")
        for prov in result.provenance:
            lines.append(f"- {prov}")
        lines.append("")
    if result.failure_modes:
        lines.append("## Failure-mode report (MASS 8 — was this run built right?)")
        held = sum(1 for m in result.failure_modes if m["holds"])
        suspected = [m["name"] for m in result.failure_modes if m["suspected"]]
        lines.append(f"- Design guards: {held}/{len(result.failure_modes)} hold structurally.")
        if suspected:
            lines.append(f"- Per-run signals to watch: {', '.join(suspected)}.")
        else:
            lines.append("- No per-run failure signals detected.")
        lines.append("- This reports whether the *simulation* was built soundly. It does not "
                     "claim the simulation predicts reality — see the recommendation caveat.")
        lines.append("")
    lines.append("## Key events")
    shown = 0
    for e in result.events:
        if e.text:
            lines.append(f"- R{e.round} {e.actor} {e.action}: {e.text}")
            shown += 1
        if shown >= 12:
            break
    lines.append("")
    lines.append("> This is a simulation grounded in your input, not a guarantee. Verify after ~48h.")
    return "\n".join(lines)


def write_full_report(result: SimulationResult) -> str:
    """The opt-in long-form report. Everything in it traces back to the same
    grounded output the short report shows — it is the same content, expanded
    with per-stakeholder narratives, the camp structure, the round-by-round
    trajectory, and the failure-mode audit. Nothing in here is invented to
    fill pages; if a section has no data, it says so."""
    bl = result.blocker
    lines = []
    lines.append(f"# {result.title} — full analysis")
    lines.append(f"_Goal: {result.goal.value} · {result.rounds} rounds · run {result.run_id}_")
    lines.append("")
    lines.append(f"**Friction: {result.friction:.0f}/100** (±{result.uncertainty:.0f}, {result.confidence} confidence)")
    lines.append("")
    lines.append(
        "_This is a simulation grounded in the documents you provided. Every stakeholder "
        "stance is traced to the input text that drove it. The friction index is a "
        "structured heuristic, not a calibrated probability of real-world outcome. A dated "
        "prediction is frozen in the run log so the result can be verified later._"
    )
    lines.append("")

    # 1. The headline recommendation (same as the short report)
    if result.recommendation:
        lines.append("## 1. The recommendation")
        lines.append(result.recommendation)
        lines.append("")

    # 2. Per-stakeholder narrative
    lines.append("## 2. Stakeholder by stakeholder")
    for p in sorted(result.personas, key=lambda x: x.stance):
        bar = "🔴 Against" if p.stance < -0.3 else ("🟢 For" if p.stance > 0.3 else "🟡 Undecided")
        lines.append(f"### {p.name} — {bar} ({p.stance:+.2f})")
        if p.reasons and p.reasons[0]:
            lines.append(f"- **Why (grounded in your input):** {p.reasons[0]}")
        else:
            lines.append("- **Why:** simulated reasoning (no source in your input backed this stance).")
        lines.append("")

    # 3. Camp structure
    if result.camps:
        lines.append("## 3. Stakeholder camps")
        lines.append(
            "Stakeholders cluster into camps by stance and by who opposes/supports whom. "
            "A camp is a coalition — winning its most-connected member tends to win the rest."
        )
        for c in result.camps:
            lines.append(f"- **{c['name']}** ({c['lean']}): {', '.join(c['members'])}")
        lines.append("")

    # 4. Round-by-round trajectory (the actual path, not just the endpoints)
    if result.snapshots:
        lines.append("## 4. Round-by-round stance trajectory")
        for snap in result.snapshots:
            desc = ", ".join(f"{k} {v:+.2f}" for k, v in sorted(snap.stances.items()))
            lines.append(f"- Round {snap.round}: {desc}")
        lines.append("")

    # 5. Counter-moves, expanded
    if result.counter_moves:
        lines.append("## 5. Counter-moves, expanded")
        lines.append(
            "These are the moves the simulation suggests to convert the blocker. They are "
            "derived from the blocker's stated reason in your own input — run the product "
            "again with a counter-move injected at an early round to see the graph respond."
        )
        for m in result.counter_moves:
            lines.append(f"- {m}")
        lines.append("")

    # 6. The frozen prediction (what to check, and when)
    lines.append("## 6. The frozen prediction — verify this")
    if bl:
        lines.append(
            f"Within the {result.rounds}-round window, the simulation predicts **{bl.name}** will be "
            f"the most resistant stakeholder (final stance {bl.stance:+.2f}), and that friction "
            f"lands at {result.friction:.0f}/100 (±{result.uncertainty:.0f})."
        )
    lines.append(
        "Come back after the window closes and compare against reality. If the named blocker "
        "wasn't the problem — or friction landed far outside ±uncertainty — the hypothesis was "
        "wrong, and the provenance section below shows exactly which input claim led it astray. "
        "That is the point: a checkable prediction, not a story."
    )
    lines.append("")

    # 7. Failure-mode audit
    if result.failure_modes:
        lines.append("## 7. Failure-mode audit (MASS 8)")
        lines.append(
            "A simulation like this can fool you in known ways. This run was checked against "
            "all eight. These report whether the *simulation was built soundly* — they do not "
            "claim the simulation predicts reality."
        )
        for m in result.failure_modes:
            mark = "⚠️ suspected" if m["suspected"] else "✓ clear"
            lines.append(f"- **{m['name']}** — {mark}. {m['control']}")
        lines.append("")

    # 8. Provenance
    if result.provenance:
        lines.append("## 8. Provenance — every stance, traced to your input")
        for prov in result.provenance:
            lines.append(f"- {prov}")
        lines.append("")

    # 9. Input quality
    if result.input_quality:
        iq = result.input_quality
        lines.append("## 9. Input quality")
        lines.append(f"- Confidence: {result.confidence} (score {iq.get('quality', 0):.2f})")
        sug = iq.get("suggestions") or []
        if sug:
            lines.append("- To strengthen the next run:")
            for s in sug:
                lines.append(f"  - {s}")
        lines.append("")

    return "\n".join(lines)


def write_frozen_log(result: SimulationResult) -> str:
    """One JSON object per line: run metadata + per-round snapshots. Immutable."""
    rows = [
        {"run_id": result.run_id, "created_at": result.created_at,
         "type": "meta", "title": result.title, "goal": result.goal.value,
         "rounds": result.rounds, "friction": result.friction,
         "uncertainty": result.uncertainty, "confidence": result.confidence,
         "blocker": result.blocker.name if result.blocker else None},
    ]
    for s in result.snapshots:
        rows.append({"type": "snapshot", "round": s.round, "stances": s.stances})
    for e in result.events:
        rows.append({"type": "event", "round": e.round, "actor": e.actor,
                     "action": e.action, "text": e.text, "source": e.source})
    return "\n".join(json.dumps(r) for r in rows)


# ── history store ──────────────────────────────────────────────────────

def save_run(result: SimulationResult, report_md: str, frozen_jsonl: str, graph_payload: dict,
             full_report_md: str | None = None) -> None:
    d = _run_dir(result.run_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "report.md").write_text(report_md)
    (d / "log.jsonl").write_text(frozen_jsonl)
    (d / "graph.json").write_text(json.dumps(graph_payload, indent=1))
    if full_report_md is not None:
        (d / "report_full.md").write_text(full_report_md)
    (d / "meta.json").write_text(json.dumps({
        "run_id": result.run_id, "title": result.title, "goal": result.goal.value,
        "created_at": result.created_at, "friction": result.friction,
        "blocker": result.blocker.name if result.blocker else None,
        "summary": result.summary,
    }, indent=1))


def list_runs(limit: int = 20) -> List[dict]:
    if not RUNS_DIR.exists():
        return []
    out = []
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):  # newest first (name sorts by mtime-ish via id — refined by mtime)
        m = d / "meta.json"
        if m.exists():
            try:
                out.append(json.loads(m.read_text()))
            except Exception:
                pass
    out.sort(key=lambda r: _parse(r.get("created_at", "")) or 0, reverse=True)
    return out[:limit]


def load_run(run_id: str) -> dict:
    d = _run_dir(run_id)
    return {
        "meta": json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {},
        "report": (d / "report.md").read_text() if (d / "report.md").exists() else "",
        "report_full": (d / "report_full.md").read_text() if (d / "report_full.md").exists() else "",
        "graph": json.loads((d / "graph.json").read_text()) if (d / "graph.json").exists() else {},
    }


def _parse(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None
