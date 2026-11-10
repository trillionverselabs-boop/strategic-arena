# Agents — generative agents (Stanford Smallville): memory stream + retrieval + reflection.
# Each stakeholder remembers what happened, retrieves the relevant bits, and acts.

from __future__ import annotations

import json
from typing import List

from .models import Persona


class StakeholderAgent:
    def __init__(self, persona: Persona):
        self.p = persona
        self.memory: List[dict] = []  # {text, importance, round}
        self.failures = 0             # failed act() calls — surfaced, never hidden

    # ── memory ────────────────────────────────────────────────────────
    def observe(self, text: str, importance: float = 0.5, rnd: int = 0) -> None:
        self.memory.append({"text": text, "importance": importance, "round": rnd})

    def retrieve(self, k: int = 3, rnd: int = 0) -> str:
        """Score by recency + importance (Smallville formula, simplified)."""
        if not self.memory:
            return ""
        def score(item):
            age = max(0, rnd - item["round"])
            return item["importance"] * (0.9 ** age)
        top = sorted(self.memory, key=score, reverse=True)[:k]
        return "; ".join(t["text"] for t in top)

    def reflect(self, llm, rnd: int) -> None:
        """Compress recent memories into one high-importance insight."""
        if len(self.memory) < 4:
            return
        recent = "; ".join(m["text"] for m in self.memory[-4:])
        try:
            out = llm.complete(
                f"You are {self.p.name} ({self.p.role}). Summarize what you're seeing "
                f"across recent events into a single insight (one sentence). Recent: {recent}"
            )
            insight = str(out).strip()
        except Exception:
            return
        if insight:
            self.observe(f"Insight: {insight}", importance=0.95, rnd=rnd)

    # ── action ────────────────────────────────────────────────────────
    def act(self, scenario_title: str, others_stances: dict, rnd: int, llm) -> dict:
        """Decide this round's move. Returns {stance_delta, action, text}."""
        context = self.retrieve(3, rnd)
        prompt = (
            f"You are {self.p.name}, a {self.p.role} reacting to the decision "
            f"'{scenario_title}'. Your current stance is {self.p.stance:+.1f} "
            f"(-1 = against, +1 = for). Relevant memories: {context or 'none'}. "
            f"Other stakeholders' stances: {others_stances}. "
            f"Decide your move this round. Respond with ONLY valid JSON: "
            f'{{"stance_delta": 0.0, "action": "supports|blocks|shares|waits", "text": "one sentence"}} '
            f"stance_delta in [-0.5, 0.5]. Stay consistent with your stance and reasons.\n"
            f"Write 'text' as something you would actually SAY in the room, in the first person "
            f"('I', 'we'), in your own voice — under 30 words, concrete, naming the "
            f"thing you need or object to. Never describe yourself in the third person "
            f"and never write 'X blocks ...' or 'X supports ...'. A person reading it "
            f"should hear a person, not a status line."
        )
        try:
            raw = llm.complete(prompt)
            data = _parse(raw)
            if data:
                delta = max(-0.5, min(0.5, float(data.get("stance_delta", 0.0))))
                return {
                    "stance_delta": delta,
                    "action": str(data.get("action", "waits")),
                    "text": str(data.get("text", "")),
                }
        except Exception:
            pass
        # No model, no opinion: hold still and count it. Never drift.
        self.failures += 1
        return {"stance_delta": 0.0, "action": "waits", "text": ""}


def _parse(raw) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    text = str(raw)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None
