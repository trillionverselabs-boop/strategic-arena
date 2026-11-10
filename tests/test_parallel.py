"""Parties act concurrently within a round — the difference between a 30-minute
review and a few minutes. Prove both that it happens and that it stays correct."""

import json
import threading
import time

from upfront.models import Persona, Scenario
from upfront.simulation import run_simulation


class ConcurrencyProbe:
    """Fake model: sleeps a little, tracks how many calls overlap."""

    model = "probe"
    temperature = 0.6

    def __init__(self):
        self.active = 0
        self.peak = 0
        self.lock = threading.Lock()

    def complete(self, prompt):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        time.sleep(0.15)
        low = prompt.lower()
        try:
            with self.lock:
                self.active -= 1
        except Exception:
            pass
        if "stakeholder landscape" in low:
            return json.dumps({"personas": [
                {"name": f"Party {i}", "role": "user", "stance": 0.1 * i} for i in range(6)
            ], "relationships": []})
        return json.dumps({"stance_delta": 0.05, "action": "supports", "text": "ok"})


def _scenario(window="30m"):
    return Scenario(title="t", goal="adoption", window=window,
                    documents=[{"type": "decision", "content": "We are doing the thing."}])


def test_parties_act_at_the_same_time():
    probe = ConcurrencyProbe()
    personas = [Persona(name=f"Party {i}", role="user", stance=0.1 * i) for i in range(6)]
    result = run_simulation(_scenario(), personas, llm=probe)
    assert probe.peak > 1, "parties must act concurrently within a round"
    assert len(result.personas) == 6
    assert result.rounds == 3
    assert all(p.stance >= 0 for p in result.personas)


def test_still_works_with_a_single_party():
    probe = ConcurrencyProbe()
    result = run_simulation(_scenario(), [Persona(name="Only", role="user", stance=0.2)], llm=probe)
    assert len(result.personas) == 1
