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
