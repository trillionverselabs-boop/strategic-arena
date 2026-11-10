# Upfront data contract — pydantic models shared by engine, tools, CLI, and API.
# These are the ONLY source of truth for input/output shapes.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── input ──────────────────────────────────────────────────────────────

class DocumentType(str, Enum):
    DECISION = "decision"      # the core proposal / plan
    EVIDENCE = "evidence"      # real data, quotes, links
    CONTEXT = "context"        # background the sim should assume


class Goal(str, Enum):
    ADOPTION = "adoption"      # "will people adopt this product / feature?"
    OPEN_WEIGHT = "open_weight"  # "should we open-weight this model?"
    DEPRECATION = "deprecation"  # "will a deprecation / change get pushback?"
    CAMPAIGN = "campaign"      # "will this campaign land?"


class Window(str, Enum):
    THIRTY_M = "30m"
    ONE_H = "1h"
    FOUR_H = "4h"
    SIX_H = "6h"
    TWELVE_H = "12h"
    TWENTY_FOUR_H = "24h"
    FORTY_EIGHT_H = "48h"

    @property
    def rounds(self) -> int:
        """More time = more rounds = more positions tested, more reaction cycles.

        30m is a sanity check (does anyone care?), 48h is the full read (coalitions
        form, positions harden, the veto player's alternative gets tested).
        """
        return {
            "30m": 3, "1h": 5, "4h": 8, "6h": 10,
            "12h": 12, "24h": 16, "48h": 20,
        }[self.value]

    @property
    def seconds(self) -> int:
        """Wall-clock length of the window — when the claims become scorable."""
        return {
            "30m": 30 * 60, "1h": 3600, "4h": 4 * 3600, "6h": 6 * 3600,
            "12h": 12 * 3600, "24h": 24 * 3600, "48h": 48 * 3600,
        }[self.value]


class Document(BaseModel):
    type: DocumentType
    content: str
    source: str = ""  # e.g. "evidence ¶2" — for provenance


class Persona(BaseModel):
    name: str
    role: str = "stakeholder"
    stance: float = Field(default=0.0, ge=-1.0, le=1.0)  # -1 against .. +1 for
    # Ability to block or materially change the outcome, 0..1. None = not assessed,
    # which is NOT the same as "cannot". The sea read refuses to print blue on an
    # unassessed field — see scoring.sea_state and tests/test_blue_earned.py.
    capacity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)     # grounded "why" — source-attributed


class Intervention(BaseModel):
    name: str
    description: str
    inject_at_round: int = Field(default=3, ge=1)


class Scenario(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    goal: Goal = Goal.ADOPTION
    documents: List[Document] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)  # fetched to text, then ingested
    window: Window = Window.TWENTY_FOUR_H
    model: str = "default"  # informational; sim always runs on the active ctx.llm model
    personas: List[Persona] = Field(default_factory=list)  # user overrides, or empty = auto-extract
    interventions: List[Intervention] = Field(default_factory=list)
    max_personas: int = Field(default=8, ge=3, le=16)
    temperature: float = Field(default=0.6, ge=0.0, le=1.0)

    @property
    def rounds(self) -> int:
        return self.window.rounds


# ── output ─────────────────────────────────────────────────────────────

class Event(BaseModel):
    round: int
    actor: str
    action: str       # e.g. "blocks", "supports", "shares", "waits", "intervention"
    text: str
    source: str = ""  # provenance: which input ¶ drove this action


class Snapshot(BaseModel):
    round: int
    stances: Dict[str, float]  # persona name -> stance
    # what was actually said this round. The live view leads with these: a
    # watcher needs words to read, not a dot that moved.
    events: List[Event] = Field(default_factory=list)


class SimulationResult(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    goal: Goal
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    window: str = "24h"   # the timeline the run was asked for; sets when claims are due
    rounds: int
    personas: List[Persona]
    events: List[Event] = Field(default_factory=list)
    snapshots: List[Snapshot] = Field(default_factory=list)
    friction: float = 0.0      # 0..100
    uncertainty: float = 0.0   # ± on friction, from input quality
    confidence: str = "low"    # low / medium / high
    blocker: Optional[Persona] = None    # the single player who can veto the move
    counter_moves: List[str] = Field(default_factory=list)  # the smarter move(s)
    camps: List[dict] = Field(default_factory=list)         # coalition clusters
    failure_modes: List[dict] = Field(default_factory=list)
    recommendation: str = ""                                # plain-language "so what do I do"
    provenance: List[str] = Field(default_factory=list)
    input_quality: Dict[str, object] = Field(default_factory=dict)
    interventions_shot: List[str] = Field(default_factory=list)
    sea: Dict[str, object] = Field(default_factory=dict)        # red / purple / blue read
    claims: List[dict] = Field(default_factory=list)            # frozen, scorable claims
    verified: Dict[str, object] = Field(default_factory=dict)   # human verdict + score
    degraded: bool = False                                      # a model call failed mid-run
    degraded_reason: str = ""
    llm_failures: int = 0                                       # failed act() calls
    # what ACTUALLY served the run, as reported by the host — the requested
    # model is not proof: a refused or unreachable override degrades to the
    # active model, and only the host knows which one answered.
    served_model: str = ""
    served_provider: str = ""
    model_fallback_note: str = ""

    @property
    def summary(self) -> str:
        blk = (f" Veto player: {self.blocker.name} (stance {self.blocker.stance:+.1f})."
               if self.blocker else " No veto player identified.")
        return (
            f"Friction {self.friction:.0f}/100 (±{self.uncertainty:.0f}, {self.confidence} confidence)."
            f"{blk} {len(self.events)} events over {self.rounds} rounds."
        )
