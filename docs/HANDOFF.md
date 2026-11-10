# Handoff — Upfront (state as of 2026-11-09, HEAD `33c6776`)

Read this first in a new session. It is the shortest path from zero to productive.

## Where things are

| | |
|---|---|
| Repo (private) | `https://github.com/trillionverselabs-boop/upfront-test` |
| Local clone — **the only copy** | `/home/lisacore/work/upfront` (dir renamed so the package imports as `upfront`) |
| Frozen backup | `https://github.com/trillionverselabs-boop/Upfront-Plugin-Original` (remote `original`) |
| Plan (versioned) | `docs/plans/2026-11-09_upfront-gap-repair.md` |
| Positioning | `docs/POSITIONING.md` |
| Catalog entry draft | `docs/catalog-entry.draft.yaml` |
| **Recommendations + test protocol** | **`docs/ROADMAP.md`** (build order, acceptance tests, Phase A/B/C) |
| Test venv | `/home/lisacore/.hermes/profiles/charlene/cache/scratch/upvenv` (pydantic, fastapi, pytest, httpx, pyyaml) |

## What is built (all pushed)

- **Correctness** — model failure raises `SimulationError` instead of inventing `Stakeholder 1..3`; no stance drift on a dead model; `find_blocker` needs `< -0.3`; degraded runs are banner-flagged; one persisted record per run; profile-safe data root via `plugin_data_dir("upfront")`.
- **Checkability** — replication manifest per run; red/purple/blue competition axis; 2–4 frozen claims; per-claim scoring + friction error; calibration ledger; `run_pair()` counterfactual; GraphRAG claim extraction.
- **UI** — green `+ New review` pill → modal form (uppercase labels, inline help, recipes, "what should I paste?" table, sample, decision-OR-URL validation, 30m→48h timelines with notes, model picker with live prices and per-run cost), live graph + **Inject ⚡**, report as markdown, claim scoring, past runs, **cross-timeline comparison**.
- **Models** — live Nous catalogue (`inference-api.nousresearch.com/v1/models`, anonymous, 394 listed / 357 chat / 5 free), prices per million tokens, cached 6h; `llm.model_override` declared and probed.
- **Marketplace** — banner + how-it-works assets, long description, category, 5 declared tools, docs_url, known_issues.

## What is verified vs not

**Verified:** 36 tests green (fake LLM, throwaway `HERMES_HOME`); `node --check desktop/plugin.js`; `plugin.yaml` + catalog YAML parse; live catalogue fetch; README quickstart output reproduced by the engine (47.3 friction, Purple/medium, veto Enterprise IT −0.70, 4 claims).

**NOT verified:** the UI has never run in the desktop app. Every visual claim is unproven.

## Do-not list

- Do **not** install the plugin into the Hermes backend without removing it afterwards (`docs/plans/...` §5.2 has the uninstall drill).
- Keep exactly **one** copy on disk. Never copy `desktop/plugin.js` into `~/.hermes/desktop-plugins/`.
- Never read credentials for the model catalogue — it is deliberately anonymous.

## Next steps, in order

Full detail and acceptance criteria: `docs/ROADMAP.md`. The end-to-end test protocol (agent installs →
url → results → uninstall → user installs → UI test) is at the bottom of that file.

1. **Desktop test** (the gate). Install from the repo → enable (expect one `llm.model_override` consent prompt) → header must read `build 0.3.4 · ui5`. Then: recipe → sample → run `24h` → confirm Purple ocean, named veto player (never `Stakeholder N`), formatted report; inject mid-run; score a claim; re-run at `30m` and confirm the comparison panel.
2. Capture 1–2 **real** screenshots into `assets/` and add them to `screenshots:` in the catalog entry.
3. `hermes plugins validate /home/lisacore/work/upfront --install-deps` — fix every failure; then remove the editable installs (handoff §5.2).
4. Decide the **name** (deferred by the user; display name is one constant `PRODUCT_NAME`; the id stays `upfront`).
5. Go **public**, pin the 40-hex SHA in `docs/catalog-entry.draft.yaml`, open the PR to `NousResearch/hermes-agent`.
6. Deadline reminder: hackathon closes **Nov 11, 5PM EST**.

## Open decisions carried from earlier

- Final product name may change after completion — display name is one line; the plugin id is expensive to change.
- Sea-state middle is "Purple ocean" (competition: high red → medium purple → low blue, red on the left).
- Repo must become public for catalog admission (overrides the private-by-default rule for this one repo, by user decision at submission time).

## What a run will say — read this before the URL test

The gap between "the backend works" and "the report is honest" is now small enough to state exactly.
Check a run against this table instead of judging the prose.

| Situation | What the report must print | If it prints something else |
|---|---|---|
| the document names parties, none oppose, one has assessed capacity to block | **Blue ocean**, with the party named in `why` | a bug — blue was not earned |
| the document names no party who could contest, or nobody's capacity was assessed | **Insufficient input** (grey, off-axis) | a bug — that is the Arete failure returning |
| documents name an opponent | red / purple by friction, unchanged | regression in `sea_state` |
| the page yields under 150 prose chars | run marked **degraded**, no report written | fetch regression |

**Verified 2026-11-09:** `tests/test_blue_earned.py` (7 cases) + `tests/test_sea_state.py`; suite 78
green; `node --check` clean. The UI path for the off-axis state is covered by `tests/test_ui_sea.py`
but has **not been seen in the desktop app** — same standing caveat as every visual claim here.

**Still true after this fix:** the plugin reads a document for *parties named in it*. It does not yet
read it for the field — incumbents, displaced parties, counter-moves. A document about a product
launch will still read as a room, not a market. That is R5–R7 in `docs/PRODUCT.md`, not a bug.

**Test protocol for the next URL (unchanged):** run one URL end-to-end, quote the exact
`competition:` line from the report, then uninstall and show `find ~/.hermes -iname '*upfront*'`
printing nothing. Do not patch code mid-run; record defects instead.
