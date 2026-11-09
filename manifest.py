"""Replication manifest — what a run was made of, so it can be re-run and audited.

MASS requires a manifest per run (prompt, config, model, version) or the result
is not reproducible and therefore not checkable.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import List

from .ingestion import EXTRACT_PROMPT
from .models import Document, Scenario


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:12]


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def build_manifest(scenario: Scenario, documents: List[Document], model: str,
                   temperature: float) -> dict:
    return {
        "type": "manifest",
        "run_title": scenario.title,
        "goal": scenario.goal.value,
        "window": scenario.window.value,
        "rounds": scenario.rounds,
        "model": model,
        "temperature": temperature,
        "extract_prompt_sha": _sha(EXTRACT_PROMPT),
        "documents": [
            {"type": d.type.value, "source": d.source, "sha": _sha(d.content),
             "chars": len(d.content)}
            for d in documents
        ],
        "max_personas": scenario.max_personas,
        "code_commit": _git_commit(),
        "python": sys.version.split()[0],
        "plugin_version": "0.2.0",
    }
