"""Shared fake LLMs for tests. No network, no credentials."""

import json


class FakeLLM:
    model = "fake"
    temperature = 0.6

    def __init__(self, stance=-0.7):
        self.stance = stance

    def complete(self, prompt):
        low = prompt.lower()
        if "stakeholder landscape" in low or "you are extracting" in low:
            return json.dumps({
                "personas": [
                    {"name": "Enterprise IT", "role": "blocker", "stance": self.stance,
                     "reason": "Cannot route inference through an external API for compliance"},
                    {"name": "The Community", "role": "champion", "stance": 0.8,
                     "reason": "Open-weight downloads tripled"},
                    {"name": "Regulators", "role": "regulator", "stance": -0.3,
                     "reason": "Wants to see the eval suite"},
                ],
                "relationships": [["Enterprise IT", "The Community", "opposes"]],
            })
        if "decide your move" in low:
            return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})
        return json.dumps({"claims": [{"claim": "61% of CIOs cannot route externally",
                                       "source": "Q2 survey of 400 CIOs"}]})


class Boom:
    """Every call fails."""

    model = "fake"
    temperature = 0.6

    def complete(self, prompt):
        raise RuntimeError("provider down")


class EmptyExtraction:
    """Model answers, but finds nobody. Valid JSON, zero personas."""

    model = "fake"
    temperature = 0.6

    def complete(self, prompt):
        return '{"personas": [], "relationships": []}'


class HalfDead:
    """Extraction works; every later call fails."""

    model = "fake"
    temperature = 0.6

    def __init__(self):
        self.n = 0

    def complete(self, prompt):
        self.n += 1
        if self.n == 1:
            return json.dumps({"personas": [
                {"name": "Eng", "role": "blocker", "stance": -0.6, "reason": "compliance"}],
                "relationships": []})
        raise RuntimeError("down")


class SlowLLM(FakeLLM):
    def __init__(self):
        super().__init__()
        import time
        self._t = time

    def complete(self, prompt):
        self._t.sleep(0.02)
        return super().complete(prompt)


class InterventionAware(FakeLLM):
    """Agent calls that mention an intervention move the stance up."""

    def complete(self, prompt):
        if "intervention" in prompt.lower() or "publish eval" in prompt.lower():
            return json.dumps({"stance_delta": 0.4, "action": "supports",
                               "text": "the evals convince us"})
        return super().complete(prompt)
