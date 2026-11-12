import threading
import time

from upfront import engine
from upfront.models import Document, DocumentType, Intervention, Scenario
from fakes import SlowLLM


def test_injection_lands_mid_run():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    out = {}

    def go():
        out["res"] = engine.run_scenario_progress(sc, SlowLLM(), run_id="ab3ab3ab3ab3")

    t = threading.Thread(target=go)
    t.start()
    time.sleep(0.15)
    queued = engine.inject("ab3ab3ab3ab3", Intervention(name="Publish eval suite",
                                                description="Ship the evals first"))
    t.join(timeout=60)
    assert queued is True
    events = [e for e in out["res"].events if e.actor == "<god>"]
    assert events, "injected intervention must appear as a <god> event"
    assert "Publish eval suite" in events[0].text
