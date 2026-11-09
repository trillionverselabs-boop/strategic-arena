"""Replication manifest — what a run was made of, so it can be re-run and audited.

MASS requires a manifest per run (prompt, config, model, version) or the result
is not reproducible and therefore not checkable.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import List

from .ingestion import EXTRACT_PROMPT
from .models import Document, Scenario


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:12]


def _git_commit() -> str:
    """Short HEAD SHA read from .git directly — no subprocess.

    A plugin runs inside the host's isolation boundary; spawning `git` just to stamp a
    commit is unnecessary surface for a value we can read from two small files.
    """
    root = Path(__file__).resolve().parent
    try:
        head = (root / ".git" / "HEAD").read_text().strip()
        if head.startswith("ref: "):
            ref = head[5:].strip()
            ref_file = root / ".git" / ref
            if ref_file.exists():
                return ref_file.read_text().strip()[:12] or "unknown"
            packed = root / ".git" / "packed-refs"
            if packed.exists():
                for line in packed.read_text().splitlines():
                    if line.startswith(("#", "^")):
                        continue
                    parts = line.split()
                    if len(parts) == 2 and parts[1] == ref:
                        return parts[0][:12]
            return "unknown"
        return head[:12] or "unknown"
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
