# Reporting — the user-facing markdown report, the frozen JSONL prediction log,
# and the run-history / calibration store (so results can be checked later).

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .models import SimulationResult
from .paths import runs_dir


def _run_dir(run_id: str) -> Path:
    return runs_dir() / run_id


def write_report(result: SimulationResult) -> str:
    """Markdown report. Returns the text; the caller writes it via save_run."""
    bl = result.blocker
    lines = []
    lines.append(f"# {result.title}")
    lines.append(f"_Goal: {result.goal.value} · {result.rounds} rounds · run {result.run_id}_")
    lines.append("")
    lines.append(f"**Friction: {result.friction:.0f}/100** (±{result.uncertainty:.0f}, {result.confidence} confidence)")
    lines.append("")
    if result.degraded:
        lines.append(f"> ⚠️ **DEGRADED RUN — do not trust this.** {result.degraded_reason}. "
                     "Stances held still where the model failed; re-run before deciding anything.")
        lines.append("")
    if result.sea:
        lines.append(f"**{result.sea.get('label', '')}** (competition: {result.sea.get('level', '')}) — "
                     f"{result.sea.get('why', '')}")
        lines.append("")
    if bl:
        lines.append(f"## Veto player: {bl.name} (stance {bl.stance:+.2f})")
        if bl.reasons:
            lines.append(f"- Why (grounded): {bl.reasons[0]}")
        lines.append("")
    else:
        lines.append("## Veto player: none identified")
        lines.append("- No stakeholder is below the blocking threshold in this simulation.")
        lines.append("")
    if result.counter_moves:
        lines.append("## Best response")
        for m in result.counter_moves:
            lines.append(f"- {m}")
        lines.append("")
    if result.recommendation:
        lines.append("## Recommendation — what to actually do")
        lines.append(result.recommendation)
        lines.append("")
    if result.camps:
        lines.append("## Coalitions (camp structure)")
        for c in result.camps:
            lines.append(f"- **{c['name']}** ({c['lean']}): {', '.join(c['members'])}")
        lines.append("")
    if result.claims:
        lines.append("## Claims to check (score these in 48h)")
        for c in result.claims:
            lines.append(f"- `{c['id']}` {c['claim']}")
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
    lines.append("> This is a structured review of the response to your move, grounded in "
                 "your input — not a forecast. Score the claims above when the window closes.")
    return "\n".join(lines)


def write_full_report(result: SimulationResult) -> str:
    """The opt-in long-form report — same grounded content, expanded."""
    bl = result.blocker
    lines = []
    lines.append(f"# {result.title} — full analysis")
    lines.append(f"_Goal: {result.goal.value} · {result.rounds} rounds · run {result.run_id}_")
    lines.append("")
    lines.append(f"**Friction: {result.friction:.0f}/100** (±{result.uncertainty:.0f}, {result.confidence} confidence)")
    lines.append("")
    if result.degraded:
        lines.append(f"> ⚠️ **DEGRADED RUN — do not trust this.** {result.degraded_reason}.")
        lines.append("")
    if result.sea:
        lines.append(f"**{result.sea.get('label', '')}** (competition: {result.sea.get('level', '')}) — "
                     f"{result.sea.get('meaning', '')}. Trigger: {result.sea.get('why', '')}")
        lines.append("")
    lines.append(
        "_This is a strategic-response review grounded in the documents you provided. Every "
        "stakeholder stance is traced to the input text that drove it. The friction index is a "
        "structured heuristic, not a calibrated probability of real-world outcome. The claims "
        "below are frozen so the review can be scored later._"
    )
    lines.append("")

    if result.recommendation:
        lines.append("## 1. The recommendation")
        lines.append(result.recommendation)
        lines.append("")

    lines.append("## 2. Stakeholder by stakeholder")
    for p in sorted(result.personas, key=lambda x: x.stance):
        bar = "🔴 Against" if p.stance < -0.3 else ("🟢 For" if p.stance > 0.3 else "🟡 Undecided")
        lines.append(f"### {p.name} — {bar} ({p.stance:+.2f})")
        if p.reasons and p.reasons[0]:
            lines.append(f"- **Why (grounded in your input):** {p.reasons[0]}")
        else:
            lines.append("- **Why:** simulated reasoning (no source in your input backed this stance).")
        lines.append("")

    if result.camps:
        lines.append("## 3. Coalitions")
        lines.append(
            "Stakeholders cluster into camps by stance and by who opposes/supports whom. "
            "A camp is a coalition — winning its most-connected member tends to win the rest."
        )
        for c in result.camps:
            lines.append(f"- **{c['name']}** ({c['lean']}): {', '.join(c['members'])}")
        lines.append("")

    if result.snapshots:
        lines.append("## 4. Round-by-round stance trajectory")
        for snap in result.snapshots:
            desc = ", ".join(f"{k} {v:+.2f}" for k, v in sorted(snap.stances.items()))
            lines.append(f"- Round {snap.round}: {desc}")
        lines.append("")

    if result.counter_moves:
        lines.append("## 5. Best responses, expanded")
        lines.append(
            "These are the moves the simulation suggests to convert the veto player. They are "
            "derived from that player's stated reason in your own input — re-run with one "
            "injected mid-simulation to see the counterfactual."
        )
        for m in result.counter_moves:
            lines.append(f"- {m}")
        lines.append("")

    lines.append("## 6. The claims — score these")
    if result.claims:
        for c in result.claims:
            lines.append(f"- `{c['id']}` ({c['kind']}) {c['claim']}")
            if c.get("source"):
                lines.append(f"  - source: {c['source'][:200]}")
    else:
        lines.append("- No claims were produced (this should not happen — report it).")
    lines.append("")
    lines.append(
        "Come back after the window closes and score each claim. If the named veto player "
        "wasn't the problem, or friction landed outside the band, the hypothesis was wrong — "
        "and the provenance section shows which input claim led it astray. That is the point: "
        "a checkable review, not a story."
    )
    lines.append("")

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

    if result.provenance:
        lines.append("## 8. Provenance — every stance, traced to your input")
        for prov in result.provenance:
            lines.append(f"- {prov}")
        lines.append("")

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


def write_frozen_log(result: SimulationResult, manifest: dict | None = None) -> str:
    """JSONL: manifest + run metadata + claims + per-round snapshots + events."""
    rows: List[dict] = []
    if manifest:
        rows.append(manifest)
    rows.append(
        {"run_id": result.run_id, "created_at": result.created_at,
         "type": "meta", "title": result.title, "goal": result.goal.value,
         "rounds": result.rounds, "friction": result.friction,
         "uncertainty": result.uncertainty, "confidence": result.confidence,
         "blocker": result.blocker.name if result.blocker else None,
         "sea_state": result.sea.get("state", ""), "degraded": result.degraded}
    )
    for c in result.claims:
        rows.append({"type": "claim", **c})
    for s in result.snapshots:
        rows.append({"type": "snapshot", "round": s.round, "stances": s.stances})
    for e in result.events:
        rows.append({"type": "event", "round": e.round, "actor": e.actor,
                     "action": e.action, "text": e.text, "source": e.source})
    return "\n".join(json.dumps(r) for r in rows)


# ── history / store ────────────────────────────────────────────────────

def save_run(result: SimulationResult, report_md: str, frozen_jsonl: str,
             graph_payload: dict, full_report_md: str | None = None,
             manifest: dict | None = None) -> None:
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
        "rounds": result.rounds,
        "uncertainty": result.uncertainty, "confidence": result.confidence,
        "blocker": result.blocker.name if result.blocker else None,
        "summary": result.summary,
        "sea_state": result.sea.get("state", ""),
        "sea_label": result.sea.get("label", ""),
        "sea_color": result.sea.get("color", ""),
        "sea_level": result.sea.get("level", ""),
        "sea_why": result.sea.get("why", ""),
        "claims": len(result.claims),
        "degraded": result.degraded,
        "model": (manifest or {}).get("model", ""),
        "code_commit": (manifest or {}).get("code_commit", ""),
    }, indent=1))


def list_runs(limit: int = 20) -> List[dict]:
    root = runs_dir()
    if not root.exists():
        return []
    out = []
    for d in root.iterdir():
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


def load_claims(run_id: str) -> List[dict]:
    p = _run_dir(run_id) / "log.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("type") == "claim":
            out.append(row)
    return out


def mark_verified(run_id: str, verdict: str, note: str = "",
                  hits: dict | None = None,
                  actual_friction: float | None = None) -> dict:
    """Score a frozen review. verdict: right|partial|wrong. hits: claim id -> bool."""
    if verdict not in ("right", "partial", "wrong"):
        raise ValueError("verdict must be right|partial|wrong")
    d = _run_dir(run_id)
    meta_path = d / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(run_id)
    meta = json.loads(meta_path.read_text())

    hits = hits or {}
    scored = sum(1 for v in hits.values() if v)
    total = len(hits) or len(load_claims(run_id))

    meta["verified"] = {
        "verdict": verdict,
        "note": note,
        "at": datetime.now().isoformat(timespec="seconds"),
        "hits": hits,
        "score": round(scored / total, 3) if total else None,
        "actual_friction": actual_friction,
        "friction_error": (round(abs(actual_friction - meta.get("friction", 0) or 0), 1)
                           if actual_friction is not None else None),
    }
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta["verified"]


def calibration() -> dict:
    """Aggregate every run into a track record — the product's value over time."""
    root = runs_dir()
    runs: List[dict] = []
    if root.exists():
        for d in root.iterdir():
            m = d / "meta.json"
            if not m.exists():
                continue
            try:
                runs.append(json.loads(m.read_text()))
            except Exception:
                continue
    verified = [r for r in runs if r.get("verified")]
    scores = [r["verified"]["score"] for r in verified if r["verified"].get("score") is not None]
    errors = [r["verified"]["friction_error"] for r in verified
              if r["verified"].get("friction_error") is not None]
    by_sea: dict = {}
    for r in runs:
        k = r.get("sea_state") or "unknown"
        by_sea[k] = by_sea.get(k, 0) + 1
    return {
        "runs": len(runs),
        "verified": len(verified),
        "claim_hit_rate": round(sum(scores) / len(scores), 3) if scores else None,
        "mean_friction_error": round(sum(errors) / len(errors), 1) if errors else None,
        "verdicts": {v: sum(1 for r in verified if r["verified"]["verdict"] == v)
                     for v in ("right", "partial", "wrong")},
        "sea_state": by_sea,
        "note": "hit rate is only meaningful with n >= 10 scored runs",
    }


def _final_stances(run_id: str) -> dict:
    p = _run_dir(run_id) / "log.jsonl"
    if not p.exists():
        return {}
    last = {}
    for line in p.read_text().splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("type") == "snapshot":
            last = row.get("stances") or {}
    return last


def compare_runs(title: str = "", limit: int = 20) -> dict:
    """Compare every run of the same decision across timelines.

    This is the feature that turns repetition into evidence: run the same decision
    at 30m / 4h / 24h and see whether the read is stable or a product of how long
    you let it run.
    """
    runs = list_runs(200)
    if title:
        needle = title.strip().lower()
        runs = [r for r in runs if needle in str(r.get("title", "")).lower()]
    runs = runs[:limit]

    rows = []
    for r in runs:
        rows.append({
            "run_id": r.get("run_id", ""),
            "title": r.get("title", ""),
            "rounds": r.get("rounds") or r.get("summary", ""),
            "friction": r.get("friction"),
            "confidence": r.get("confidence", ""),
            "blocker": r.get("blocker"),
            "sea_state": r.get("sea_state", ""),
            "sea_label": r.get("sea_label", ""),
            "created_at": r.get("created_at", ""),
            "verified": r.get("verified", {}),
        })

    frictions = [x["friction"] for x in rows if isinstance(x["friction"], (int, float))]
    blockers = [x["blocker"] for x in rows if x["blocker"]]
    stable = bool(rows) and len(set(blockers)) <= 1 and (
        not frictions or (max(frictions) - min(frictions)) <= 15
    )

    comparison = {
        "title": title,
        "runs": len(rows),
        "rows": rows,
        "friction_min": min(frictions) if frictions else None,
        "friction_max": max(frictions) if frictions else None,
        "friction_spread": round(max(frictions) - min(frictions), 1) if frictions else None,
        "blocker_stable": bool(rows) and len(set(blockers)) <= 1,
        "stable": stable,
        "reading": (
            "Stable across timelines — the same veto player and a friction spread "
            "inside ±15. Run it once more before you act on it."
            if stable else
            "Unstable across timelines — the answer moves with how long you run it. "
            "That is a finding, not a failure: read the per-run rows before deciding."
            if rows else "No runs yet for this decision."
        ),
    }

    if len(rows) >= 2:
        shortest = min(rows, key=lambda x: x.get("rounds") or 0)
        longest = max(rows, key=lambda x: x.get("rounds") or 0)
        a, b = _final_stances(shortest["run_id"]), _final_stances(longest["run_id"])
        comparison["stance_drift"] = {
            k: round(b[k] - a.get(k, 0.0), 3) for k in b
        }
        comparison["drift_between"] = [shortest["run_id"], longest["run_id"]]

    return comparison


def _parse(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None
