# Roadmap — recommendations after the 2026-11-09 session

These are the build items that turn Upfront from "impressive demo" into "a tool people keep using".
Ordered by value-per-hour. Read with `docs/HANDOFF.md`.

---

## R1 — Auto-rescore at window close (highest value, ~1 session)

**Why:** the product's claim is a *scored track record*, but scoring depends on the user remembering to
come back after 48h. Nobody remembers. Every unscored run is a wasted claim, and the calibration
ledger stays empty — which makes the whole differentiator invisible.

**What:** claims become a to-do the system owns, not the user.

1. `reporting.due_claims(as_of=None)` — every run whose `created_at + window` has passed and that has
   no `verified` block. Returns `[{run_id, title, due_at, claims[]}]`.
2. `GET /due` on the backend returning that list.
3. Tool `arena_due()` — same payload, so an agent can act on it.
4. A bundled skill `upfront-review` (see R2) that instructs the agent: *when a review is filed, schedule
   a cron job at the window close that calls `arena_due` and asks the user to score it.*

**Acceptance:**
- `tests/test_due.py`: a run with `window="30m"` and a faked `created_at` 1h ago appears in `due_claims()`;
  a scored run does not. `arena_due` registered in the schema set.
- Manual: `HERMES_HOME=<tmp>` + engine run → `/due` returns 1 row, JSON fields as above.

**Do not** build a scheduler inside the plugin. Use Hermes cron (`cronjob` tool) — a plugin-owned timer
would break the "no background daemon" disclosure and the catalog's isolation expectations.

---

## R2 — Preset packs as plugin skills (fastest visible win)

**Why:** the recipes in the UI are prefilled *text*. As skills they become executable knowledge the agent
can load and follow, and they show up in `skills_list` — which is what makes a plugin feel like part of
Hermes rather than an app bolted onto it.

**What:** four skills under `skills/<name>/SKILL.md`, registered in `register(ctx)` with
`ctx.register_skill(name, path)` (namespaced `plugin:upfront-launch` etc.):

| Skill | Teaches |
|---|---|
| `upfront-launch` | how to brief a launch decision: what to paste, what evidence to demand, which timeline |
| `upfront-pricing` | price-change specific: grandfathering, churn risk, competitor framing |
| `upfront-deprecation` | sunset briefs: affected segments, migration path, notice period |
| `upfront-openweight` | licence/weights/evals briefs: compliance objections, community expectations |

Each: 40–80 lines, a checklist, one worked example, and the "not a prediction" boundary stated once.

**Acceptance:** `hermes plugins doctor <path>` still passes; `skill_view("plugin:upfront-launch")` returns
content; `plugin.yaml` does **not** need a new capability (skills are a normal surface).

---

## R3 — Decision record export (the retention hook)

**Why:** a technical user keeps artefacts next to the code. If the review becomes a file in the repo, it
gets read again, linked in PRs, and compared against reality by the people who ship.

**What:** `reporting.export_decision(run_id, out_dir="decisions")` writes `decisions/<slug>.md`:

```markdown
# Decision: <title>
- run: <run_id> · <created_at> · <rounds> rounds · model <model> · commit <code_commit>
- competition: Purple ocean (medium) — <why>
- friction: 47/100 ±3 · veto player: Enterprise IT (−0.70)
## Claims (score these)
- [ ] `a1b2c3d4` Enterprise IT is the binding constraint within 16 rounds.
## Verdict
_unscored_
```

Plus `GET /export/{run_id}` and tool `arena_export(run_id, out_dir?)` returning the path written.
When a verdict exists, the export fills `## Verdict` with it and appends the per-claim ✓/✗.

**Acceptance:** `tests/test_export.py` — after a run, export creates the file; it contains the claim ids
and the sea label; re-exporting after `mark_verified` includes the verdict line and does not duplicate.

---

## R4 — Model-aware run presets (small, do last)

**Why:** the cost line already shows the price; the missing link is a recommendation. `flash-class + 24h`
is the sensible default for a first pass, and `frontier + 48h` only when the decision is expensive.

**What:** one line in the form under the cost: *"For a first pass: a flash-class model at 24h. Spend on
48h and a bigger model only when the decision is expensive."* No new code paths.

---

## Test protocol — end-to-end, in this exact order

The user installs the UI copy themselves; the agent must never leave an install behind.

### Phase A — backend test (agent installs, tests, uninstalls)

1. Agent: `hermes plugins install trillionverselabs-boop/strategic-arena --yes-deps --enable`
   (private repo: uses the `gh` login or `GITHUB_TOKEN` in the profile `.env`).
2. Agent: `hermes plugins list | grep upfront` → expect `enabled`, version `0.3.0`.
3. User supplies **one URL** (repo README, blog post, or article).
4. Agent: `arena_run` with `title`, `urls: [<that URL>]`, `window: "6h"`.
   Report **the real returned JSON**: friction, uncertainty, confidence, sea (state/level/why),
   veto player, claims (kinds + text), `degraded`, and the run id.
5. Agent: `arena_report(run_id)` → confirm the markdown has the competition line, claims section,
   and no `DEGRADED RUN` banner. `arena_calibration()` → counts.
6. Review together: does the output make sense for that URL? If not, record *why* before changing code.
7. Agent: **uninstall completely** — `hermes plugins remove upfront`, remove
   `~/.hermes/desktop-plugins/strategic-arena`, uninstall `hermes-upfront` from every managed venv, then
   `find ~/.hermes -iname '*upfront*'` must print nothing (see HANDOFF do-not list).

### Phase B — user installs and tests the UI

1. User: desktop → Capabilities → Plugins → install `trillionverselabs-boop/strategic-arena`, enable.
   Expect **one** consent prompt for `llm.model_override`.
2. Header must read `build 0.3.0 · ui1`. If not: ⌘K → Reload desktop plugins.
3. Recipe → `Use a sample` → timeline `24h` → Run. Expect: competition axis (Purple), friction bar,
   named veto player, graph, formatted report, 4 claims.
4. Inject a counter-move mid-run; confirm a `<god>` event appears in the report.
5. Score a claim ✓/✗ and set a verdict; reopen the run and confirm it persisted.
6. Re-run the same title at `30m`; confirm the comparison panel appears with a reading.
7. Capture **real** screenshots here → `assets/`, then add to the catalog `screenshots:` list.

### Phase C — submission

`hermes plugins validate /home/lisacore/work/upfront --install-deps` → fix all failures → remove the
editable installs it creates → repo public → pin the 40-hex SHA in `docs/catalog-entry.draft.yaml` →
PR to `NousResearch/hermes-agent` before **Nov 11, 5PM EST**.

---

## R5–R9 — the document reader (see `docs/PRODUCT.md`)

R1–R4 made the tool keep its promises. R5–R9 make it *read the document*, which is the difference
between a review tool and a strategy instrument. Full spec, paper mapping and rule constraints live in
`docs/PRODUCT.md`; the build order is R5 (Brief extraction with spans) → R6 (stakeholder/field split +
blue-must-be-earned) → R7 (field read) → R8 (persona fidelity, reason-action log) → R9 (MASS failure-mode
harness).

**Sequencing constraint:** the catalog PR is due Nov 11 5PM EST. Ship 0.3.x (fetch fix + blue-must-be-earned)
first; land R5–R9 as 0.4.0 with its own SHA-bump PR.

**Before that PR:** declare `python_dependencies` with floor *and* upper bound (`pydantic`, `fastapi`) —
`plugin.yaml` currently declares none while importing both, and a reviewer will ask (rule 10). Deferred
deliberately: it changes install topology (a managed venv appears), so it happens after the demo run,
not before it.
