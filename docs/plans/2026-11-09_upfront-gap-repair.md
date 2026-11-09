# Plan — Upfront: restore what the last test lost, and fix the bugs it exposed

**Repo (only working copy):** `/home/lisacore/work/upfront-test` → `https://github.com/trillionverselabs-boop/upfront-test` (private)
**Backup (frozen, do not edit):** `https://github.com/trillionverselabs-boop/Upfront-Plugin-Original`
**Base commit:** `98a4e43` (state the "Pt2. Grill Me docs" session left behind)

---

## Goal

Ship **strategic-response review**: give the tool a decision, it maps the players who can veto it, their coalitions, your best response, and a contested-landscape read — then scores itself against reality so its track record is measurable. A run must either produce a grounded result or fail loudly; the mid-run injection and the verify-later loop must actually work.

## Positioning — what this is (and is not)

**Not a predictor. A game-theoretic review of the response to a move.**

The papers in our skill set (MASS, OASIS, Generative Agents, GraphRAG, CAMEL) are explicit that LLM-driven simulation produces *pre-experimental evidence* — mechanism rehearsal, counterfactual contrast, risk identification. MASS's own boundary rule: "Do not claim it predicts real outcomes." So the product is framed as an **adversarial response review**, not a forecast:

| Game concept | In this product |
|---|---|
| Your move | the decision document |
| Players | extracted stakeholders, each with interest, information, and **veto power** |
| Coalition structure | camps (stance + oppose/support edges) |
| Veto player | the blocker — the player without whom your move does not pass |
| Best response | counter-moves |
| Perturbation / counterfactual | mid-run injection (same game, one variable changed) |
| Payoff proxy | stance delta → friction delta |
| Stable outcome (not "equilibrium") | repeated runs agreeing in direction (MASS: directional consistency) |
| Market contestability | red / purple / blue ocean read |
| Track record | calibration ledger — every frozen claim scored against what happened |

Two rules that keep it honest and keep it valuable:
1. **Every run publishes falsifiable claims** ("Enterprise IT, stance −0.70, will be the binding constraint in 48h"), each with the evidence span that produced it. No claim, no run.
2. **Every claim gets scored.** The value over time is not any single report; it is that after 20 reviewed decisions you can show a hit rate and a calibration curve. That is what makes this an instrument instead of a story.

**Sea state (red / purple / blue).** A landscape-level read, deliberately a *different* colour scale from per-stakeholder stance so they never collide: node stance stays red/amber/green; the run carries a **Sea state** chip — **Red ocean** (contested, veto players aligned against), **Purple ocean** (contested middle — the normal case; a real fight with winnable ground), **Blue ocean** (uncontested: no veto player, low friction). Purple is the midpoint because most real decisions are neither a bloodbath nor empty water, and telling those apart is the insight.

---


---

## Current context / assumptions

- Python package is the plugin root itself (`/home/lisacore/work/upfront-test` is imported as package `upfront`; tests add the **parent** dir to `sys.path`).
- Agent half: `plugin.yaml`, `__init__.py` (`register(ctx)`), `tools.py`. Desktop half: `desktop/plugin.js` (uncompiled ESM, only `@hermes/plugin-sdk`, `react`, `react/jsx-runtime` — **no JSX syntax allowed**). Backend: `dashboard/plugin_api.py` (FastAPI router at `/api/plugins/upfront/`).
- **Testing rule for this work:** do **not** leave the plugin installed in the Hermes backend. All development verification runs through `pytest` with a fake LLM and a throwaway `$HERMES_HOME`. If any task requires an installed copy, the task ends with the full uninstall drill in Phase 5.2. The real acceptance test is the **desktop install** the user performs at the end.
- `hermes plugins install` builds an editable install inside a managed venv; those linger. Cleanup commands are in Phase 5.2.
- Every command below runs in `/home/lisacore/work/upfront-test`.

---

## Findings — what the current code is missing (evidence)

The last real run reported **`friction 0` / `blocker: Stakeholder 1`** on the Arete preset. That is not a bad simulation — it is the *dead-LLM signature*, reproduced arithmetically:

| # | Defect | Where | Consequence |
|---|---|---|---|
| 1 | **Silent extraction failure → fake personas.** `extract_personas` returns `([], [])` on any exception, and the engine substitutes `Stakeholder 1..3`. | `engine.py:54-55`, `ingestion.py:48-54` | The run looks successful but nobody was ever extracted from the documents. |
| 2 | **Dead-LLM stance drift.** `act()` fallback nudges `+0.05/round` when stance ≥ 0. | `agents.py:72-74` | 20 rounds → **all personas +1.00**, friction `(1−1)/2·70 = 0`. Verified: `fallback+dead-LLM after 20 rounds → [1.0,1.0,1.0], friction = 0.0`. |
| 3 | **`find_blocker` has no threshold** — it returns the minimum stance even when everyone is positive. | `scoring.py:51-54` | Report prints "blocker: Stakeholder 1 (+1.00)". Nonsense on its face. |
| 4 | **Every run is persisted twice.** Engine writes `runs/<engine_run_id>/`, then `plugin_api` writes a second `runs/<http_run_id>/meta.json`. | `engine.py:116`, `dashboard/plugin_api.py:89-96` | "Previous runs" doubles, half the entries have no report. |
| 5 | **God-mode injection is unreachable.** `Intervention` exists and `simulation.py:30-36` injects at a round, but no UI control, no `/inject` endpoint, and the tool schema omits `interventions` (`tools.py:47-83` reads a key the model can never send). | `models.py:53-56`, `simulation.py:30-36`, `tools.py:26-30` | The single biggest demo moment from the original plan is dark. |
| 6 | **The "living graph" has no edges while running.** In-progress render passes `edges: []`. | `desktop/plugin.js:186-191` | It is a row of coloured dots — "watch the graph react" reads as nothing happening. |
| 7 | **Verify-tomorrow is write-only.** `log.jsonl` freezes the prediction, but there is no way to record what actually happened. | `reporting.py:204-218` | The "checkable prediction, not a story" claim cannot be exercised. |
| 8 | **Data path is not profile-safe.** Hardcoded `Path.home()/".hermes"/"upfront"` in three files. | `engine.py:14`, `reporting.py:13`, `plugin_api.py:89-91` | Writes to the wrong home under profiles (violates Hermes invariant), and is why run history is tied to one install location. |
| 9 | **Two desktop load paths + no version marker.** The app reads `$HERMES_HOME/plugins/upfront/desktop/plugin.js` *and* `~/.hermes/desktop-plugins/upfront/plugin.js`; the stale one wins and nothing on screen says which loaded. | `desktop/plugin.js` (no version), session 20261108_215445_c75282 msgs 2104-2126 | "The UI didn't update" was undiagnosable for ~40 minutes. |
| 10 | **A repo URL ingests GitHub's page chrome**, not the README. | `fetch.py:62-65` | URL-only runs are grounded in "Skip to content / Sign in / file listing". |
| 11 | **Catalog submission is blocked:** no `LICENSE`, wrong MASS attribution (`Hu & Shen`), `plugin.yaml` has no capabilities/desktop declaration, no catalog entry. | `README.md:21`, `failure_modes.py:1`, `plugin.yaml:1-9` | Cannot be admitted to the catalog as-is. |
| 12 | **Report is dumped as raw markdown** into a `<pre>` — asterisks and all. | `desktop/plugin.js:194-200` | Kills the "pops for judges" quality bar. |
| 13 | **Nothing is checkable over time.** No replication manifest (no seed/config/prompt hash/model/commit recorded), no claim extraction (GraphRAG's claim-based validation is absent), no calibration record, and "verify" is a human thumbs-up with no scoring. | `grep -n "seed\|replication\|manifest" *.py` → only camp-clustering locals; `log.jsonl` (`reporting.py:204-218`) holds snapshots only | The product cannot accumulate a track record, so it cannot become more than a demo. This is the value gap. |

---

## Architecture / proposed approach

Three changes in order: **(a)** make failure impossible to hide (typed errors, no fake personas, a degraded banner, profile-safe paths, one persisted run); **(b)** light up the two features the plan promised but never wired — a live `/inject` queue the simulation drains at rumtime, and a `/verify` write-back on the frozen log; **(c)** make the desktop half honest and pretty — a visible build stamp, edges in the live graph, real markdown rendering, and one documented copy on disk.

---

## Phase 0 — One working copy (5 min, mutating)

**0.1 Confirm the repo has everything, then delete the redundancies.**

```bash
cd /home/lisacore/work/upfront-test
git rev-parse origin/main          # expect: 98a4e43fa8bc67286a78c002928df2865437499d
git status -sb                     # expect: ## main...origin/main   (clean)
md5sum desktop/plugin.js           # expect: dd86b388ba40534b14bd15208753f294

git -C /home/lisacore/work/upfront log -1 --pretty=%h                      # expect 98a4e43
git -C /home/lisacore/work/upfront-grill-docs-state log -1 --pretty=%h     # expect 98a4e43
diff -rq --exclude=.git /home/lisacore/work/upfront /home/lisacore/work/upfront-test   # expect: no output (identical)
```

Only when both commands print `98a4e43` and the diff is empty:

```bash
cd /home/lisacore/work/upfront-test
git worktree remove --force /home/lisacore/work/upfront-grill-docs-state
# then delete /home/lisacore/work/upfront by hand, once it holds no tracked files
ls -d /home/lisacore/work/*/        # expect exactly one line: /home/lisacore/work/upfront-test/
```

---

## Phase 1 — P0: a run must never lie

### 1.1 Test scaffolding with a throwaway home

**File:** `tests/conftest.py` (new)

```python
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO.parent))
sys.path.insert(0, str(REPO))


@pytest.fixture(autouse=True)
def tmp_hermes_home(tmp_path, monkeypatch):
    """Never let a test write into the real ~/.hermes."""
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home
```

Verify: `python -m pytest tests/ -q` → tests still run (they may fail; the point is no import errors).

Commit: `test: throwaway HERMES_HOME fixture`

### 1.2 Profile-safe data root

**File:** `paths.py` (new)

```python
"""Every file this plugin writes lives under the ACTIVE Hermes home."""

from __future__ import annotations

import os
from pathlib import Path


def data_root() -> Path:
    """$HERMES_HOME/upfront, falling back to ~/.hermes/upfront outside Hermes."""
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home) / "upfront"


def runs_dir() -> Path:
    return data_root() / "runs"


def graph_path() -> Path:
    return data_root() / "graph.json"
```

**File:** `tests/test_paths.py` (new)

```python
from pathlib import Path

from upfront import paths


def test_data_root_follows_hermes_home(tmp_hermes_home):
    assert paths.data_root() == tmp_hermes_home / "upfront"
    assert paths.graph_path() == tmp_hermes_home / "upfront" / "graph.json"
```

Run: `python -m pytest tests/test_paths.py -q` → **fails** (`ModuleNotFoundError` / AttributeError).
Then implement `paths.py`, re-run → **1 passed**.
Commit: `feat(paths): profile-safe data root`

### 1.3 Point the three hardcoded writers at `data_root()`

**File:** `engine.py` — replace line 14:

```python
from .paths import graph_path
...
GRAPH_PATH = graph_path()   # keep module-level name; it is imported by plugin_api
```

**File:** `reporting.py` — replace line 13 and every `RUNS_DIR` use:

```python
from .paths import runs_dir
...
def _run_dir(run_id: str) -> Path:
    return runs_dir() / run_id
```

In `list_runs`, replace `if not RUNS_DIR.exists()` with:

```python
    root = runs_dir()
    if not root.exists():
        return []
```
and `for d in sorted(RUNS_DIR.iterdir(), ...)` → `for d in sorted(root.iterdir(), reverse=True):`.

**File:** `dashboard/plugin_api.py` — replace lines 89-96 with nothing (see 1.8).

Verify: `python -m pytest tests/ -q` → no collection errors; `grep -rn 'Path.home() / ".hermes"' --include=*.py .` → **no output**.
Commit: `fix(paths): write under $HERMES_HOME, not ~/.hermes`

### 1.4 Extraction failure must be distinguishable from "no stakeholders"

**File:** `ingestion.py` — change the return contract to `None` on transport/parse failure:

```python
def extract_personas(
    documents: List[Document], llm, max_personas: int = 8
) -> Tuple[List[Persona], List[Tuple[str, str, str]]] | None:
    """Returns (personas, relationships), or None if the model call failed."""
    prompt = EXTRACT_PROMPT.format(max_personas=max_personas, docs=_docs_block(documents))
    try:
        raw = llm.complete(prompt)
    except Exception:
        return None            # <- was: return [], []
    parsed = _parse_json(raw)
    if parsed is None:
        return None            # <- was: return [], []
    ...
```

**File:** `tests/test_ingestion.py` (new)

```python
from upfront import ingestion
from upfront.models import Document, DocumentType


class Boom:
    def complete(self, prompt):
        raise RuntimeError("provider down")


class Empty:
    def complete(self, prompt):
        return '{"personas": [], "relationships": []}'


def test_transport_failure_is_none():
    docs = [Document(type=DocumentType.DECISION, content="Ship it")]
    assert ingestion.extract_personas(docs, Boom()) is None


def test_genuinely_empty_is_not_none():
    docs = [Document(type=DocumentType.DECISION, content="Ship it")]
    assert ingestion.extract_personas(docs, Empty()) == ([], [])
```

Run: `python -m pytest tests/test_ingestion.py -q` → 1 fails, 1 passes → implement → **2 passed**.
Commit: `fix(ingestion): signal model failure instead of returning empty`

### 1.5 The engine refuses to invent stakeholders

**File:** `engine.py` — add near the top:

```python
class SimulationError(RuntimeError):
    """A run that cannot produce a trustworthy result. Surfaced to the user as-is."""
```

Replace lines 47-55 with:

```python
    personas: List[Persona] = list(scenario.personas)
    relationships: List[tuple] = []
    if not personas:
        extracted = ingestion.extract_personas(scenario.documents, llm, scenario.max_personas)
        if extracted is None:
            raise SimulationError(
                "The model call failed, so no stakeholders could be read from your "
                "documents. Nothing was simulated — check the model is reachable and re-run."
            )
        personas, relationships = extracted
        if not personas:
            raise SimulationError(
                "The model read your documents but found no stakeholders in them. "
                "Add a decision document that names who is affected, or supply personas."
            )
```

**File:** `tests/test_engine_guards.py` (new)

```python
import pytest

from upfront import engine
from upfront.models import Document, DocumentType, Scenario


class Boom:
    def complete(self, prompt):
        raise RuntimeError("provider down")


class Empty:
    def complete(self, prompt):
        return '{"personas": [], "relationships": []}'


def _scenario():
    return Scenario(title="t", documents=[Document(type=DocumentType.DECISION, content="Ship it")])


def test_model_failure_raises(tmp_hermes_home):
    with pytest.raises(engine.SimulationError, match="model call failed"):
        engine.run_scenario(_scenario(), Boom())


def test_zero_personas_raises(tmp_hermes_home):
    with pytest.raises(engine.SimulationError, match="found no stakeholders"):
        engine.run_scenario(_scenario(), Empty())
```

Run: `python -m pytest tests/test_engine_guards.py -q` → **2 failed** → implement → **2 passed**.
Commit: `fix(engine): raise instead of fabricating Stakeholder 1..3`

### 1.6 Agents may not drift on a dead model

**File:** `agents.py` — in `__init__` add `self.failures = 0`; replace lines 70-74 with:

```python
        # No model, no opinion: hold still and count it. Never drift.
        self.failures += 1
        return {"stance_delta": 0.0, "action": "waits", "text": ""}
```

**File:** `tests/test_agents.py` (new)

```python
from upfront.agents import StakeholderAgent
from upfront.models import Persona


class Boom:
    def complete(self, prompt):
        raise RuntimeError("down")


def test_dead_model_holds_stance_and_counts():
    a = StakeholderAgent(Persona(name="Eng", stance=0.2))
    move = a.act("t", {}, 1, Boom())
    assert move["stance_delta"] == 0.0
    assert a.p.stance == 0.2
    assert a.failures == 1
```

Run → fails (drift `0.05`) → implement → **1 passed**.
Commit: `fix(agents): no stance drift when the model is unreachable`

### 1.7 A blocker must actually be a blocker

**File:** `scoring.py` — replace `find_blocker`:

```python
BLOCKER_THRESHOLD = -0.3


def find_blocker(personas: List[Persona]) -> Persona | None:
    """The worst stakeholder — or None when nobody is meaningfully against it."""
    if not personas:
        return None
    worst = min(personas, key=lambda p: p.stance)
    return worst if worst.stance < BLOCKER_THRESHOLD else None
```

**File:** `tests/test_scoring.py` (new)

```python
from upfront.models import Persona
from upfront.scoring import find_blocker


def test_no_blocker_when_everyone_is_positive():
    assert find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=0.8)]) is None


def test_blocker_when_someone_opposes():
    b = find_blocker([Persona(name="a", stance=1.0), Persona(name="b", stance=-0.7)])
    assert b is not None and b.name == "b"
```

Run → one fails → implement → **2 passed**.
Commit: `fix(scoring): blocker requires stance < -0.3`

### 1.8 One run, one record

**File:** `engine.py` — signature and run-id control:

```python
def run_scenario_progress(scenario: Scenario, llm, on_round: Callable | None = None,
                          run_id: str | None = None) -> SimulationResult:
    key = run_id or scenario.title
    _emit(key, "running", 0, scenario.rounds)
```
then use `key` in the three `_emit(...)` calls inside this function, and after `result = simulation.run_simulation(...)`:

```python
    if run_id:
        result.run_id = run_id
```

**File:** `dashboard/plugin_api.py` — `_work()` becomes:

```python
    def _work():
        try:
            def _on_round(snap):
                engine._emit(run_id, "running", snap.round, scenario.rounds,
                             {k: round(v, 3) for k, v in (snap.stances or {}).items()})
            result = engine.run_scenario_progress(scenario, _llm(), on_round=_on_round, run_id=run_id)
            engine._emit(run_id, "done", result.rounds, result.rounds,
                         {p.name: round(p.stance, 3) for p in result.personas})
        except Exception as exc:
            engine._emit(run_id, "failed", 0, scenario.rounds)
            engine._PROGRESS[run_id]["error"] = str(exc)
```

(delete the `mkdir` + `meta.json` block entirely — the engine already persisted this run under `run_id`.)

**File:** `tests/test_single_run.py` (new)

```python
import json

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario


class FakeLLM:
    def complete(self, prompt):
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [
                {"name": "Eng", "role": "blocker", "stance": -0.6, "reason": "no external API"},
                {"name": "Community", "role": "champion", "stance": 0.7, "reason": "wants weights"},
            ], "relationships": [["Eng", "Community", "opposes"]]})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_one_run_one_record(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Open-weight it")])
    engine.run_scenario_progress(sc, FakeLLM(), run_id="abc123")
    runs = reporting.list_runs(10)
    assert len(runs) == 1
    assert runs[0]["run_id"] == "abc123"
    assert (reporting.runs_dir() / "abc123" / "report.md").exists()
```

Run → fails → implement → **1 passed**.
Commit: `fix(engine): one persisted record per run`

### 1.9 Say it out loud when the run is degraded

**File:** `models.py` — add to `SimulationResult`:

```python
    degraded: bool = False
    degraded_reason: str = ""
    verified: Dict[str, object] = Field(default_factory=dict)
```

**File:** `engine.py` — after the simulation, before scoring:

```python
    total_calls = max(1, scenario.rounds * len(result.personas))
    failures = sum(getattr(a, "failures", 0) for a in agents) if (agents := locals().get("agents")) else 0
```
Because `agents` live inside `simulation.run_simulation`, expose them instead: add to `simulation.py` `result.llm_failures = sum(a.failures for a in agents)` (new field `llm_failures: int = 0` in `SimulationResult`), then in `engine.py`:

```python
    if result.llm_failures:
        result.degraded = True
        result.degraded_reason = (
            f"{result.llm_failures} of {total_calls} model calls failed during the run"
        )
        result.confidence = "low"
```

**File:** `reporting.py` — immediately after the friction line in `write_report` and `write_full_report`:

```python
    if result.degraded:
        lines.append(f"> ⚠️ **DEGRADED RUN — do not trust this.** {result.degraded_reason}. "
                     "Stances held still where the model failed; re-run before deciding anything.")
        lines.append("")
```

**File:** `tests/test_degraded.py` (new)

```python
import json

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario


class HalfDead:
    """Extraction works, then every act() call fails."""
    def __init__(self):
        self.n = 0

    def complete(self, prompt):
        self.n += 1
        if self.n == 1:
            return json.dumps({"personas": [
                {"name": "Eng", "role": "blocker", "stance": -0.6, "reason": "compliance"}],
                "relationships": []})
        raise RuntimeError("down")


def test_degraded_run_is_flagged(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    res = engine.run_scenario(sc, HalfDead())
    assert res.degraded is True
    assert res.confidence == "low"
    assert "DEGRADED RUN" in reporting.load_run(res.run_id)["report"]
```

Run → fails → implement → **1 passed**.
Commit: `feat(engine): flag degraded runs in the report`

### 1.10 Keep the existing contract green

`tests/test_endtoend.py` asserts `friction > 0` and `blocker is not None` with its FakeLLM — both still hold. Run the full suite:

```bash
python -m pytest tests/ -q
```
Expected: all pass (excluding `test_real_run.py`'s manual `main()`, which is not a pytest test).

Commit: `test: full suite green after P0`

---

## Phase 2 — P0/P1: light up injection and verification

### 2.1 A live injection queue the simulation drains

**File:** `simulation.py` — signature:

```python
def run_simulation(scenario, personas, events_out=None, on_round=None, llm=None,
                   injection_queue: list | None = None) -> SimulationResult:
```
and inside the round loop, **before** agents act:

```python
        while injection_queue:
            iv = injection_queue.pop(0)
            for a in agents:
                a.observe(f"Intervention: {iv.name} — {iv.description}", 0.95, rnd)
            result_events.append(
                Event(round=rnd, actor="<god>", action="intervention",
                      text=f"{iv.name}: {iv.description}")
            )
```

**File:** `engine.py` — module level:

```python
_INJECT: Dict[str, list] = {}
```

in `run_scenario_progress`, before `simulation.run_simulation`:

```python
    key = run_id or scenario.title
    _INJECT[key] = []
```
pass `injection_queue=_INJECT[key]`, and in a `finally:` after the sim:

```python
    finally:
        _INJECT.pop(key, None)
```

plus the public hook:

```python
def inject(run_id: str, intervention) -> bool:
    """Queue a mid-run intervention. False when the run is not live."""
    with _LOCK:
        q = _INJECT.get(run_id)
        if q is None:
            return False
        q.append(intervention)
        return True
```

**File:** `tests/test_injection.py` (new)

```python
import json, threading, time

from upfront import engine
from upfront.models import Document, DocumentType, Intervention, Scenario


class SlowLLM:
    def complete(self, prompt):
        time.sleep(0.02)
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [
                {"name": "Eng", "role": "blocker", "stance": -0.6, "reason": "compliance"},
                {"name": "Community", "role": "champion", "stance": 0.5, "reason": "wants weights"},
            ], "relationships": []})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_injection_lands_mid_run(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    out = {}

    def go():
        out["res"] = engine.run_scenario_progress(sc, SlowLLM(), run_id="inj1")

    t = threading.Thread(target=go); t.start()
    time.sleep(0.15)
    assert engine.inject("inj1", Intervention(name="Publish eval suite", description="Ship the evals first")) is True
    t.join(timeout=30)
    events = [e for e in out["res"].events if e.actor == "<god>"]
    assert events, "injected intervention must appear as a <god> event"
    assert "Publish eval suite" in events[0].text
```

Run → fails (`TypeError: unexpected keyword`) → implement → **1 passed**.
Commit: `feat(sim): drain a live intervention queue mid-run`

### 2.2 Expose injection over HTTP

**File:** `dashboard/plugin_api.py` — add:

```python
@router.post("/inject/{run_id}")
async def inject(run_id: str, body: dict):
    iv = Intervention(
        name=body.get("name", "Counter-move"),
        description=body.get("description", ""),
        inject_at_round=1,  # queue position wins; round is informational here
    )
    if not iv.description.strip():
        raise HTTPException(status_code=400, detail="description required")
    ok = engine.inject(run_id, iv)
    return {"queued": ok, "run_id": run_id}
```

Manual check (no install needed):

```bash
python -c "
import sys; sys.path[:0]=['/home/lisacore/work','/home/lisacore/work/upfront-test']
import importlib.util as u
s=u.spec_from_file_location('plugin_api','dashboard/plugin_api.py'); m=u.module_from_spec(s); s.loader.exec_module(m)
print([r.path for r in m.router.routes if 'inject' in r.path])
"
```
Expected: `['/inject/{run_id}']`.
Commit: `feat(api): POST /inject/{run_id}`

### 2.3 Let the agent inject too

**File:** `tools.py` — inside `run_schema["parameters"]["properties"]` add:

```python
                "interventions": {
                    "type": "array",
                    "description": "Mid-run counter-moves to inject (the god-mode move: change one thing mid-simulation and watch the graph bend).",
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
```

**File:** `tests/test_tools_schema.py` (new)

```python
from upfront.tools import register_tools


class Ctx:
    def __init__(self):
        self.schemas = {}

    def register_tool(self, name, toolset, schema, handler):
        self.schemas[name] = schema


def test_interventions_are_offered_to_the_model():
    c = Ctx(); register_tools(c)
    props = c.schemas["upfront_run"]["parameters"]["properties"]
    assert "interventions" in props
    assert "urls" in props
```

Run → fails → implement → **1 passed**.
Commit: `feat(tools): expose interventions on upfront_run`

### 2.4 Record the verdict on a frozen prediction

**File:** `reporting.py` — add:

```python
def mark_verified(run_id: str, verdict: str, note: str = "") -> dict:
    """Write the real-world outcome onto a frozen prediction. verdict: right|partial|wrong."""
    if verdict not in ("right", "partial", "wrong"):
        raise ValueError("verdict must be right|partial|wrong")
    d = _run_dir(run_id)
    meta_path = d / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(run_id)
    meta = json.loads(meta_path.read_text())
    meta["verified"] = {
        "verdict": verdict,
        "note": note,
        "at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta["verified"]
```

**File:** `dashboard/plugin_api.py` — add:

```python
@router.post("/verify/{run_id}")
async def verify(run_id: str, body: dict):
    try:
        return reporting.mark_verified(run_id, body.get("verdict", ""), body.get("note", ""))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
```

**File:** `tests/test_verify.py` (new)

```python
import json, pytest

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario


class FakeLLM:
    def complete(self, prompt):
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [{"name": "Eng", "role": "blocker",
                                             "stance": -0.6, "reason": "compliance"}],
                               "relationships": []})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_verdict_is_persisted(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    res = engine.run_scenario(sc, FakeLLM())
    reporting.mark_verified(res.run_id, "right", "Eng did block in review")
    meta = json.loads((reporting.runs_dir() / res.run_id / "meta.json").read_text())
    assert meta["verified"]["verdict"] == "right"


def test_bad_verdict_rejected(tmp_hermes_home):
    with pytest.raises(ValueError):
        reporting.mark_verified("nope", "maybe")
```

Run → fails → implement → **2 passed**.
Commit: `feat(reporting): record a verification verdict on a run`

### 2.5 Desktop: inject + verify + build stamp + edges

**File:** `desktop/plugin.js` — four edits, no JSX:

1. Top of file, after imports:

```javascript
const BUILD = '0.2.0 · gapfix'   // bump on every UI change — this is how you know the app reloaded
```

2. In `UpfrontPage`, add state next to `history`:

```javascript
  const [injectText, setInjectText] = React.useState('')
```

3. Inside the "Simulation in progress" card (after the progress bar), add the god-mode control:

```javascript
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx('input', {
            className: 'flex-1 rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
            placeholder: 'Inject a counter-move mid-run — e.g. "Publish the eval suite first"',
            value: injectText, onChange: e => setInjectText(e.target.value),
          }),
          jsx('button', {
            type: 'button',
            className: 'rounded bg-(--ui-accent) px-3 py-1 text-sm text-white disabled:opacity-50',
            disabled: !injectText.trim(),
            onClick: async () => {
              haptic('tap')
              await ctx.rest(`/inject/${running.runId}`, {
                method: 'POST',
                body: { name: 'Counter-move', description: injectText },
              }).catch(() => {})
              setInjectText('')
            },
            children: 'Inject ⚡',
          }),
        ]}),
```

4. Pass real edges to the live graph. Replace the `React.useMemo` block with a version that reuses the last known graph edges:

```javascript
        React.useMemo(() => {
          const nodes = Object.entries(running.stances || {}).map(([name, stance]) => ({ id: name, name, stance }))
          if (!nodes.length) return null
          const edges = (result?.graph?.edges) || []
          return jsx(GraphSvg, { graph: { nodes, edges } })
        }, [running.stances, result]),
```

5. In the header, replace the gateway line with:

```javascript
        jsx('div', { className: 'text-xs text-(--ui-text-tertiary)', children: `gateway: ${gateway} · build ${BUILD}` }),
```

6. In "Previous runs", append the verify buttons to each row's children (replace the `children:` string with a fragment):

```javascript
                children: jsxs('span', { className: 'flex items-center gap-2', children: [
                  jsx('span', { children: `${h.title} — friction ${h.friction ?? '—'} — ${h.blocker ? 'blocker: ' + h.blocker : 'no blocker'}` }),
                  ...['right', 'partial', 'wrong'].map(v => jsx('button', {
                    key: v, type: 'button',
                    className: 'rounded border border-(--ui-border) px-1 text-xs',
                    onClick: async (ev) => {
                      ev.stopPropagation()
                      await ctx.rest(`/verify/${h.run_id}`, { method: 'POST', body: { verdict: v } }).catch(() => {})
                      ctx.rest('/history').then(setHistory).catch(() => {})
                    },
                    children: h.verified?.verdict === v ? `✓ ${v}` : v,
                  })),
                ]}),
```

**Verify (static, no app restart):**

```bash
node --check desktop/plugin.js && echo "syntax OK"
grep -c "Inject ⚡" desktop/plugin.js     # expect 1
grep -c "BUILD" desktop/plugin.js         # expect >= 3
```
Commit: `feat(desktop): mid-run inject control, verify buttons, build stamp, live edges`

### 2.6 Render the report instead of dumping raw markdown

**File:** `desktop/plugin.js` — add a tiny block renderer above `UpfrontPage` (only the subset the report emits: `#`, `##`, `###`, `-`, `>`):

```javascript
function Markdown({ text }) {
  const lines = String(text || '').split('\n')
  return jsx('div', { className: 'flex flex-col gap-1 text-xs', children: lines.map((ln, i) => {
    const key = `md${i}`
    if (ln.startsWith('### ')) return jsx('div', { key, className: 'text-sm font-semibold', children: ln.slice(4) })
    if (ln.startsWith('## '))  return jsx('div', { key, className: 'mt-2 text-sm font-semibold', children: ln.slice(3) })
    if (ln.startsWith('# '))   return jsx('div', { key, className: 'text-lg font-semibold', children: ln.slice(2) })
    if (ln.startsWith('> '))   return jsx('div', { key, className: 'border-l-2 pl-2 text-(--ui-text-tertiary)', children: ln.slice(2) })
    if (ln.startsWith('- '))   return jsx('div', { key, className: 'pl-3', children: `• ${ln.slice(2)}` })
    if (!ln.trim()) return jsx('div', { key, className: 'h-1' })
    return jsx('div', { key, children: ln })
  }) })
}
```

Then replace the result `<pre>`:

```javascript
        jsx('div', { className: 'rounded border border-(--ui-border) p-3 overflow-auto max-h-[520px]', children: jsx(Markdown, { text: result.report }) }),
```

Verify: `node --check desktop/plugin.js && echo "syntax OK"`; `grep -c "Markdown" desktop/plugin.js` → expect ≥ 2.
Commit: `feat(desktop): render the report as markdown, not a <pre>`

---

## Phase 3 — P1: make "did the UI update?" answerable

### 3.1 One copy on disk, documented

Audit:

```bash
ls -d /home/lisacore/.hermes/desktop-plugins/upfront 2>/dev/null || echo "no root desktop-plugins copy (good)"
ls -d /home/lisacore/.hermes/profiles/charlene/plugins/upfront 2>/dev/null || echo "plugin not installed (expected during dev)"
```

Rule to record in the README: the unified package is the only copy. Never copy `desktop/plugin.js` into `~/.hermes/desktop-plugins/` — that second copy is what silently won last time.

### 3.2 README: the reload procedure

**File:** `README.md` — under "Install", add:

```markdown
### When the UI looks stale (it happened — twice)

The desktop app reads `desktop/plugin.js` at load. Toggling the plugin **does not**
re-read it. Check which build you are running: the page header prints `build …`.
If it does not match `BUILD` in `desktop/plugin.js`:

1. `⌘K` → **Reload desktop plugins** (fastest), or
2. Capabilities → Plugins → Upfront off → on, or
3. Quit the app fully (tray → Quit) and relaunch.

If a toggle hangs ~30s, a stale plugin-host child is holding the RPC: `pkill -f plugin_host_child`
and retry. That is a Hermes process issue, not a plugin bug.
```

Commit: `docs: build stamp + reload procedure`

### 3.3 Keep the product name changeable (decision may come after completion)

The user will decide the final name **after** the build. So: identity stays stable, the display name is one constant.

**File:** `desktop/plugin.js` — add near `BUILD`:

```javascript
const PRODUCT_NAME = 'Upfront'   // display only — change this one line to rename the product
```

then use it in the header (`children: PRODUCT_NAME`), in the page title row, and in `export default { name: PRODUCT_NAME }` (keep `id: 'upfront'` unchanged).

**File:** `plugin.yaml` — keep `name: upfront` (identity) and add nothing else; the human label lives in `docs/POSITIONING.md` and the desktop constant until the catalog entry pins a `title`.

**File:** `docs/POSITIONING.md` — add the rename table (below) so the next person knows the cost of each kind of rename.

| Rename | Cost | What must change |
|---|---|---|
| **Display name** (what a user reads) | 1 line | `PRODUCT_NAME` in `desktop/plugin.js`, README title, POSITIONING.md |
| **Catalog / marketing name** | low | `docs/catalog-entry.draft.yaml` `name:` + `title:`; PR to `plugin-catalog/` |
| **Repo name** | low | GitHub rename (301-redirects), `git remote set-url origin`, local dir name |
| **Plugin id** (`upfront`) | **high** | tool names `upfront_*`, `$HERMES_HOME/upfront/` data path, install folder `plugins/upfront`, saved runs' provenance. Needs a migration script: rename the data dir, rewrite `plugin.yaml`/`tools.py` prefixes, and leave old tool names as aliases for one release. |

Verify: `grep -c "PRODUCT_NAME" desktop/plugin.js` → expect ≥ 3; `node --check desktop/plugin.js && echo "syntax OK"`.
Commit: `refactor(desktop): product display name is a single constant`

---

## Phase 4 — P2: input quality and catalog readiness

### 4.1 A GitHub repo URL must ingest the README, not the page chrome

**File:** `fetch.py` — add module-level:

```python
_GITHUB_REPO = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s?#]+)/?$")
_CHROME_LINES = (
    "Skip to content", "You signed in", "Sign in", "Sign up", "Navigation Menu",
    "Search or jump to", "Reload to refresh your session", "Dismiss alert",
    "Footer", "Terms", "Privacy", "Security", "Status", "Docs", "Contact",
)
```

and at the top of `fetch_url`, right after the scheme check:

```python
    m = _GITHUB_REPO.match(url)
    if m:
        owner, repo = m.group(1), m.group(2)
        for branch in ("HEAD", "main", "master"):
            raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            readme = _get_text(raw)
            if readme:
                return Document(type=doc_type, content=_drop_chrome(readme), source=url)
```

Add the two helpers (refactor the body of `fetch_url` into `_get_text(url) -> str | None` so both paths share it):

```python
def _drop_chrome(text: str) -> str:
    keep = [ln for ln in text.splitlines()
            if ln.strip() and not any(ln.strip().startswith(p) for p in _CHROME_LINES)]
    return _WS_RE.sub("\n\n", "\n".join(keep)).strip()[:50_000]
```

**File:** `tests/test_fetch.py` (new)

```python
from upfront.fetch import _drop_chrome


def test_github_chrome_is_dropped():
    html = "Skip to content\nSign in\n# Upfront\nA pre-launch opponent.\nDismiss alert\n"
    out = _drop_chrome(html)
    assert "Skip to content" not in out
    assert "A pre-launch opponent." in out
```

Plus a live check (network, one URL, ~1s):

```bash
python -c "
import sys; sys.path[:0]=['/home/lisacore/work','/home/lisacore/work/upfront-test']
from upfront.fetch import fetch_url
d = fetch_url('https://github.com/trillionverselabs-boop/Upfront-Plugin-Original')
print(len(d.content)); print(d.content[:200])
"
```
Expected: starts with `# Upfront Prediction` (or the repo's README heading), **not** "Skip to content".
Commit: `fix(fetch): repo URLs ingest the README, chrome stripped`

### 4.2 Catalog blockers: licence + attribution

```bash
curl -fsSL https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt -o LICENSE
```
If that 404s, paste an MIT licence text with `Copyright (c) 2026 TrillionVerse Labs`.

**Files:** `README.md:21` and `failure_modes.py:1` — replace `MASS (Hu & Shen)` with:

```
MASS (Qian et al., "MASS: Optimizing Multi-Agent Systems with Enhanced Prompts and Topologies")
```

Verify: `grep -rn "Hu & Shen" . --include=*.md --include=*.py` → no output.
Commit: `fix(docs): LICENSE + correct MASS citation`

### 4.3 Manifest declares what it actually does

**File:** `plugin.yaml` (full replacement):

```yaml
name: upfront
version: "0.2.0"
requires_hermes: ">=0.23.0"
description: "Upfront Prediction — a pre-launch opponent. Paste a decision, watch a living stakeholder graph react; inject a counter-move mid-run, then verify the frozen prediction later. Local-first, runs on your active model."
provides_tools:
  - upfront_run
  - upfront_status
  - upfront_report
  - upfront_history
capabilities:
  tools: [upfront_run, upfront_status, upfront_report, upfront_history]
  desktop: {entry: "desktop/plugin.js", areas: [sidebar.nav, routes]}
  network: ["active-model inference via ctx.llm", "user-supplied URL fetch (http/https, 200KB cap)"]
  writes: ["$HERMES_HOME/upfront/"]
```

Verify: `hermes plugins validate . --install-deps` → if it rejects `capabilities`/`desktop` keys, delete only the rejected keys and re-run until green; record which keys survived in the commit message. **Do not install the plugin** in this step.
Commit: `chore(manifest): declare capabilities, bump to 0.2.0`

### 4.4 Catalog entry, ready but not submitted

**File:** `docs/catalog-entry.draft.yaml` (new)

```yaml
name: upfront
title: Upfront Prediction
description: >-
  A pre-launch opponent. Paste a decision and watch a stakeholder graph react;
  inject a counter-move mid-run; the run freezes a dated prediction you verify later.
  Uses your active Hermes model; fetches user-supplied URLs to text.
repo: https://github.com/trillionverselabs-boop/upfront-test   # must become PUBLIC before submission
sha: REPLACE_WITH_40_HEX_COMMIT
tier: community
category: desktop
maintainer: trillionverselabs-boop
capabilities:
  tools: [upfront_run, upfront_status, upfront_report, upfront_history]
  env: []
requires_hermes: ">=0.23.0"
```

Verify: `git rev-parse HEAD` → paste into `sha` in a later commit (the pin must be the reviewed commit).
Commit: `docs: catalog entry draft (public repo + SHA pin still required)`

---

## Phase 5 — Validation, and the no-install discipline

### 5.1 Local suite (the only automated gate)

```bash
cd /home/lisacore/work/upfront-test
python -m pytest tests/ -q
```
Expected: all tests pass; **nothing written to `~/.hermes`** —
```bash
ls ~/.hermes/upfront 2>/dev/null || echo "clean — no writes outside the temp home"
```

### 5.2 If an install ever happens, undo it completely

```bash
uv=~/.hermes/tools/uv-*/uv
hermes plugins remove upfront
# then delete the directory ~/.hermes/desktop-plugins/upfront by hand
for d in ~/.hermes/installs/*/environments/*/; do
  $uv pip uninstall --python "$d/venv/bin/python" hermes-upfront 2>/dev/null
  # then delete "$d/workspace/plugin-sources/upfront-*" by hand
done
find ~/.hermes -iname '*upfront*' -not -path '*/cache/uv/*' | grep -v state.db
```
Expected: no output from `find`. Run history, if you want to keep it, lives in `~/backups/upfront-runtime-data-*.tar.gz`.

### 5.3 The user's desktop acceptance test (the real gate)

Not run by the implementer. Sequence handed to the user:

1. Desktop → Capabilities → Plugins → install from `https://github.com/trillionverselabs-boop/upfront-test` (private repo; Hermes uses the `gh` login).
2. Enable it → left sidebar shows **Upfront**; header shows `build 0.2.0 · gapfix` (proof the new file loaded).
3. Paste the Arete preset (title + decision + evidence), window `24h`, Run.
4. Mid-run, type "Publish the eval suite first" → **Inject ⚡** → expect a `<god> · intervention` event in the report and a visible stance shift in the graph.
5. After completion: header still says `build 0.2.0 · gapfix`; report is formatted, not raw asterisks; the blocker is a **named** stakeholder (never `Stakeholder N`).
6. Click **right/partial/wrong** on that run → reopen it → the ✓ verdict persists.
7. Deliberately break the model (switch to an unreachable provider), run again → expect a **hard error**, never `friction 0`.
8. Finished run shows a **Sea state** chip in words ("Purple ocean") plus why — not colour alone. Re-run with an obviously uncontested decision → **Blue ocean**; with the Arete preset (hard veto) → **Red ocean**.
9. The report lists **claims with ids**; score two of them ✓/✗ on the run → reopen → ✓ persists, and the header line shows `1/2 claims`.
10. Bottom of the page (or the `upfront_calibration` tool) shows `runs N · verified M · claim hit rate X%` — with `n` visible, never a bare percentage.

---

## Phase 6 — P0 for value: the checkability layer

Everything below turns "a convincing report" into "an instrument with a track record". Four of the five paper mechanisms this product claims (MASS replication manifest + repeated runs, GraphRAG claim validation, calibration) are missing today.

### 6.1 Record how the run was made (MASS replication manifest)

**File:** `manifest.py` (new)

```python
"""Replication manifest — what a run was made of, so it can be re-run and audited."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import List

from .ingestion import EXTRACT_PROMPT
from .models import Document, Scenario


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:12]


def _git_commit() -> str:
    """Short HEAD SHA read from .git directly — no subprocess in the plugin process."""
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
            {"type": d.type.value, "source": d.source, "sha": _sha(d.content), "chars": len(d.content)}
            for d in documents
        ],
        "max_personas": scenario.max_personas,
        "code_commit": _git_commit(),
        "python": sys.version.split()[0],
        "plugin_version": "0.2.0",
    }
```

**File:** `engine.py` — before `simulation.run_simulation`, after documents are resolved:

```python
    from .manifest import build_manifest
    manifest = build_manifest(scenario, scenario.documents,
                              getattr(llm, "model", "default"),
                              getattr(llm, "temperature", 0.6))
```

then pass it to the persistence step: `reporting.save_run(result, report_md, frozen, graph_payload, full_md, manifest=manifest)`.

**File:** `reporting.py` — `write_frozen_log(result, manifest: dict | None = None)` prepends the manifest as the first JSONL line:

```python
def write_frozen_log(result: SimulationResult, manifest: dict | None = None) -> str:
    rows = []
    if manifest:
        rows.append(manifest)
    rows.append({...})   # existing meta row, unchanged
```
and `save_run(..., manifest: dict | None = None)` passes it through.

**File:** `llm_adapter.py` — expose the fields the manifest needs:

```python
    def __init__(self, ctx_llm, temperature: float = 0.6, model: str = "default"):
        self._llm = ctx_llm
        self.temperature = temperature
        self.model = model
```

**File:** `tests/test_manifest.py` (new)

```python
import json

from upfront import engine, reporting
from upfront.manifest import build_manifest
from upfront.models import Document, DocumentType, Scenario


class FakeLLM:
    model = "fake"
    temperature = 0.6

    def complete(self, prompt):
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [{"name": "Eng", "role": "blocker",
                                             "stance": -0.6, "reason": "compliance"}],
                               "relationships": []})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_manifest_is_first_line_of_log(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it", source="memo")])
    res = engine.run_scenario(sc, FakeLLM())
    lines = (reporting.runs_dir() / res.run_id / "log.jsonl").read_text().splitlines()
    first = json.loads(lines[0])
    assert first["type"] == "manifest"
    assert first["model"] == "fake"
    assert first["documents"][0]["chars"] == len("Ship it")
    assert len(first["extract_prompt_sha"]) == 12
```

Run → fails → implement → **1 passed**.
Commit: `feat(replication): per-run manifest in the frozen log`

### 6.2 Sea state — red / purple / blue

**File:** `scoring.py` — add:

```python
SEA = {
    "red":    {"label": "Red ocean",    "color": "#e5484d"},
    "purple": {"label": "Purple ocean", "color": "#8b5cf6"},
    "blue":   {"label": "Blue ocean",   "color": "#3b82f6"},
}


def sea_state(result: SimulationResult) -> dict:
    """Landscape-level contestability. Separate scale from per-node stance colour.

    blue   — uncontested: no blocking camp, low friction.
    red    — contested and armed: a hard veto player, or two+ blocking camps, or high friction.
    purple — the middle: a real contest with contestable ground (the common case).
    """
    against = [c for c in result.camps if c.get("lean") == "against"]
    hard_veto = result.blocker is not None and result.blocker.stance < -0.7
    f = result.friction

    if hard_veto or len(against) >= 2 or f >= 65:
        key, why = "red", (
            f"hard veto player ({result.blocker.name} {result.blocker.stance:+.2f})" if hard_veto
            else f"{len(against)} blocking camps" if len(against) >= 2
            else f"friction {f:.0f}/100"
        )
    elif f < 35 and not against:
        key, why = "blue", f"no blocking camp, friction {f:.0f}/100"
    else:
        key, why = "purple", f"friction {f:.0f}/100 with {len(against) or 'no'} blocking camp(s)"
    return {"state": key, "label": SEA[key]["label"], "color": SEA[key]["color"], "why": why}
```

**File:** `models.py` — add `sea: Dict[str, object] = Field(default_factory=dict)` to `SimulationResult`.
**File:** `engine.py` — after `result.friction`/`result.blocker` are set: `result.sea = scoring.sea_state(result)`.
**File:** `reporting.py` — in `write_report` add after the friction line:

```python
    if result.sea:
        lines.append(f"**{result.sea['label']}** — {result.sea['why']}")
        lines.append("")
```

**File:** `tests/test_sea_state.py` (new)

```python
from upfront.models import Persona, SimulationResult
from upfront.scoring import sea_state


def _res(friction, blocker_stance=None, camps=None):
    return SimulationResult(
        title="t", goal="adoption", rounds=8, friction=friction, personas=[],
        blocker=Persona(name="Eng", stance=blocker_stance) if blocker_stance is not None else None,
        camps=camps or [],
    )


def test_blue_when_quiet():
    assert sea_state(_res(20, -0.1))["state"] == "blue"


def test_red_on_hard_veto():
    assert sea_state(_res(50, -0.8))["state"] == "red"


def test_red_on_two_blocking_camps():
    camps = [{"name": "A", "members": ["a"], "lean": "against"},
             {"name": "B", "members": ["b"], "lean": "against"}]
    assert sea_state(_res(40, None, camps))["state"] == "red"


def test_purple_in_the_middle():
    assert sea_state(_res(48, -0.4, [{"name": "A", "members": ["a"], "lean": "against"}]))["state"] == "purple"
```

Run → fails → implement → **4 passed**.
Commit: `feat(scoring): red/purple/blue sea state`

### 6.3 Publish falsifiable claims with every run

**File:** `claims.py` (new)

```python
"""Frozen, checkable claims. No claim, no run: a report you cannot score is marketing."""

from __future__ import annotations

import uuid
from typing import List

from .models import SimulationResult


def build_claims(result: SimulationResult) -> List[dict]:
    """Deterministic claims derived only from this run. Each is scorable yes/no."""
    claims: List[dict] = []
    window = f"{result.rounds} rounds"

    if result.blocker:
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "veto_player",
            "claim": f"{result.blocker.name} is the binding constraint on this decision within {window}.",
            "expected": {"subject": result.blocker.name, "stance": round(result.blocker.stance, 2)},
            "source": (result.blocker.reasons[0] if result.blocker.reasons else ""),
        })
    else:
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "no_veto_player",
            "claim": f"No stakeholder blocks this decision within {window}.",
            "expected": {"subject": None},
            "source": "",
        })

    lo = max(0.0, result.friction - result.uncertainty)
    hi = min(100.0, result.friction + result.uncertainty)
    claims.append({
        "id": uuid.uuid4().hex[:8],
        "kind": "friction_band",
        "claim": f"Observed friction will land between {lo:.0f} and {hi:.0f} "
                 f"(point estimate {result.friction:.0f} ± {result.uncertainty:.0f}).",
        "expected": {"lo": round(lo, 1), "hi": round(hi, 1), "point": round(result.friction, 1)},
        "source": "input quality score",
    })

    against = [c for c in result.camps if c.get("lean") == "against"]
    if against:
        camp = max(against, key=lambda c: len(c.get("members", [])))
        claims.append({
            "id": uuid.uuid4().hex[:8],
            "kind": "coalition",
            "claim": f"The blocking camp led by {camp['members'][0]} "
                     f"({', '.join(camp['members'])}) stays aligned against the decision.",
            "expected": {"members": list(camp["members"])},
            "source": "camp clustering",
        })
    return claims
```

**File:** `models.py` — `claims: List[dict] = Field(default_factory=list)`.
**File:** `engine.py` — after `result.sea = ...`: `result.claims = build_claims(result)` (import at top of function).
**File:** `reporting.py` — `write_frozen_log` appends `{"type": "claim", **c}` rows; `write_report` adds:

```python
    if result.claims:
        lines.append("## Claims to check (score these in 48h)")
        for c in result.claims:
            lines.append(f"- `{c['id']}` {c['claim']}")
        lines.append("")
```

**File:** `tests/test_claims.py` (new)

```python
from upfront.claims import build_claims
from upfront.models import Persona, SimulationResult


def test_three_claims_with_a_blocker_and_a_camp():
    res = SimulationResult(
        title="t", goal="adoption", rounds=8, friction=50.0, uncertainty=10.0,
        personas=[Persona(name="Eng", stance=-0.8, reasons=["compliance"])],
        blocker=Persona(name="Eng", stance=-0.8, reasons=["compliance"]),
        camps=[{"name": "Eng + 1", "members": ["Eng", "Ops"], "lean": "against"}],
    )
    c = build_claims(res)
    kinds = {x["kind"] for x in c}
    assert kinds == {"veto_player", "friction_band", "coalition"}
    assert c[1]["expected"] == {"lo": 40.0, "hi": 60.0, "point": 50.0}
    assert all(x["id"] for x in c)


def test_no_blocker_case_is_still_scorable():
    res = SimulationResult(title="t", goal="adoption", rounds=8, friction=20.0,
                           uncertainty=5.0, personas=[Persona(name="A", stance=0.5)])
    c = build_claims(res)
    assert c[0]["kind"] == "no_veto_player"
    assert len(c) == 2
```

Run → fails → implement → **2 passed**.
Commit: `feat(claims): freeze falsifiable claims per run`

### 6.4 Score the verdict per claim

**File:** `reporting.py` — replace `mark_verified` with a claim-aware version (keep the old signature working):

```python
def mark_verified(run_id: str, verdict: str, note: str = "",
                  hits: dict | None = None, actual_friction: float | None = None) -> dict:
    """Score a frozen prediction. `hits` maps claim id -> True/False."""
    if verdict not in ("right", "partial", "wrong"):
        raise ValueError("verdict must be right|partial|wrong")
    d = _run_dir(run_id)
    meta_path = d / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(run_id)
    meta = json.loads(meta_path.read_text())

    hits = hits or {}
    claim_ids = [ln for ln in (d / "log.jsonl").read_text().splitlines()
                 if '"type": "claim"' in ln] if (d / "log.jsonl").exists() else []
    scored = sum(1 for v in hits.values() if v)
    total = len(hits) or len(claim_ids)

    meta["verified"] = {
        "verdict": verdict,
        "note": note,
        "at": datetime.now().isoformat(timespec="seconds"),
        "hits": hits,
        "score": round(scored / total, 3) if total else None,
        "actual_friction": actual_friction,
        "friction_error": (round(abs(actual_friction - meta.get("friction", 0)), 1)
                           if actual_friction is not None else None),
    }
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta["verified"]
```

**File:** `tests/test_verify.py` — extend the existing file:

```python
def test_claims_are_scored(tmp_hermes_home, ...):
    # reuse the FakeLLM run from the existing test, then:
    res = engine.run_scenario(sc, FakeLLM())
    out = reporting.mark_verified(res.run_id, "partial",
                                  hits={"a": True, "b": False}, actual_friction=61.0)
    assert out["score"] == 0.5
    assert out["actual_friction"] == 61.0
    assert out["friction_error"] is not None
```

Run → fails → implement → **passed**.
Commit: `feat(verify): per-claim scoring and friction error`

### 6.5 The calibration ledger (the track record)

**File:** `reporting.py` — add:

```python
def calibration() -> dict:
    """Aggregate every run into a track record. This is the product's value over time."""
    runs = []
    root = runs_dir()
    if root.exists():
        for d in root.iterdir():
            m = d / "meta.json"
            if not m.exists():
                continue
            try:
                runs.append(json.loads(m.read_text()))
            except Exception:
                continue
    verified = [r for r in runs if r.get("verified")]
    scores = [r["verified"]["score"] for r in verified if r["verified"].get("score") is not None]
    errors = [r["verified"]["friction_error"] for r in verified
              if r["verified"].get("friction_error") is not None]
    by_sea: dict = {}
    for r in runs:
        key = r.get("sea_state", "unknown")
        by_sea[key] = by_sea.get(key, 0) + 1
    return {
        "runs": len(runs),
        "verified": len(verified),
        "claim_hit_rate": round(sum(scores) / len(scores), 3) if scores else None,
        "mean_friction_error": round(sum(errors) / len(errors), 1) if errors else None,
        "verdicts": {v: sum(1 for r in verified if r["verified"]["verdict"] == v)
                     for v in ("right", "partial", "wrong")},
        "sea_state": by_sea,
    }
```

**File:** `reporting.py` — `save_run` meta must carry the sea state, so add to the meta dict: `"sea_state": result.sea.get("state", "")`.

**File:** `dashboard/plugin_api.py` — add `@router.get("/calibration")` returning `reporting.calibration()`.
**File:** `tools.py` — register `upfront_calibration` (no params) returning `json.dumps(reporting.calibration())`; add it to `plugin.yaml` `provides_tools`.

**File:** `tests/test_calibration.py` (new)

```python
import json

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario


class FakeLLM:
    model = "fake"
    temperature = 0.6

    def complete(self, prompt):
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [{"name": "Eng", "role": "blocker",
                                             "stance": -0.8, "reason": "compliance"}],
                               "relationships": []})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_ledger_aggregates_scored_runs(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    a = engine.run_scenario(sc, FakeLLM())
    b = engine.run_scenario(sc, FakeLLM())
    reporting.mark_verified(a.run_id, "right", hits={"x": True, "y": True})
    reporting.mark_verified(b.run_id, "wrong", hits={"x": False, "y": True})
    led = reporting.calibration()
    assert led["runs"] == 2
    assert led["verified"] == 2
    assert led["claim_hit_rate"] == 0.75
    assert led["verdicts"]["right"] == 1
```

Run → fails → implement → **1 passed**.
Commit: `feat(calibration): ledger of hit rate and friction error`

### 6.6 Counterfactual pair — the injection as a controlled experiment

**File:** `engine.py` — add:

```python
def run_pair(scenario: Scenario, llm, intervention, run_id_baseline: str,
             run_id_treatment: str) -> dict:
    """Baseline vs treatment: same documents, one variable changed (MASS counterfactual)."""
    baseline = run_scenario_progress(scenario, llm, run_id=run_id_baseline)

    treated = scenario.model_copy(deep=True)
    treated.interventions = [intervention]
    treatment = run_scenario_progress(treated, llm, run_id=run_id_treatment)

    def _stances(res):
        return {p.name: round(p.stance, 3) for p in res.personas}

    b, t = _stances(baseline), _stances(treatment)
    pair = {
        "baseline_run": baseline.run_id,
        "treatment_run": treatment.run_id,
        "intervention": {"name": intervention.name, "description": intervention.description},
        "friction_delta": round(treatment.friction - baseline.friction, 1),
        "stance_delta": {k: round(t[k] - b.get(k, 0.0), 3) for k in t},
        "verdict": ("counter-move works" if treatment.friction < baseline.friction
                    else "counter-move did not help"),
    }
    (reporting.runs_dir() / baseline.run_id / "pair.json").write_text(json.dumps(pair, indent=1))
    return pair
```

**File:** `tests/test_pair.py` (new)

```python
import json

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Intervention, Scenario


class FakeLLM:
    model = "fake"
    temperature = 0.6

    def __init__(self):
        self.seen_intervention = False

    def complete(self, prompt):
        if "extracting" in prompt.lower() or "stakeholder landscape" in prompt.lower():
            return json.dumps({"personas": [{"name": "Eng", "role": "blocker",
                                             "stance": -0.8, "reason": "compliance"}],
                               "relationships": []})
        if "Intervention" in prompt:
            self.seen_intervention = True
            return json.dumps({"stance_delta": 0.4, "action": "supports", "text": "evals convince us"})
        return json.dumps({"stance_delta": 0.0, "action": "waits", "text": ""})


def test_pair_reports_a_delta(tmp_hermes_home):
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    llm = FakeLLM()
    pair = engine.run_pair(sc, llm, Intervention(name="Publish evals", description="Ship evals first"),
                           "base1", "treat1")
    assert pair["friction_delta"] <= 0
    assert (reporting.runs_dir() / "base1" / "pair.json").exists()
    assert pair["verdict"] in ("counter-move works", "counter-move did not help")
```

Run → fails → implement → **1 passed**.
Commit: `feat(engine): counterfactual baseline/treatment pair`

### 6.7 GraphRAG claim extraction (enrichment, never required)

Deterministic claims (6.3) stay the contract. This adds sourced claims from the documents so provenance is machine-checkable.

**File:** `claims.py` — add:

```python
EXTRACT_CLAIMS_PROMPT = """Read the documents and list the factual claims that a stakeholder
reaction depends on. For each, quote the source span. Max 8.

Respond with ONLY JSON:
{{"claims": [{{"claim": "...", "source": "exact quoted span from the document"}}]}}

DOCUMENTS:
{docs}
"""


def extract_claims(result: SimulationResult, llm, documents) -> List[dict]:
    """Optional enrichment. Returns [] on any failure — deterministic claims still stand."""
    from .ingestion import _docs_block
    try:
        raw = llm.complete(EXTRACT_CLAIMS_PROMPT.format(docs=_docs_block(documents)))
    except Exception:
        return []
    from .ingestion import _parse_json
    parsed = _parse_json(raw)
    if not parsed:
        return []
    out = []
    for c in parsed.get("claims", [])[:8]:
        text = str(c.get("claim", "")).strip()
        src = str(c.get("source", "")).strip()
        if text:
            out.append({"kind": "extracted", "claim": text, "source": src,
                        "id": uuid.uuid4().hex[:8]})
    return out
```

**File:** `engine.py` — after deterministic claims:

```python
    extra = extract_claims(result, llm, scenario.documents)
    if extra:                      # enrichment only; never required, never fatal
        result.claims = result.claims + extra
        result.degraded = result.degraded  # unchanged
```

**File:** `tests/test_claim_extraction.py` (new)

```python
import json

from upfront.claims import extract_claims
from upfront.models import Document, DocumentType, Scenario, SimulationResult


class ClaimsLLM:
    def complete(self, prompt):
        return json.dumps({"claims": [
            {"claim": "61% of CIOs cannot route inference externally", "source": "Q2 survey of 400 CIOs"}]})


class Boom:
    def complete(self, prompt):
        raise RuntimeError("down")


def _res():
    return SimulationResult(title="t", goal="adoption", rounds=8, personas=[])


def test_extracted_claims_carry_sources():
    docs = [Document(type=DocumentType.EVIDENCE, content="61% of CIOs block external routing")]
    out = extract_claims(_res(), ClaimsLLM(), docs)
    assert out[0]["kind"] == "extracted"
    assert "CIOs" in out[0]["source"]


def test_failure_is_silent_and_empty():
    assert extract_claims(_res(), Boom(), []) == []
```

Run → fails → implement → **2 passed**.
Commit: `feat(claims): GraphRAG-style sourced claim extraction`

### 6.8 Desktop: sea-state chip, claims scoring, calibration line

**File:** `desktop/plugin.js` — three edits, no JSX.

1. Sea-state chip in the result header. Add above the result block:

```javascript
function SeaChip({ sea }) {
  if (!sea || !sea.state) return null
  return jsx('span', {
    className: 'rounded px-2 py-0.5 text-xs font-medium text-white',
    style: { backgroundColor: sea.color },
    title: sea.why,
    children: sea.label,
  })
}
```

and render it beside the result title:

```javascript
      result && jsxs('div', { className: 'flex items-center gap-2', children: [
        jsx(SeaChip, { sea: result.sea }),
        jsx('span', { className: 'text-xs text-(--ui-text-tertiary)', children: result.sea?.why || '' }),
      ]}),
```

2. Fetch the sea state with the report. In `run()`, where the result is set:

```javascript
        const [rep, g, meta] = await Promise.all([
          ctx.rest(`/report/${run_id}`).catch(() => ({ report: '' })),
          ctx.rest(`/graph/${run_id}`).catch(() => ({ nodes: [], edges: [] })),
          ctx.rest(`/status/${run_id}`).catch(() => ({})),
        ])
        setResult({ report: rep.report, graph: g, sea: meta.sea })
```
and have `/status` return it (task 6.8b below).

3. `dashboard/plugin_api.py` — `status()` returns the sea state once done:

```python
@router.get("/status/{run_id}")
async def status(run_id: str):
    prog = engine.get_progress(run_id)
    try:
        meta = json.loads((reporting.runs_dir() / run_id / "meta.json").read_text())
        prog["sea"] = {"state": meta.get("sea_state", ""), "label": meta.get("sea_label", ""),
                       "color": meta.get("sea_color", ""), "why": meta.get("sea_why", "")}
    except Exception:
        pass
    return prog
```
(`save_run` must persist `sea_label` / `sea_color` / `sea_why` alongside `sea_state` — add those three keys in 6.5's meta write.)

Verify: `node --check desktop/plugin.js && echo "syntax OK"`; `grep -c "SeaChip" desktop/plugin.js` → expect 2.
Commit: `feat(desktop): sea-state chip on finished runs`

### 6.9 Documentation: positioning + what to promise

**File:** `docs/POSITIONING.md` (new) — the game-review framing, the paper→mechanism table, the sea-state definition, and the three sentences we are allowed to say about accuracy (pre-experimental evidence; scored track record; never "predicts"). Content is written in the repo (see the file added with this plan).
**File:** `README.md` — replace the opening two paragraphs so the first line a reviewer reads is the game-review framing, not "pre-launch opponent"; add a **Sea state** bullet and a **Track record** bullet under "What you get back".
Verify: `head -12 README.md` shows the new framing; `grep -n "See state\|Sea state" README.md` → 1 hit.
Commit: `docs: strategic-review positioning, sea state, track record`

---

## Tests / validation

- TDD per task: write the test, run it, watch it fail for the stated reason, implement minimally, re-run to green, commit with the message given.
- Full suite gate before each phase end: `python -m pytest tests/ -q`.
- Never install into the Hermes backend for verification; never copy `plugin.js` into `~/.hermes/desktop-plugins/`.
- `node --check desktop/plugin.js` after every `plugin.js` edit (it is loaded uncompiled, so a syntax slip blanks the page).

---

## Risks, tradeoffs, open questions

1. **`capabilities:` may not be a supported `plugin.yaml` key.** Mitigation: validate with `hermes plugins validate .` and drop rejected keys; the catalog entry carries the real capability declaration regardless.
2. **The `/inject` queue is process-local.** If the gateway restarts mid-run, queued injections are lost and the run fails — acceptable: the run is already in-process.
3. **Friction for a genuinely neutral input is 35, not 0** (`(1−0)/2·70`). Deliberately left alone this pass: the degenerate-0 bug is the one that lied. Recalibrating friction changes every historical number and needs its own decision.
4. **20-round sims cost `rounds × personas` model calls** (up to ~160 + reflections). That is the real cause of the slow toggle/run feel. A `max_parallel` or cheap-model pin is a follow-up; not in this pass.
5. **The report renderer is a 6-rule markdown subset.** Inline `**bold**` is not handled; acceptable for now, but a judge may notice.
6. **Private repo vs catalog.** Submission needs a public repo and a 40-hex pin. Flip visibility only when the user says so — that is a standing rule, not a default.
7. **Open question for the user:** should `upfront-test` keep the name once it becomes the real product repo, or rename to `upfront` at submission time? Renaming later breaks existing clone URLs but GitHub 301-redirects.
8. **Game-theory framing risks overclaiming.** We never use the word "equilibrium", never claim a Nash outcome, and never present a single run as a stable result — repeated-run directional consistency is the only stability claim allowed. If a reviewer reads the words "game-theoretic review" as "solves the game", the report must push back in the same breath.
9. **Calibration needs volume to be honest.** A hit rate over 3 runs is noise. Until 10 scored runs exist, the ledger must display `n` next to every number and must not be shown on its own as a headline.
10. **Counterfactual pairs cost 2×** (`run_pair` = two full simulations). Keep it opt-in, never the default path, and say the cost before running.
11. **Purple is load-bearing.** Red/purple/blue must stay distinguishable for colour-blind users: every sea-state chip carries its text label and a `title` explanation, never colour alone. Node stance colours (red/amber/green) and sea state (red/purple/blue) must not be conflated in copy — they are different layers.
