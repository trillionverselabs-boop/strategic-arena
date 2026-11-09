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
| R2 — preset packs as skills | not started | — | — |
| R3 — decision record export | not started | — | — |
| R4 — model-aware presets | not started | — | — |

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

## Open items for the next session

1. Phase A backend end-to-end test (install → one URL → `upfront_run` → report → calibration → full
   uninstall, proven with `find ~/.hermes -iname '*upfront*'`).
2. Phase B: user installs via Capabilities → Plugins; header must read `build 0.3.0 · ui1`.
3. Screenshots → `assets/`, `hermes plugins validate`, repo public, 40-hex SHA pin, catalog PR.
