# Tool registration — arena_run/status/report/history/calibration as agent tools.
# Handlers are thin: build a Scenario, run the engine, return JSON.

from __future__ import annotations

import json

from . import engine
from .llm_adapter import LlmAdapter
from .models import Scenario


def _scenario_from(params: dict) -> Scenario:
    docs = params.get("documents", []) or []
    if not docs and not params.get("urls"):
        # URL-only runs are legitimate; documents may legitimately be empty.
        pass
    documents = [
        {"type": d.get("type", "decision"), "content": d.get("content", ""),
         "source": d.get("source", "")}
        for d in docs
    ]
    personas = [
        {"name": p.get("name", "Stakeholder"), "role": p.get("role", "stakeholder"),
         "stance": p.get("stance", 0.0), "reasons": p.get("reasons", [])}
        for p in params.get("personas", [])
    ]
    interventions = [
        {"name": iv.get("name", "Intervention"), "description": iv.get("description", ""),
         "inject_at_round": iv.get("inject_at_round", 3)}
        for iv in params.get("interventions", [])
    ]
    return Scenario(
        title=params.get("title", "Untitled"),
        goal=params.get("goal", "adoption"),
        documents=documents,
        urls=params.get("urls", []) or [],
        window=params.get("window", "24h"),
        model=params.get("model", "default"),
        personas=personas,
        interventions=interventions,
        max_personas=params.get("max_personas", 8),
        temperature=params.get("temperature", 0.6),
        # auto when unset, so the lens is never guessed into a corner
        kind=str(params.get("kind") or "auto"),
    )


def register_tools(ctx, allow_model_override: bool = False) -> None:
    # ── arena_run ──────────────────────────────────────────────────
    run_schema = {
        "name": "arena_run",
        "description": (
            "Run a stakeholder reaction review on a decision (a strategic-response read, not a "
            "forecast). Give a title and at least one document (type=decision, content=text) or "
            "one or more URLs. Optionally add evidence documents for grounding, a goal "
            "(adoption/open_weight/deprecation/campaign), a window (6h/12h/24h/48h), and "
            "mid-run interventions. Returns a run with friction, the veto player, coalitions, "
            "best responses, the red/purple/blue competition read, and frozen claims you can "
            "score later. Use arena_calibration for the track record. "
            "Set kind='paper' for a research paper (arXiv/DOI): it draws the MARKET room "
            "(incumbent, fast follower, buyer, integrator, channel, the authors' lab) and "
            "additionally decodes what the publication gives away — what is reproducible from "
            "the text, what it withholds, how long a funded competitor needs to rebuild it "
            "(the replication clock), and whether the authors are the first competitor. "
            "kind='whitepaper' is the different, peer-review room."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title for the decision."},
                "goal": {"type": "string", "enum": ["adoption", "open_weight", "deprecation", "campaign"]},
                "kind": {
                    "type": "string",
                    "enum": ["auto", "repo", "post", "paper", "whitepaper", "case_study",
                             "press", "tweet", "decision"],
                    "description": (
                        "What is being read, which sets the room. 'paper' = a research paper read "
                        "for the product it implies and the market that would receive it (adds the "
                        "moat decode + replication clock). 'whitepaper' = defensibility review. "
                        "Omit / 'auto' reads it off the link."
                    ),
                },
                "window": {"type": "string", "enum": ["30m", "1h", "4h", "6h", "12h", "24h", "48h"]},
                "model": {
                    "type": "string",
                    "description": (
                        "Optional model id from the live catalogue (see the desktop form, "
                        "or GET /api/plugins/strategic-arena/models). Empty / 'default' runs on the "
                        "user's active model. Only honoured when the user granted "
                        "llm.model_override."
                    ),
                },
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["decision", "evidence", "context"]},
                            "content": {"type": "string"},
                            "source": {"type": "string"},
                        },
                        "required": ["type", "content"],
                    },
                },
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URLs (a blog post, a repo README, a landing page) to fetch and treat as documents. Use this OR documents, or both.",
                },
                "interventions": {
                    "type": "array",
                    "description": (
                        "Mid-run counter-moves to inject (the god-mode move: change one thing "
                        "mid-simulation and watch the graph bend)."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "inject_at_round": {"type": "integer", "default": 3},
                        },
                        "required": ["name", "description"],
                    },
                },
            },
            "required": ["title"],
        },
    }

    def handle_run(params, **kwargs):
        scenario = _scenario_from(params)
        llm = LlmAdapter(
            ctx.llm,
            temperature=scenario.temperature,
            model=scenario.model,
            allow_override=allow_model_override,
        )
        result = engine.run_scenario(scenario, llm)
        return json.dumps({
            "run_id": result.run_id, "title": result.title,
            "friction": result.friction, "uncertainty": result.uncertainty,
            "confidence": result.confidence,
            "blocker": result.blocker.name if result.blocker else None,
            "counter_moves": result.counter_moves,
            "sea": result.sea,
            "claims": result.claims,
            "degraded": result.degraded,
            "summary": result.summary,
            "personas": [{"name": p.name, "stance": round(p.stance, 2)} for p in result.personas],
        })

    ctx.register_tool(name="arena_run", toolset="arena", schema=run_schema, handler=handle_run)

    # ── arena_status / report / history / calibration ─────────────
    status_schema = {
        "name": "arena_status",
        "description": "Check the status of a review run (running/done + progress).",
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string"}}, "required": ["run_id"]},
    }

    def handle_status(params, **kwargs):
        return json.dumps(engine.get_progress(params.get("run_id", "")))

    ctx.register_tool(name="arena_status", toolset="arena", schema=status_schema, handler=handle_status)

    report_schema = {
        "name": "arena_report",
        "description": "Return the report for a past run. By default the short report; "
                       "pass full=true for the opt-in long-form analysis.",
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string"},
            "full": {"type": "boolean", "default": False}},
            "required": ["run_id"]},
    }

    def handle_report(params, **kwargs):
        from . import reporting
        run_id = str(params.get("run_id", "") or "")
        try:
            data = reporting.load_run(run_id)
        except ValueError as exc:
            return json.dumps({"error": str(exc), "run_id": run_id})
        key = "report_full" if params.get("full") else "report"
        return json.dumps({"run_id": run_id, "report": data.get(key, "")})

    ctx.register_tool(name="arena_report", toolset="arena", schema=report_schema, handler=handle_report)

    history_schema = {
        "name": "arena_history",
        "description": "List past review runs (most recent first) so you can verify results over time.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "default": 20}}},
    }

    def handle_history(params, **kwargs):
        from . import reporting
        return json.dumps(reporting.list_runs(params.get("limit", 20)))

    ctx.register_tool(name="arena_history", toolset="arena", schema=history_schema, handler=handle_history)

    cal_schema = {
        "name": "arena_calibration",
        "description": "The track record: runs, how many were scored, claim hit rate and "
                       "friction error. Judge accuracy by this, never by a single report.",
        "parameters": {"type": "object", "properties": {}},
    }

    def handle_calibration(params, **kwargs):
        from . import reporting
        return json.dumps(reporting.calibration())

    ctx.register_tool(name="arena_calibration", toolset="arena",
                      schema=cal_schema, handler=handle_calibration)

    # ── arena_due ──────────────────────────────────────────────────
    due_schema = {
        "name": "arena_due",
        "description": (
            "Reviews whose window has closed and that nobody has scored yet. Call this when a "
            "review's timeline is up: it returns {due: [{run_id, title, due_at, window, claims}]} "
            "so you can ask the user to score each claim (✓/✗) and set a verdict. Scoring is what "
            "builds the track record; an unscored run is a wasted claim."
        ),
        "parameters": {"type": "object", "properties": {
            "as_of": {"type": "string",
                      "description": "Optional ISO timestamp to evaluate 'due' against (default: now)."}}},
    }

    def handle_due(params, **kwargs):
        from . import reporting
        rows = reporting.due_claims(as_of=params.get("as_of") or None)
        return json.dumps({"due": rows, "count": len(rows)})

    ctx.register_tool(name="arena_due", toolset="arena", schema=due_schema, handler=handle_due)

    # ── arena_export ───────────────────────────────────────────────
    export_schema = {
        "name": "arena_export",
        "description": (
            "Write a review to a decision record file (`decisions/<slug>.md`) and return the path. "
            "The file keeps the run metadata, the competition read, the frozen claims as a score "
            "checklist, and the verdict. Re-exporting after scoring fills the verdict in place. "
            "Use it to keep the review next to the code or the change ticket."
        ),
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string"},
            "out_dir": {"type": "string", "default": "decisions",
                        "description": "Directory for the record. Relative paths resolve "
                                       "inside the plugin data dir; absolute paths are "
                                       "accepted only inside it. Anything outside is refused."}},
            "required": ["run_id"]},
    }

    def handle_export(params, **kwargs):
        from . import reporting
        run_id = str(params.get("run_id", "") or "")
        try:
            path = reporting.export_decision(run_id,
                                             out_dir=params.get("out_dir") or "decisions")
        except FileNotFoundError:
            return json.dumps({"error": "run not found", "run_id": run_id})
        except ValueError as exc:
            return json.dumps({"error": str(exc), "run_id": run_id})
        return json.dumps({"run_id": run_id, "path": path})

    ctx.register_tool(name="arena_export", toolset="arena",
                      schema=export_schema, handler=handle_export)


