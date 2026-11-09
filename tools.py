# Tool registration — registers upfront_run/status/report/history as agent tools.
# Handlers are thin: build a Scenario, run the engine, return JSON.

from __future__ import annotations

import json
import threading

from . import engine
from .llm_adapter import LlmAdapter
from .models import Scenario


def _scenario_from(params: dict) -> Scenario:
    docs = params.get("documents", [])
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


def register_tools(ctx) -> None:
    # ── upfront_run ──────────────────────────────────────────────────
    run_schema = {
        "name": "upfront_run",
        "description": (
            "Run a stakeholder reaction simulation on a decision. Give a title and at "
            "least one document (type=decision, content=text). Optionally add evidence "
            "documents for better grounding, a goal (adoption/open_weight/deprecation/campaign), "
            "and a window (6h/12h/24h/48h). Returns a run with a friction score, a "
            "blocker (who will fight you), counter-moves, and full provenance. Runs "
            "synchronously and returns the finished result. Use upfront_history to look "
            "back at past runs and verify them."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title for the decision."},
                "goal": {"type": "string", "enum": ["adoption", "open_weight", "deprecation", "campaign"]},
                "window": {"type": "string", "enum": ["6h", "12h", "24h", "48h"]},
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
            },
            "required": ["title", "documents"],
        },
    }

    def handle_run(params, **kwargs):
        llm = LlmAdapter(ctx.llm, temperature=params.get("temperature", 0.6))
        scenario = _scenario_from(params)
        result = engine.run_scenario(scenario, llm)
        return json.dumps({
            "run_id": result.run_id, "title": result.title,
            "friction": result.friction, "uncertainty": result.uncertainty,
            "confidence": result.confidence, "blocker": result.blocker.name if result.blocker else None,
            "counter_moves": result.counter_moves, "summary": result.summary,
            "personas": [{"name": p.name, "stance": round(p.stance, 2)} for p in result.personas],
        })

    ctx.register_tool(name="upfront_run", toolset="upfront", schema=run_schema, handler=handle_run)

    # ── upfront_status / upfront_report / upfront_history ────────────
    status_schema = {
        "name": "upfront_status",
        "description": "Check the status of a simulation run (running/done + progress).",
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
        "description": "List past simulation runs (most recent first) so you can verify results over time.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "default": 20}}},
    }

    def handle_history(params, **kwargs):
        from . import reporting
        return json.dumps(reporting.list_runs(params.get("limit", 20)))

    ctx.register_tool(name="upfront_history", toolset="upfront", schema=history_schema, handler=handle_history)
