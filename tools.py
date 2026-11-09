# Tool registration — upfront_run/status/report/history/calibration as agent tools.
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
    )


def register_tools(ctx, allow_model_override: bool = False) -> None:
    # ── upfront_run ──────────────────────────────────────────────────
    run_schema = {
        "name": "upfront_run",
        "description": (
            "Run a stakeholder reaction review on a decision (a strategic-response read, not a "
            "forecast). Give a title and at least one document (type=decision, content=text) or "
            "one or more URLs. Optionally add evidence documents for grounding, a goal "
            "(adoption/open_weight/deprecation/campaign), a window (6h/12h/24h/48h), and "
            "mid-run interventions. Returns a run with friction, the veto player, coalitions, "
            "best responses, the red/purple/blue competition read, and frozen claims you can "
            "score later. Use upfront_calibration for the track record."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title for the decision."},
                "goal": {"type": "string", "enum": ["adoption", "open_weight", "deprecation", "campaign"]},
                "window": {"type": "string", "enum": ["30m", "1h", "4h", "6h", "12h", "24h", "48h"]},
                "model": {
                    "type": "string",
                    "description": (
                        "Optional model id from the live catalogue (see the desktop form, "
                        "or GET /api/plugins/upfront/models). Empty / 'default' runs on the "
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

    ctx.register_tool(name="upfront_run", toolset="upfront", schema=run_schema, handler=handle_run)

    # ── upfront_status / report / history / calibration ─────────────
    status_schema = {
        "name": "upfront_status",
        "description": "Check the status of a review run (running/done + progress).",
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string"}}, "required": ["run_id"]},
    }

    def handle_status(params, **kwargs):
        return json.dumps(engine.get_progress(params.get("run_id", "")))

    ctx.register_tool(name="upfront_status", toolset="upfront", schema=status_schema, handler=handle_status)

    report_schema = {
        "name": "upfront_report",
        "description": "Return the report for a past run. By default the short report; "
                       "pass full=true for the opt-in long-form analysis.",
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string"},
            "full": {"type": "boolean", "default": False}},
            "required": ["run_id"]},
    }

    def handle_report(params, **kwargs):
        from . import reporting
        data = reporting.load_run(params.get("run_id", ""))
        key = "report_full" if params.get("full") else "report"
        return json.dumps({"run_id": params.get("run_id", ""), "report": data.get(key, "")})

    ctx.register_tool(name="upfront_report", toolset="upfront", schema=report_schema, handler=handle_report)

    history_schema = {
        "name": "upfront_history",
        "description": "List past review runs (most recent first) so you can verify results over time.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "default": 20}}},
    }

    def handle_history(params, **kwargs):
        from . import reporting
        return json.dumps(reporting.list_runs(params.get("limit", 20)))

    ctx.register_tool(name="upfront_history", toolset="upfront", schema=history_schema, handler=handle_history)

    cal_schema = {
        "name": "upfront_calibration",
        "description": "The track record: runs, how many were scored, claim hit rate and "
                       "friction error. Judge accuracy by this, never by a single report.",
        "parameters": {"type": "object", "properties": {}},
    }

    def handle_calibration(params, **kwargs):
        from . import reporting
        return json.dumps(reporting.calibration())

    ctx.register_tool(name="upfront_calibration", toolset="upfront",
                      schema=cal_schema, handler=handle_calibration)
