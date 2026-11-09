# Upfront (`upfront`)

**A strategic-response review, not a predictor.** Paste a decision (or drop in a URL — a
blog post, a repo README, a landing page) and Upfront maps the players who can **veto** the
move, the coalitions around it, your **best response**, and how **contested the ground** is.
Then it freezes falsifiable claims you score against what actually happens.

```
Your move → who can veto it → coalitions → best response → competition read → claims frozen → score them later
```

### The competition read: red / purple / blue ocean

A landscape-level read, on a **left-to-right axis**: red on the left (high competition —
everyone fighting for the same fish), purple in the middle (medium — a real contest with
winnable ground, the common case), blue on the right (low — open water, *this is the good
end*). It is a different colour scale from per-stakeholder stance (red / amber / green),
so the two never get conflated.

### This is a review, not a forecast

MASS's own boundary rule: LLM-driven simulation produces *pre-experimental evidence* —
mechanism rehearsal, counterfactual contrast, risk identification. Upfront never claims to
predict an outcome, solve a game, or find an equilibrium. What it does claim is a **scored
track record**: every run freezes claims, every claim can be scored, and the calibration
ledger shows hit rate and friction error over N runs.

## How it works

Under the hood it is a small, clean-room implementation of five research ideas:

| Research | What it powers here |
|---|---|
| **GraphRAG** (Edge et al.) | Document → stakeholder/relationship extraction; stakeholder camp clusters |
| **Generative Agents** (Park et al.) | Each stakeholder has a memory stream, retrieval, and periodic reflection |
| **OASIS** | The round-based simulation loop and social action types |
| **MASS** (Qian et al.) | Replication manifest, scheduling discipline, and the 8 known failure modes, reported per run |
| **CAMEL** | Role-play framing + inception-style prompt templates |

Everything is local-first: the graph and every past run are stored in `~/.hermes/upfront/`
on your machine. No cloud graph service, no Zep, no Docker. Runs on **your active Hermes
model** via `ctx.llm` — the plugin never sees or stores a credential.

## What you get back

- **Friction score** (0–100, ± uncertainty) — how hard this will land. The uncertainty comes
  from *input quality*, not from claiming predictive accuracy. This is a structured
  hypothesis grounded in your document, **not a calibrated probability of real-world outcome.**
- **A living stakeholder graph** — nodes colored by stance (red = against, green = for), edges
  for oppose/support. Pure React SVG, no library.
- **The blocker + counter-moves** — the single most dangerous stakeholder, why (traced to a
  sentence in your doc), and the move that flips them.
- **Provenance** — every stance cites the input text it came from ("grounded"), clearly
  separated from reasoning the model filled in ("speculated").
- **A competition read** — **Red ocean** (high), **Purple ocean** (medium), **Blue ocean**
  (low), with the trigger stated in words. Colour is never the only signal.
- **Frozen claims** — 2-4 falsifiable calls per run (veto player, friction band, coalition
  stability), written to `log.jsonl` with a **replication manifest** (model, temperature,
  prompt hash, document hashes, code commit) so the run can be audited and re-run.
- **A track record** — score the claims and the ledger reports claim hit rate, friction
  error, and the sea-state mix. The hit rate is the accuracy claim; a single report is not.

### Desktop experience (left sidebar → Upfront)

The page is a full-center view. The **starting form** is a single card:

- **Title** (single line), **Decision document** (large textarea, required),
  **Evidence (optional)** (smaller textarea), **URLs** (one per line — blog post, repo
  README, landing page; fetched as documents). Fetched URLs are **real documents**, not
  free-text noise: the page is fetched, converted to text, and ingested alongside
  anything you pasted — with the URL kept as the source for provenance.
- **Model** picker: the live catalogue with per-million prices, a "free only" filter, and
  a live `N calls · cost` line for the selected window (see *Live model catalogue* below).
- **Window** dropdown: `6h` / `12h` / `24h` / `48h`.
- **Run button:** "Run prediction" (disabled until a decision is typed, or while running).

**In progress:** when you click Run, the button reads `Simulating… X%` and a live
**"Simulation in progress"** card appears below the form. It shows a progress bar and
`Round N of M — X%`, and — wired to the same polled `/status` payload — a **live SVG
graph that updates every round** as stakeholder stances shift. Node colors move
red/yellow/green in real time as the simulation proceeds.

**Finished report:** when the run completes, the live card gives way to a 2-column
result view:
- **Left:** the final stakeholder graph (nodes + oppose/support edges, camp labels).
- **Right:** the markdown report (friction score, blocker, counter-moves, provenance,
  camps, failure-mode audit, and the plain-language recommendation).

**History:** every run is saved. The "Past runs — click to reopen & verify" list shows
each run's title, friction score, and blocker. Clicking one reloads its graph and
report so you can check the frozen prediction later.

**Opt-in deep dive:** `upfront_report(run_id, full=true)` (or `GET /report/{id}?full=true`)
returns the long-form `report_full.md` — the same grounded content expanded with
per-stakeholder narratives, round-by-round trajectories, the camp structure, and the
MASS failure-mode audit. Same predictions, just also saved as `report_full.md` next to
`report.md`. It adds no new claims — longer, not invented filler.

## What to feed it (and what hurts)

Best results come from documents that **contain a real disagreement**:

- ✅ **A decision + an evidence document.** The decision states the plan; the evidence
  (real numbers, quotes, sources) is what turns "simulated" into "grounded." This is the
  single biggest driver of output quality.
- ✅ **URLs are fine.** Drop a blog post, a repo README, or a landing page — the plugin
  fetches them to text and ingests them as documents.
- ⚠️ **Opinion with no source** → stances become guesswork, confidence drops.
- ⚠️ **Marketing copy with no substance** → nothing to ground on.
- ⚠️ **A document that already assumes consensus** → the tool will (correctly) report low friction.

The plugin scores your input quality and tells you "add an evidence document for grounded
stances" when a run comes back thin — the tool teaches you what to feed it.

## Which model to run it on

Upfront runs on **your active Hermes model** (borrowed via `ctx.llm`, host-owned auth).
It does not need a frontier model — the work is many small structured judgments
(open to act, nudge a stance, summarize a few memories), not one hard reasoning problem.

- **Best value: a cheap, fast "flash"-class model.** The vast majority of the calls are
  short JSON out-judgments; a small/fast model handles them well and runs the whole
  simulation far faster and cheaper. This is where you'll feel the model-quality / speed
  tradeoff most — a big reasoning model makes the sim *slower*, not smarter.
- **A larger/reasoning model** gives more nuanced per-round language but costs many
  seconds per call; across 50–200 calls that adds up. Use it when you want the richest
  per-actor reasoning and don't mind the wait.

### Live model catalogue with real prices

The form's **Model** picker is populated from the public Nous inference catalogue
(`https://inference-api.nousresearch.com/v1/models` — no credentials required, 357 usable
chat models at the time of writing) and shows, for every model, the **published price per
million tokens** in and out. The run line under it does the arithmetic before you commit:

```
176 calls · ~$0.02 at list price        (a paid flash-class model)
176 calls · FREE                        (one of the five zero-priced models)
```

- **Free models are flagged and filterable** ("free only") — the currently configured
  default, `reflection/beam-1.0-501b-a23b:free`, is one of them.
- **Cheap ≠ frontier.** For a review the work is many small structured judgments, so a
  flash-class model is usually the right buy; a frontier model costs ~$5 for the same
  176 calls and makes the run *slower*, not smarter.
- **Nothing is hardcoded.** Prices come from the same live endpoint the Portal uses, are
  cached for 6 hours, and carry their fetch time in the UI. No invented price list.
- **Choosing a specific model needs consent.** Hermes gates host-owned model selection
  behind the `llm.model_override` capability; the plugin declares it and probes it. If the
  user declines, the run still works — on the active model — and the UI says so.

The catalogue is fetched anonymously, so it never touches a credential (see rule 11 below).

## Catalog disclosure (admission rule 13)

What a user would want to know before installing, stated plainly:

- **Network calls:** to the inference endpoint serving your active Hermes model
  (via `ctx.llm`), and — only when you provide URLs — to fetch those URLs as text.
  Fetched URLs are capped (http/https only, size and length limited, hard timeout).
- **Background processes:** a simulation runs in a background thread while it streams
  progress to the desktop UI. No long-running daemon, no auto-update, no telemetry.
- **Data:** reads and writes live only under `~/.hermes/upfront/` (graph + run history)
  plus the plugin's own package files. Nothing leaves the machine except the inference
  and URL-fetch calls above.
- **Credentials:** none stored. All model access goes through Hermes' host-owned
  `ctx.llm` (admission rule 11). The plugin never reads `.env`, `auth.json`, or any
  vendor token file.

## Install

Hermes plugins only load when the plugin is enabled. From the desktop app:
**Capabilities → Plugins → Upfront → enable**, then it appears in the left sidebar.

From the CLI:

```bash
hermes plugins install /path/to/upfront   # or by catalog name once listed
hermes plugins enable upfront
```

The desktop half is opt-in by design: it inventories in Capabilities → Plugins and stays
off until you switch it on. That's the marketplace pattern — install, then enable.

### When the UI looks stale (it happened — twice)

The desktop app reads `desktop/plugin.js` at load. Toggling the plugin **does not** re-read
it. The page header prints `gateway: … · build <BUILD>`; if that does not match `BUILD` in
`desktop/plugin.js`, you are looking at an old module:

1. `⌘K` → **Reload desktop plugins** (fastest), or
2. Capabilities → Plugins → Upfront off → on, or
3. Quit the app fully (tray → Quit) and relaunch.

If a toggle hangs ~30s, a stale plugin-host child is holding the RPC: `pkill -f plugin_host_child`
and retry. That is a Hermes process issue, not a plugin bug.

### Where data lives

Run history, the graph, the manifests and the calibration ledger live in the plugin's
sanctioned data root (`plugin_data_dir("upfront")` — `<hermes home>/plugin-data/upfront/`),
which survives plugin updates and removal and follows the active profile.

## Develop / run as a test

From a fresh clone of this repo (Python ≥3.11):

```bash
# 1. install dev + runtime deps
pip install -e .[test]   # or manually: pip install pydantic fastapi pytest kuzu

# 2. run the test suite
python -m pytest tests/ -q
```

Test files:

- `tests/test_endtoend.py` — full sim with a fake LLM (no network, no credentials).
- `tests/test_real_run.py` — real run against whatever `ctx.llm` Hermes provides
  (skips when no LLM is bound; that is expected outside Hermes).

Manual smoke check (also what the backend loader does):

```bash
python -c "
import sys, importlib.util
spec = importlib.util.spec_from_file_location('hermes_dashboard_plugin_upfront', 'dashboard/plugin_api.py')
m = importlib.util.module_from_spec(spec)
sys.modules['hermes_dashboard_plugin_upfront'] = m
spec.loader.exec_module(m)
print('router:', m.router)  # should print an APIRouter, no import errors
"
# note: _llm() raises until register() binds ctx.llm — that is correct behaviour.
```

If you only need to verify the plugin validates:

```bash
hermes plugins validate . --install-deps
```

## Repo layout

```
upfront/
├── plugin.yaml              # plugin manifest (provides_tools …)
├── __init__.py              # register(ctx): tools + ctx.llm bind
├── pyproject.toml           # python deps: pydantic, fastapi
├── dashboard/
│   ├── manifest.json        # {"name": "upfront", "api": "plugin_api.py"}
│   └── plugin_api.py        # FastAPI backend at /api/plugins/upfront/
├── desktop/plugin.js        # desktop UI (sidebar + pane, React ESM)
├── data/presets/*.json      # arete / arete-real demo presets
├── tests/                   # pytest suite (fake-LLM end-to-end)
└── src modules: models, graph, ingestion, agents, simulation, scoring,
                 reporting, tools, engine, llm_adapter, fetch …
```

## Tools exposed

- `upfront_run` → `{ run_id }`
- `upfront_status(run_id)` → status / progress / snapshot
- `upfront_report(run_id)` → markdown report text
- `upfront_history([limit])`

