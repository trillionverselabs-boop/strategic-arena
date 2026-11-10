# Progress log — Upfront

Running log for cheap handoffs. Newest state at the top of each item; one entry per shipped item.
Truth for state and gates: `docs/HANDOFF.md` + `docs/ROADMAP.md`.

Gates (both must pass before every commit):

```
VENV=/home/lisacore/.hermes/profiles/charlene/cache/scratch/upvenv
$VENV/bin/python -m pytest tests/ -q --ignore=tests/test_real_run.py
node --check desktop/plugin.js
```

| Item | Status | Tests | Commit |
|---|---|---|---|
| R1 — auto-rescore at window close | shipped | 44 passed | see git log |
| R2 — preset packs as skills | shipped | 54 passed | see git log |
| R3 — decision record export | shipped | 60 passed | see git log |
| R4 — model-aware presets | shipped | 63 passed | see git log |
| R5 — desktop UI: Recent block + graphical polish | shipped | node --check + render smoke | see git log |
| R6 — desktop UI: Kanban look (SDK components) | shipped | node --check + render smoke | see git log |

---

## R1 — auto-rescore at window close (shipped)

**What shipped**

- `models.Window.seconds` — wall-clock length of each timeline (30m → 1800s … 48h → 172800s).
- `SimulationResult.window` — the timeline a run was asked for; persisted into `meta.json`, so
  the deadline is a property of the record, not of the caller's memory.
- `reporting.due_claims(as_of=None)` — every run whose `created_at + window` has passed and that has
  no `verified` block, oldest first: `[{run_id, title, due_at, window, created_at, claims[]}]`.
  Unknown window or unparseable timestamp → skipped, never guessed.
- `GET /api/plugins/upfront/due` → `{due: [...], count: n}`.
- Tool `upfront_due(as_of?)` — the same payload, so an agent can act on it.
- Bundled skill `skills/upfront-review/SKILL.md` (registered through `ctx.register_skill`, resolves as
  `upfront:upfront-review`): when a review is filed, schedule **one-shot** Hermes cron at the window
  close whose prompt calls `upfront_due`; never a plugin-owned timer.
- `__init__._register_skills()` walks `skills/*/SKILL.md`; a bad skill is logged and skipped, never fatal.
- `plugin.yaml` + catalog draft: `upfront_due` added to tools. `pyproject.toml` version aligned to
  0.3.0 and stale "Upfront Prediction" description replaced.

**Verified**

- `tests/test_due.py` (8 tests): window persisted; closed window due; open window not due; scored run
  not due; `as_of` respected; `/due` route payload; `upfront_due` in the schema set; skill registered.
- Manual, throwaway `HERMES_HOME`: 30m run → `/due` empty (window open), then with `as_of` past the
  window → one row, `due_at = created_at + 30m`, 4 claims with ids.
- Full suite green, `node --check` clean.

**Next:** R2 — the four preset packs as skills.

---

## R2 — preset packs as plugin skills (shipped)

**What shipped** — four packs under `skills/`, registered via `ctx.register_skill` (resolve as
`upfront:<name>`, never copied into `~/.hermes/skills`):

| Skill | Teaches |
|---|---|
| `upfront-launch` | launch briefs: what to paste, evidence to demand, timeline choice |
| `upfront-pricing` | price changes: grandfathering rule quoted verbatim, churn risk, competitor framing |
| `upfront-deprecation` | sunsets: affected segments counted, migration burden, notice-period collisions |
| `upfront-openweight` | licence/weights/evals: exact licence id, compliance objections, community expectations |

Each 60–73 lines: when to use, what to paste, what the read must tell you, timeline, checklist,
worked example, and the "not a prediction" boundary stated once.

**Verified**

- `tests/test_skills.py` (10 tests): existence, frontmatter (`name` == dir, description ≤ 1024),
  checklist, boundary, tool named, line budget, all five skills register through `register()`,
  `plugin.yaml` capabilities unchanged (`llm.model_override` only).
- Test caught a real omission: pricing / deprecation / open-weight packs never named `upfront_run`;
  added an explicit "run it with" line to each.
- `hermes plugins doctor /home/lisacore/work/upfront` → OK: runtime discovery, manifest parsing,
  import and registration passed; 6 tools.
- `node --check desktop/plugin.js` clean.

**Next:** R3 — decision record export.

---

## R3 — decision record export (shipped)

**What shipped**

- `reporting.export_decision(run_id, out_dir="decisions") -> str` — writes
  `<data_root>/decisions/<slug>.md` (absolute `out_dir` honoured). Contents: title, `run:` line with
  created_at / rounds / model / code commit, competition label + level + why, friction ± uncertainty,
  veto player with stance, claims as a `- [ ]` checklist with ids, and a `## Verdict` section.
- Once `mark_verified` has run, re-export fills `## Verdict` with verdict + note + per-claim ✓/✗ +
  actual friction/error, and **rewrites the same file** — no duplicates. A second run with the same
  title gets `-<run_id[:6]>` rather than overwriting the first record.
- `GET /api/plugins/upfront/export/{run_id}?out_dir=` → `{run_id, path, markdown}`.
- Tool `upfront_export(run_id, out_dir?)` → `{run_id, path}`.
- `meta.json` now records `blocker_stance` (old records fall back to final snapshot stances).
- `plugin.yaml` + catalog draft: `upfront_export` listed (7 tools).
- Collateral fix in `claims.py`: the coalition claim printed `X (X, Y)`; now `The blocking camp (X, Y)`,
  and a camp with no members can no longer raise IndexError — it is skipped.

**Verified**

- `tests/test_export.py` (5): file written with every claim id and the sea label; custom out_dir;
  re-export after verify fills verdict, contains ✓ and ✗, single `# Decision:` line, same path;
  unknown run raises `FileNotFoundError`; tool registered.
- Manual, throwaway `HERMES_HOME`: exported `decisions/ship-the-open-weight-release.md` and read it
  back — real output, seen above.
- Full suite 60 passed, `node --check` clean.

**Next:** R4 — model-aware presets (one line in the form).

---

## R4 — model-aware run presets (shipped)

One line under the cost line: *"For a first pass: a flash-class model at 24h. Spend on 48h and a
bigger model only when the decision is expensive."* No new code path, no new state.

**Verified** — `tests/test_ui_presets.py` asserts the copy is present, sits directly under the cost
line, and that the build stamp is still `0.3.0 · ui1`; `node --check` clean; suite 63 passed.

---

## Open items for the next session

1. Phase A backend end-to-end test (install → one URL → `upfront_run` → report → calibration → full
   uninstall, proven with `find ~/.hermes -iname '*upfront*'`).
2. Phase B: user installs via Capabilities → Plugins; header must read `build 0.3.0 · ui1`.
3. Screenshots → `assets/`, `hermes plugins validate`, repo public, 40-hex SHA pin, catalog PR.

---

## Fetch fix — the Arete page (shipped, pre-Phase-A)

Found by measuring the real source of nousresearch.com/arete (1.66 MB, supplied by the user) against
`upfront.fetch`, not by reasoning about it.

**Two stacked defects, measured:**

| | before | after |
|---|---|---|
| bytes read | 200,000 (12% of page — all `<head>` + inline SVG badges) | 2,000,000 |
| tokens the model saw | 3,230 | 1,998 |
| SVG path-coordinate junk | 3,211 tokens (**99.4%**) | 179 (9.0%) |
| plain words | 14 | 1,902 |
| article prose reachable | **none** — body starts at ~1.5 MB | 12,610 chars, all body markers present |

1. `MAX_BYTES = 200_000` truncated every modern marketing/blog page to its `<head>`. The cap now
   bounds memory only; the real gate is `PROSE_MIN`.
2. `<svg>` geometry was never stripped, so icon path data (`M178.187 0H21.8099C9.76…`) survived
   tag-stripping as thousands of prose-shaped tokens.
3. Guard added: a page yielding under 150 prose chars returns `None` instead of a document, so the
   run is honestly **degraded** rather than reviewed off a title tag. Calibration: real page 9,210
   prose chars, junk page ~20.
4. `html.unescape` in `_clean` — `&#x27;` and `&amp;` are markup, not prose.

**Verified:** `tests/test_fetch.py` 7 passed (SVG stripped, 1.5 MB body survives, junk page rejected,
entity decode); full suite **69 passed**; `node --check` clean.

**Consequence for the demo:** the earlier Arete run was graded off a page title and 3,211 coordinate
strings. It must be re-run before any of its numbers are quoted.

---

## Blue must be earned (shipped 2026-11-09)

The report's one remaining lie. `sea_state()` derived Blue from *the absence of objectors among named
stakeholders*, so a document naming no opponent at all — the Arete-27B page — was printed as
"Blue ocean": an empty room described as open water.

**Rule now enforced:** blue requires a named party with an **assessed capacity to block** (≥0.5) who is
not contesting, and the `why` names them. With no such party, or with nobody's capacity assessed, the
state is **insufficient input** — grey, off the red/purple/blue axis, with the reason on screen.

| Change | Where |
|---|---|
| `Persona.capacity` (0..1, `None` = not assessed) | `models.py` |
| extraction asks for capacity, never guesses (`_unit`) | `ingestion.py` |
| the gate + `INSUFFICIENT` state + `CAPACITY_MIN` | `scoring.py` |
| off-axis chip showing the reason, not three unlit pills | `desktop/plugin.js` |
| 7 cases + the legacy test that encoded the lie | `tests/test_blue_earned.py`, `tests/test_sea_state.py` |
| UI coverage for the off-axis branch | `tests/test_ui_sea.py` |

**Verified:** 78 tests passed, `node --check` clean. "Assessed as powerless" and "not assessed" are
different facts and the code now distinguishes them — the second one can never produce blue.


---

## Desktop UI — Recent block + graphical polish (shipped 2026-11-09)

First pass over `desktop/plugin.js` at the desktop-app test gate. Two real rendering defects found by
reading the generated SVG, plus the requested polish.

**Fixes (defects, not taste)**

| Defect | Cause | Fix |
|---|---|---|
| Graph edges invisible | `stroke="var(--ui-border)"` was set as an SVG **presentation attribute**; `var()` is invalid there, so the stroke fell back to `none` | moved to `style` (`stroke`, `strokeWidth`, `strokeDasharray`) |
| Node labels unreadable in dark theme | `fill="var(--ui-text)"` — same problem, defaulted to black on the dark `--ui-bg` | `style: { fill: 'var(--ui-text)' }` |
| Live graph had no edges during a run | `started()` sets `result` to null, so `result?.graph?.edges` was always `[]` — the gap-repair plan's "reuse the last edges" never had edges to reuse | remember the last run's edges in `lastEdges` state, set in `openRun()` |
| Report leaked `**asterisks**` | the 6-rule Markdown subset had no inline handling | `inline()` splits on `**bold**` and renders `<strong>` |

**Polish**

- **Recent** block above **Past reviews** — the two latest runs, accent border, shared `RunRow`.
- **Competition axis** is now a real red→purple→blue gradient bar with a marker at the active state,
  plus the text label (colour is never the only signal).
- **Friction bar** — taller, rounded, mid-point tick, `n/100` label.
- **Timeline** — pill row (30m → 48h) instead of a plain `<select>`; the note follows the selection.
- **Claim scoring** — the ✓/✗ buttons take a green/red fill when selected, not just bold.

**Verified:** `node --check` clean; a headless render smoke test (stubbed `@hermes/plugin-sdk` +
`react`) renders the page, the modal, and a finished result — asserting the SVG graph, the gradient
axis, the styled SVG stroke/fill, the Recent block, and `<strong>` in the report. BUILD → `0.3.1 · ui2`.

---

## Desktop UI — the Kanban look (shipped 2026-11-09)

The page now uses the app's own design language instead of hand-rolled controls, so it
reads as part of Hermes rather than a page inside it.

**What changed**

- The form is a real `Dialog` (the Kanban new-task dialog shape): `Input`, `Textarea`,
  `Select`, `Switch`, `Button`, and the `FIELD_LABEL` / `Section` / `Callout` chrome.
- The results page is built from Kanban's card atom: elevated fill, hairline border,
  optional coloured left rule, `Badge` for the sea state, `Callout` for the failed-run
  banner and the "what you get" panel.
- No hardcoded colours left in the controls — theme tokens and the primary button.

**Verified:** `node --check` clean; the headless render smoke test renders the page, the
dialog and a finished result, asserting the SVG graph, the gradient competition axis, the
Recent block, the claim rows and `<strong>` in the report. BUILD → `0.3.2 · ui3`.

---

## Rename — the product is "Upfront Prediction" (2026-11-09)

The display name is **Upfront Prediction** everywhere a user reads it: the sidebar nav
(`PRODUCT_NAME`), the plugin card (`plugin.yaml` `label`), the catalog entry `title`, and
the README title. The plugin `id` stays `upfront` — tool names, the data dir and saved
runs' provenance do not change.

BUILD → `0.3.3 · ui4`.

---

## The challenge player is the one who can stop you, not the one who shouts loudest (2026-11-09)

Found in a real backend run before the desktop test: a price-rise document named `Enterprise IT`
(role blocker, capacity 0.9, stance −1.00) *and* `Free tier users` (stance −1.00, capacity 0.0).
The report named **Free tier users** as the veto player — the angriest party, not the one with a
lever. "Who can challenge" is stance x power, and the old `find_blocker` only looked at stance.

- `find_blocker` now ranks negative stakeholders by `stance x capacity` (unassessed capacity gets
  0.5 — unknown is not zero). `Enterprise IT` wins that run; `Free tier users` no longer does.
- `sea_state` only calls a hard veto when the blocker both dislikes the move (`< -0.7`) **and**
  has capacity `>= 0.5`. Anger without a lever now reads as friction, not as a veto.
- `sea_state` also counts a coalition as a *blocking camp* only when someone in it can actually
  stop the move (dislike `< -0.3` **and** capacity `>= 0.5`). A room with Finance against and a
  couple of resellers asking for a fixable detail was printing Red on "2 blocking camps"; that is a
  contest with winnable ground, which is Purple. Unknown camp members still count as a fight —
  never guess a fight is harmless.
- Possessive fix in the best-response copy: `Enterprise Resellers'` rather than `Resellers's`.
- Five tests added (`tests/test_scoring.py`); suite 83 green.

**Sample rewritten for the demo.** The sample had drifted into a document where every named party
supported the move, so the demo produced "Blue ocean — nobody is contesting this": the weakest
possible rehearsal. It now carries one party with a lever and conditions (Finance wants the free
window capped), one fixable complaint (resellers ask for a protection clause), one compliance
condition (Legal) and the parties who gain. That is what the product actually does — it is not a
forecast, it is the fight before the fight.

BUILD → `0.3.4 · ui5`.

---

## "LLM not bound in backend" — the two halves never shared the model (2026-11-09)

First live run in the desktop app failed with `LLM not bound in backend. The agent plugin half
must load and call plugin_api.set_llm(ctx.llm)`. The desktop half was fine (header read
`build 0.3.4 · ui5`); the binding was architecturally impossible:

- The agent half is imported by the agent plugin loader under one module name; `dashboard/
  plugin_api.py` is imported **standalone from its file path** by the dashboard loader under a
  different name. Two module objects, two separate globals — `set_llm` wrote to a copy the routes
  never read.
- `from .dashboard import plugin_api` also failed silently (`except Exception: pass`), so even the
  *intended* binding never ran. That swallowed exception is why this surfaced as a runtime error
  instead of at load time.

Fix: `upfront/llm_binding.py` holds the binding in a synthetic module kept in `sys.modules` — the
one namespace every import name shares — so whichever way either half is imported, they see the
same object. `register(ctx)` binds through it and logs a failure instead of hiding it;
`plugin_api._llm()` reads from it. Four tests (`tests/test_llm_binding.py`) load `plugin_api.py`
by file path, exactly as the app does, and prove the binding crosses the import boundary.
Suite 87 green.

---

## The routes can now reach the model without the agent half (2026-11-09)

After the `sys.modules` holder fix, a **freshly restarted** desktop backend still failed with
`LLM not bound in backend`. That settles the architecture question: `register(ctx)` and the
FastAPI routes are not guaranteed to share a process, and no in-process trick — module global,
`sys.modules` holder, registry — crosses a process boundary.

`upfront/host_llm.py` gives the routes their own way to the model: it reads the provider, base URL
and rotating agent key from this machine's own `~/.hermes` (on every run — the key rotates) and
speaks `POST {base}/chat/completions` with **stdlib only**, so no `openai` SDK version can break
it. `_resolve_llm()` order: agent binding → agent copy under another name → local host config →
a plain "No model available" naming the reason. Every resolution writes one line to
`<plugin-data>/desktop-debug.log` with the pid, so "Run failed" is diagnosable in one read.

**Verified for real:** `build_host_llm()` resolved `reflection/beam-1.0-501b-a23b:free` on
`inference-api.nousresearch.com` and returned a live completion. Suite 89 green.

This is the floor, not the preferred path: the agent binding stays first because the host owns
provider routing and token refresh.

---

## The result page answers the question, and the graph explains itself (2026-11-09)

The first real user ran a full 24h review and reported: *"40 minutes and I still don't know
what was done or provided… the numbers mean nothing, what does the graph mean."* The run itself
was sound (`degraded False`, model path `host-config` confirmed in the debug log) — the screen
was not. Four defects, all fixed:

- **No answer at the top.** The page opened with the raw audit: Stakeholders, then a Provenance
  section repeating it, then Key events, then ten claims. Now a `VerdictCard` leads: competition
  read, friction with a plain-language meaning ("A quiet room…", "A fight…"), **who can challenge
  this** with their condition and their power, and **so what do I do**. The audit moved behind
  "show the full audit".
- **The graph was decoration.** Nodes were a radial blob with no axis, no legend, no size cue.
  Now: position = stance on a labelled axis (against → behind it), **size = power to stop it**,
  a dashed ring marks **your side** (parties grounded in the decision document), and
  **coalitions are drawn as hulls** — GraphRAG's community idea applied to the party graph, so
  the reader sees camps form instead of dots.
- **Inject looked dead and had no visible effect.** The button was disabled until text existed,
  with no explanation. It is now always available, says what it does, and after a run reports the
  impact: `Injected ✓ — Finance +0.3 · Legal +0.2`.
- **The form promised nothing about time.** Free models are rate-limited; the user spent 30
  minutes on a 24h review with no warning. Timelines now carry realistic free-model ETAs
  (30m ≈ 2–5 min … 24h ≈ 15–30 min) and selecting a free model shows a Callout.

**Speed.** Parties act concurrently within a round (they only read the shared stance map), and
reflection is parallel too — 112 sequential calls become ~16 × one-call latency. Two tests
(`tests/test_parallel.py`) prove concurrency happens and results stay correct.

Backend: `/report` now returns the summary fields (recommendation, counter-moves, personas,
interventions, camps) so the page leads with the answer; graph nodes carry `capacity`.

BUILD → `0.4.0 · ui6`. Suite 95 green.

---

## The card and the marketplace listing (2026-11-09)

The installed-plugin card in Capabilities → Plugins renders only **name, version,
kind, provenance and the `description`** — no image, no author, no tags (checked in
`apps/desktop/src/app/capabilities/plugins/plugins-tab.tsx`). So the levers are the description
and the catalog entry.

- **Tagline.** Both `plugin.yaml` and the catalog entry now lead with *"See who can kill your plan
  before you ship it."* — the hook has to survive the first ~120 characters because that is all a
  card shows before the fold.
- **Logo.** `assets/logo.svg` — the stance axis with the ringed party who can stop the move. Used in
  the README; the marketplace `image:` stays the wide banner.
- **Banner + how-it-works redrawn** (`assets/banner.png`, `assets/how-it-works.png`, sources kept as
  `.html` for the next edit). The old ones still said "veto player" and "2–4 falsifiable calls" —
  terminology we retired. New copy: who can challenge / their conditions / testable claims.
- **Catalog entry fixed.** The draft declared `capabilities.tools` and `hooks:`; the catalog schema
  is `provides_tools` / `provides_hooks` / `provides_middleware` / `requires_env`. It also gained
  `platforms`, the new pinned SHA, version 0.4.0 and the second screenshot.
