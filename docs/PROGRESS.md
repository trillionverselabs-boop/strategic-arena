# Progress log — Upfront

Running log for cheap handoffs. Newest state at the top of each item; one entry per shipped item.
Truth for state and gates: `docs/HANDOFF.md` + `docs/ROADMAP.md`.

Gates (both must pass before every commit):

```
# the runner copies the tree to a temp `upfront/` and honours PYTHON=
PYTHON=<a venv with pytest fastapi pydantic httpx pyyaml> ./scripts/test.sh -q
node --input-type=module --check < desktop/plugin.js
```

Marketplace/submission state lives in `docs/MARKETPLACE.md`; this PR's specifics in
`docs/CATALOG-PR-153750.md`.

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
  0.3.0 and stale "Strategic Arena" description replaced.

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

## Rename — the product is "Strategic Arena" (2026-11-09)

The display name is **Strategic Arena** everywhere a user reads it: the sidebar nav
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

---

## Cancel, and text you can actually read (2026-11-09)

The retest screenshot showed `build 0.3.4 · ui5` — the desktop half had never updated, so the
run was on the old UI. Two fixes, both real:

- **Cancel.** A run that takes 15–30 minutes needs an exit. `POST /cancel/{run_id}` sets a flag
  honoured *between* rounds (the in-flight round finishes, then the run stops), the status
  becomes `cancelled`, and **nothing partial is ever written to history** — Past reviews only
  ever holds complete runs. The UI shows a `Cancel run` button beside the inject row and a
  "Run cancelled" note instead of a spinner that never ends. Four tests in
  `tests/test_cancel.py`, including the no-write guarantee.
- **Contrast.** The user could not read the screen. The desktop's background bleed-through is a
  setting they like, so the fix is on the text: node labels are now near-white (`#f2f4f7`), 12.5px,
  semibold, with a dark halo (`paintOrder: stroke`) so they survive over busy backgrounds; axis
  labels, caption, legend, progress line, "loudest objector" line and result-page reasons all moved
  off `--ui-text-tertiary` onto `#c7cdd6`. Five more UI guards.

BUILD → `0.4.1 · ui7`. Suite 101 green.

**Update path (the reason the retest ran the old UI):** the desktop half lives on the user's
machine. `plugins update` on lisacore refreshes only the backend copy. The reliable path in the
app is **Uninstall → Install from Git** (which installs both halves at the current commit), then a
full quit and relaunch.

---

## Uninstall leaves 18 paths behind — shipped a purge with a proof (2026-11-09)

`hermes plugins remove` deletes the plugin tree, config, aliases and OAuth grants, then stops
(`hermes_cli/plugins_cmd_remove.py` → `_remove_user_plugin`). It never touches the dependency
environments that `--yes-deps` built, so an **editable `hermes-upfront` survives in each venv**,
along with the `workspace/plugin-sources/upfront-*` snapshot the build came from. Measured twice on
a real machine: **18 paths** survive.

That snapshot is the dangerous one: a later install can build from it, which is exactly how a
"reinstalled and the UI is still old" bug happens.

`scripts/uninstall-clean.py` (described in `docs/UNINSTALL.md`, linked from the README) fills the
gap: it pip/uv-uninstalls where the env has a package manager, deletes the editable files directly
where it does not (uv envs often ship without pip), prunes emptied cache dirs, and **ends with the
proof line** — it re-scans and exits non-zero if anything survived. `--keep-data` preserves
`plugin-data/upfront` (run history). Three tests cover dry-run, full purge and keep-data.

Verified end to end on this machine: install → built-in remove (18 paths left) → purge → `find
~/.hermes -iname '*upfront*'` returns 0. Suite 104 green.

---

## Admission rule 11: the model now comes from the host facade, not auth.json (2026-11-09)

A compliance pass against the catalog submission rules found one real violation, and the
validator cannot see it (it scans for dangerous patterns, not for "did you read a credential
store"):

**Rule 11** — *"A plugin never reads `.env` files, Hermes's `auth.json`, another tool's login …
or any other credential store directly."* `host_llm.py`, written to fix the desktop "LLM not
bound" bug, read `~/.hermes/auth.json` and built an OpenAI client with the agent key. It worked;
it also would have been a decline at review.

Fix: `build_host_llm()` now returns a shim over **`agent.plugin_llm.PluginLlm`** — the exact
object `PluginContext.llm` builds (`hermes_cli/plugins.py` → `PluginLlm(plugin_id=...)`), so
the routes get host-owned credentials, the per-plugin trust gate, fallback and usage accounting.
The plugin never holds a token and never builds an `Authorization` header.

Verified with a live call through the real interpreter:
`build_host_llm().complete("Reply with exactly: OK")` → `OK`.

Also removed `tools/probe_free_models.py`, a dev probe that read `auth.json` — it is not runtime
code, but a reviewer reads the whole pinned tree. `tests/test_admission.py` now guards the line:
no credential-store reads, no subprocess/eval, in any shipped module (docstrings excepted).

**`hermes plugins validate --install-deps` now passes end to end** (dependency resolution
included) — the earlier failure was stale duplicate `plugin-sources/upfront-*` snapshots from
earlier installs, which is exactly the residue `scripts/uninstall-clean.py` exists to clear.

Suite 112 green.

---

## A refused model override degrades instead of failing (2026-11-09)

Selecting a non-free model in the picker failed the run with a generic "the model call failed".
Reproduced: `PluginLlmTrustError: Plugin 'upfront' cannot override the model` — the host gates
model overrides behind `plugins.entries.<id>.llm.allow_model_override`.

Verified in the source that this is a **core mismatch**, not our bug: the consent screen records
`plugins.entries.<id>.granted_capabilities`, but `PluginLlm._resolve_trust_policy()` reads only the
legacy booleans. Granting `llm.model_override` in the UI therefore need not open the gate.

What the plugin does now: on `PluginLlmTrustError` it drops the override for the **rest of the run**
(no failed call per round), runs on the active model, and writes a note the result page shows —
"your model choice was not permitted by the host, so this run used your active model; to enable the
picker set `plugins.entries.upfront.llm.allow_model_override: true`". Two tests
(`tests/test_trust_degrade.py`).

Also: the real exception now reaches the user and `desktop-debug.log`; the "answered but not JSON"
path is named too, so a free model that rambles is distinguishable from an unreachable model.

BUILD → `0.4.2 · ui8`, version 0.4.3. Suite 114 green.

---

## The form says what the host will actually do (2026-11-09)

Model choice was gated by the host and nobody found out until the run failed. Now it is stated
before you commit:

- **`GET /model-access`** reads exactly what the enforcer reads (`plugins.entries.upfront.llm`)
  and returns a boolean plus the config key — no credentials, just a permission.
- **The form warns when the picker will be ignored**: "The host has not granted model choice —
  this run will use your active model instead of <model>. To let the picker choose, add
  `plugins.entries.upfront.llm.allow_model_override: true` to config.yaml (a host permission,
  not a plugin setting)."
- The **cost line** tells the truth too: `FREE (active model — choice not granted)` instead of
  quoting a price for a model that will not run.
- The model field's own hint says it up front.

BUILD → `0.4.3 · ui9`, version 0.4.4. Suite 115 green.

---

## The page tells the story, not the measurements (2026-11-10)

First real screen grabs came back with one verdict: *"the circles with numbers mean
nothing."* Correct diagnosis. The page showed a graph, a friction bar and a stakeholder
list — all true, none of it saying what would happen to the user's decision, and
nothing a bystander could watch for the length of a 48-hour run.

**What changed, and why each piece exists:**

- **Home** is now an identity line + one primary action + three steps + four value
  tiles, and the run history moved to the lower third as compact cards plus a capped
  list (`test_history_does_not_eat_the_page`).
- **The room** is an ordered board: parties sorted from *will block it · −1* to
  *behind it · +1*, each with a bar measured from a labelled centre, a spoken power
  word (*can stop it / can slow it / can only complain*), and their own reason. The
  numbered dots are gone for good.
- **Live runs** read as a feed: a round track with a "you are here" marker, an
  estimated time remaining, the loudest objection, the statements the parties just
  made, and the board beside the injection console. A watcher has something to read.
- **Results** lead with the call: a headline sentence built from the blocker and the
  heat band, then *who can stop it / what they need / your best move*, then the room,
  the **movement chart** (positions over rounds), the **transcript** grouped by round,
  and the scorecard with a countdown and the running record.
- **Scorecard** is now *The call, frozen*: a bet slip, not a checklist — it shows when
  to score, asks ✓/✗ per claim, and prints the aggregate record so tracking has a
  visible payoff.
- **Warmth in the engine:** the stakeholder prompt now requires first-person speech
  and forbids third-person reportage (`tests/test_events.py`). This is what turns a
  lab printout into people you can plan against.
- **Backend for all of it:** `Snapshot.events` (the round's own statements) is now
  emitted on every progress tick and exposed as `GET /events/{run_id}` with the
  per-round stance series; `GET /status` also carries `movers` and `previous` so the
  page can show what an injection actually moved.
- **Honesty fixes:** an off-axis competition read now says *why* instead of lighting
  an unlit axis (`test_ui_sea.py`); `text-(#hex)` — an invalid Tailwind form that
  silently renders nothing — was replaced with real tokens, and a guard fails if it
  returns.

**Verified:** 143 tests green; `node --check` clean; the page rendered end to end
against real run data in a harness (home, live, results) and reviewed for layout,
overlap and clipping before shipping. Suite 143 green. BUILD → `0.5.0 · ui12`,
version 0.5.0.

**Not verified:** the real desktop window. The user must confirm the header reads
`build 0.5.0 · ui12` — see `docs/DESKTOP-UPDATES.md` for why the server-side update
cannot prove that on its own.

---

## The Reload button told the truth (2026-11-10, later)

The user reported the Reload button and ⌘K both "don't work", and rightly objected
to restarting the app every time. Diagnosis, after reading the desktop loader:

- **The button only reloaded the page.** The app reads `desktop/plugin.js` from the
  machine the window runs on, so a page reload can never pick up a new build — and
  the old banner literally said "Press Reload UI — it republishes the installed
  copy". That instruction was impossible, which is why the button read as broken.
- **⌘K was never broken either.** `Reload desktop plugins` re-reads known entries
  from disk; if the file on the window's machine is unchanged, it faithfully shows
  the old build. Nothing new to read.
- **Neither fix needs a restart.** The app fs-watches the copy
  (`watchDiskPluginFile`) and hot-reloads in place on save; and Install from Git
  with the **Desktop** target makes the app do the copying itself.

**What changed:**

- `Reload UI` → **Reload page**, with a title that says what it does.
- A stale window now gets an **"this window is behind"** card: `window X → installed
  Y`, **Update in the app** (→ `host.navigate('/capabilities?tab=plugins')`), and
  **Download the UI file**.
- `GET /ui/download` writes the shipped `desktop/plugin.js` to a stable path in the
  plugin data dir and returns it for the **gateway save bridge**
  (`captureGatewayFileDownload`), which streams the bytes through the native save
  dialog — the sanctioned way to hand a file to a remote window. Feature-detected:
  a missing SDK export would be a fatal import and a blank page.
- `/ui`'s hint no longer says "reload the page"; it names the two things that work.
- `docs/DESKTOP-UPDATES.md` rewritten around what each action actually does.

**Verified:** 150 tests green (new `tests/test_ui_download.py` covers the served
bytes being identical to the repo file, the path being one the gateway may
download, and the honest hint); `node --check` clean; the download route returns
88,367 bytes byte-identical to `desktop/plugin.js`, and the path resolves through
the host's managed-file guard (`_is_sensitive_path` false, `_resolve_managed_path`
returns it unchanged).

**Not verified:** the save dialog on the user's machine. That is the one step only
they can perform.

---

## The run list is one line, and the plugin stopped updating itself (2026-11-10, later)

Two things in one round: a UX request from the user, and an admission-rule audit
that caught a regression I had just introduced.

**1. Every run is now one line** — title, a miniature of the room (a dot per party:
position = stance, size = power), verdict band, blocker, heat, scored state, age,
then a chevron. Six by default with `show all`, and the whole block sits in the
lower third so the hero can breathe. The three tall cards and the second list are
gone (`RunCard`, `RunRow` deleted; `MiniRoom` + `RunLine` + `RunTableHead` added).

**2. Rule 03 caught me.** The previous round added "Download the UI file" — a save
bridge that handed the user the plugin's own desktop half. It was manual and it
only copied a local file, but rule 03 names it exactly: *"no self-updating code …
in-app 'check for updates' … strip it from the catalog build."* Removed:
the `/ui/download` route, the `/ui/refresh` call, the save bridge import, and the
button. A stale window now gets the honest diagnosis and **Open plugin settings**
(the app's own update path), which is where the update belongs.
`tests/test_no_self_update.py` fails if any of it comes back — including a raw
`fetch(` in the shipped UI.

**3. The model picker was telling the truth.** `plugins.entries.upfront.llm.
allow_model_override` had been reset to `entries: {}` in the profile config, and
the gateway serves the default home, which had no such key — so the host really
had not granted model choice. Added the documented key to `~/.hermes/config.yaml`
(host config, an operator action, not plugin behaviour). The enforcer resolves the
policy per call, so it took effect with no restart:
`_resolve_trust_policy("upfront").allow_model_override` → `True`, and
`GET /model-access` → `{"allowed": true}`. The plugin still only *reads* the
permission — rule 6/13 stay satisfied, and `tests/test_trust_degrade.py` still
covers the honest fallback when it is absent.

**Verified:** 150 tests green; `node --check` clean; `hermes plugins validate`
passes; the one-line table rendered against an 8-run fixture and checked column by
column (title / room / verdict / blocker / heat / scored / age / chevron).
BUILD → `0.5.1 · ui13`, version 0.5.1.

---

## Roundtable, zones, both loudest voices, and the provenance graph (2026-11-10, later)

The model switch still would not take. It was not the permission this time — it was
*when* the plugin read it:

```python
allow_override=getattr(base, "allow_override", False)   # captured at register()
```

The adapter is built once, at session start, so a permission granted afterwards
reached `/model-access` but never a run. Now one helper resolves the key **per
call** — `_override_allowed()` — and `_run_llm()` is the only place a run's
adapter is built, so the picker and the run cannot disagree. `tests/test_model_gate.py`
covers the exact bug: the permission flips after registration, the run still
asks for the picked model, and a denied permission never sends `model` at all.

UI, in the same round:

- **"Rehearsing" → "Roundtable in session"**, and the closing line is "Closing the
  roundtable — writing the call". The product is still a rehearsal; the live
  object is a roundtable.
- **+ New review** is the accent button again, matching the entry screen.
- **Three named, counted groups** above the room board — *will block it · 2*,
  *undecided · 1*, *behind it · 2* — each with a one-line meaning, instead of a
  colour legend. The meters now run faint→saturated from the neutral line, so
  depth reads as strength, not just direction.
- **Both loudest voices**, quoted, live and in the results: loudest against it and
  loudest for it, with the sentence each actually said.
- **"What ends this objection"**: the blocker's condition verbatim, then *Bring:*
  — the artifact their own words point at (licence → the signed paper, budget →
  a capped number in writing, clause → the drafted term). Explicitly derived, with
  the disclaimer that the run adds no facts.
- **"What each party is standing on"** — a provenance graph: cited spans on the
  left, parties on the right, an edge per citation. It answers "why is Legal
  objecting" with the line Legal is standing on, and shows when three parties are
  arguing from the same sentence.

**Honest limit, now visible:** the graph is thin because each party currently
carries one grounded reason, so a 5-party run collapses to ~2 cited spans. That is
an extraction-depth problem, not a drawing problem — the engine should return 2–3
cited reasons per party. Next round.

**Verified:** 154 tests green; `node --check` clean; live board, results page and
the graph rendered against real run data and checked for overlap/clipping.
BUILD → `0.5.2 · ui14`, version 0.5.2.

---

## The leverage ledger, and the palette (2026-11-10, later still)

**What ships:** `leverage.py` computes what each party is *worth* — exact Shapley over
the room's own friction function. A party "not in S" is neutralised, not removed, so
the room stays the same size and the question stays legible: how much of this heat is
that party's, above a room where nobody objects? It is arithmetic, not a model call:
deterministic, order-independent, and exact — `sum(party) == total - baseline`, which
`tests/test_leverage.py` asserts. Route: `GET /leverage/{run_id}`, read-only.

Worked example (the live run in this profile, 5 parties):

| party | points | share | veto |
|---|---|---|---|
| Finance | +13.5 | 81.8% | outright |
| Legal | +13.5 | 81.8% | outright |
| Enterprise resellers | +1.4 | 8.5% | — |
| Enterprise CIOs | −4.9 | — | cools |
| Community fine-tuners | −7.0 | — | cools |
| **room** | **51.5** | | floor 35.0, attributable 16.5 |

Clear Finance alone → 35.2, Legal still vetoes. Clear Legal alone → 35.2, Finance still
vetoes. Clear both → 18.9, Quiet ground, nobody can stop it. That is the sentence the
page could not say before.

**A correction to the design mockup:** it showed a hatched "+6 coalition interaction"
in the heat. This engine's friction is additive in stances (an average plus two
counts), so that number cannot exist. It is not faked — the coalition is reported by
what it actually does (`kind: "veto"`): *clearing either one alone leaves the other's
veto standing; clearing both leaves none*. A guard test (`test_ui_ledger.py`) keeps a
fabricated interaction off the page.

**Palette.** Off the red/green stoplight and onto the blue the product reads as:

| role | hex | meaning |
|---|---|---|
| `BRAND.blue` | `#4c9bf0` | accent, primary action, "behind it" |
| `C.hold` | `#e5b54a` | undecided |
| `C.against` | `#d9538f` | will block it (rose, the warm end) |
| `C.own` | `#9b7be0` | parties named by your own document |

Blue and rose are a complementary pair with gold held between them: a cool→warm ramp,
not a stoplight. Direction is carried by the labels and by position, never by hue alone.
Text uses `textTone()` (74% hue, 26% white) because an 11px rose on near-black is a
smudge, not a word. The accent is scoped to the plugin page (`--ui-accent`) and the
three primary buttons carry the brand blue on their own instance — never by restyling
core UI.

**Found while verifying:** the preview harness's stub `Button` silently dropped
`style`, so the button rendered green locally while the real component would have been
blue. The stub now forwards `style` like the real one, and the computed colour is
asserted (`rgb(76,155,240)`).

**Verified:** 174 tests green; `node --check` clean; `hermes plugins validate` passes;
waterfall, ledger, concession cards and palette rendered against real run data and
critiqued twice before shipping. BUILD → `0.5.3 · ui15`, version 0.5.3.

---

## The ledger is live, and the timeline is explained (2026-11-10, last)

**Cost, measured — not estimated.** The ledger is exact Shapley over `2^n` subsets,
memoised, and it is CPU-only:

| parties | subsets | per ledger | vs one round (1–2 min of model time) |
|---|---|---|---|
| 5 | 32 | **0.51 ms** | 0.003% |
| 6 | 64 | 0.91 ms | 0.005% |
| 8 | 256 | 3.23 ms | 0.02% |
| 10 | 1024 | 12.9 ms | 0.07% |
| 12 | 4096 | 53.9 ms | 0.27% |
| 16 (sampled, 2000 permutations) | — | 162.6 ms | 0.8% |

A round costs one model call per party. So **the ledger is free at any room size
this product will see** — which is why it is on the live page, not only on results.
`GET /status/{run_id}` now carries `leverage`; on a live run it is computed from the
stances as they stand, with capacity assumed (0.5), and the card says so:

> live estimate · capacity assumed until the room closes

**Timeline guidance, on the selection itself.** The modal no longer offers a bare
dropdown. It marks the standard (`24 hours — 16 rounds · recommended`), says what
each choice is best for, and prints the rule:

> Go longer only when the parties are external (regulators, partners, press,
> competitors), the move is public, or a veto player is dug in — longer buys
> movement, not more objections. Most rooms stop moving after 8–10 rounds, and the
> last 4 hours cost double.

**Previous reviews use the same colours** because the history rows draw from
`stanceTone()` and `frictionBand()`, which now read the brand palette; nothing in
the list is hardcoded. The one leftover was the heat gauge gradient, still
green→amber→red — now the same cool→warm ramp as the room.

**Verified:** 174 tests green; `node --check` clean; `validate` passes; live ledger,
timeline hint and the recommended tag rendered and confirmed in the harness.
BUILD → `0.5.4 · ui16`, version 0.5.4.

---

## Final polish before the demo (2026-11-10, late)

Four fixes from the screenshot review, all verified in the harness:

1. **The wait is alive.** Round 0 takes 30–60s (one call to read the input, one per
   party) and a static "reading your documents" read as a hang. A `WorkingBar` now
   sits under the round track: an SMIL shimmer that actually moves (one `<animate>`
   node, no injected stylesheet, no animation framework, stops on unmount), a staged
   label that advances with elapsed time — *Reading what you gave it → Naming the
   parties who will react → Working out who can stop it → Opening the arena* — and a
   ticking `32s · round 0 is the slow one` so nobody wonders if it died.
2. **One accent per surface.** The header CTA is now the highest-contrast action
   (white on near-black, `#f1f4f9`); actions inside a panel stay brand blue. The
   `Inject ⚡` button was the app's default green sitting next to a blue one — that
   is how a palette starts looking accidental. Verified: inject `rgb(76,155,240)`,
   header `rgb(241,244,249)`.
3. **Vocabulary.** "Change the situation" → **counter-moves**, and the step copy now
   says "inject a counter-move mid-run" instead of the old phrase.
4. **Reload page was lying.** It called `window.location.reload()`, which tears down
   the webview — losing the run you were watching — and cannot fetch a newer UI file
   anyway. It now remounts the page body (`key` on the root) and re-reads its data:
   a real reload of the view, no teardown. A test fails the build if
   `window.location.reload()` comes back.

**Marketplace copy synced.** `plugin.yaml` had `label: Strategic Arena` but the
catalog draft still said "Strategic Arena" and described a rehearsal. Title,
description and tags now match the brand; the manifest description leads with the
artifact framing. The plugin id, folder, tool prefixes, data dir and repo slug stay
`upfront` — renaming those breaks installs, the catalog pin and the desktop folder.

**Verified:** 202 tests green; `node --check` clean; `hermes plugins validate` passes;
round-0 screen measured with the live fixture (stage label, 32s tick, 1 animate node,
button colours).
BUILD → `0.6.1 · ui23`, version 0.6.1.
