# Product — the end goal

**Upfront reads a document the way a strategist reads it, then tells you two things:
who can stop the move, and what it changes for everyone else.**

A review tool answers the first question. A strategy instrument answers both. Today Upfront answers
only the first, and it answers it from whatever the *user typed into the form* — which is why a real
document produced "blue ocean": the room was empty because nobody had been put in it.

---

## The pipeline (and what each stage must produce)

| # | Stage | Input | Output | Status |
|---|---|---|---|---|
| 0 | **Ingest** | URL, pasted text, or file | clean prose + title/date/author/links | fixed 2026-11-09 (`fetch`) |
| 1 | **Read** | clean prose | a `Brief`: the move, who makes it, the claims, named actors, constraints, numbers — **every field with a quoted span** | **missing — this is the hole** |
| 2 | **Roster** | `Brief` | 8–12 parties, each typed `stakeholder` or `field`, with capacity to block, incentive, hostility, quoted evidence | missing |
| 3 | **Simulate** | roster + brief | rounds of structured turns, reason-action log, frozen claims | exists (single-axis) |
| 4 | **Report** | run | **veto read** + **field read** (displaced, ranked counter-moves with timing, scoreable claims) | half |
| 5 | **Calibrate** | scored claims | hit rate, and only at n ≥ 10 may it be called evidence | exists |

Stage 1 is the whole user complaint. The form asks the user to do the reading; the document already
contains the answer, and the user should not have to retype a 1,900-word post into four fields.

### Stage 1 — what "read the document" concretely means

One structured extraction pass, producing a `Brief`:

- **move** — the decision being made, one sentence, quoted.
- **actor** — who is doing it (org, person), and what they control.
- **claims** — every factual assertion the document makes that could later be checked: `{text, span, date_if_any}`. These become the scoreable set. This is the single highest-value change: the document's own numbers (803 prompts, 2.32 → 2.98, 22% → 1%) become claims the calibration ledger can grade.
- **actors[]** — every named party, with role and quoted span.
- **constraints[]** — licence terms, law, contract, physics, budget. The things that decide "can it be stopped" before any human opinion does.
- **numbers[]** — prices, benchmarks, dates, headcounts, with spans.

**Hard rule: no span, no fact.** An item without a quoted span from the document is not extracted into
`Brief`; it goes into `assumptions[]` and is *labelled as an assumption in the report*. This is the
difference between analysis and fiction, and it is checkable at review time.

### Stage 2 — the roster, and why the split matters

- `stakeholder` — can say yes or no to the move. Feeds friction and veto.
- `field` — competitor, incumbent, displaced party, or beneficiary. **Never feeds friction or veto.**
  Their hostility is evidence the move *landed*; it feeds a displacement score.

`sea_state` may only print **blue ocean** when at least one `field` party with real capacity to contest
is named, together with the reason they can't stop it. Otherwise the report says **insufficient input**
— an honest answer, and the one that would have caught the Arete run.

---

## Where the research actually plugs in

Each paper earns its place by doing one job. None of them is decoration.

| Paper / skill | The job it does | Where it lands |
|---|---|---|
| **GraphRAG** (Edge et al.) — `graphrag-principles` | entity + relationship + **claim** extraction, chunking, community summaries | Stage 1. The `Brief` is a one-document mini-index: entities, claims, and a summary per section, not a full graph index — we don't need Leiden communities for one article. |
| **CAMEL** — `camel-multi-agent-roleplaying` | inception prompting, role cards, the critic/role-flip failure modes to avoid | Stage 3. Role cards for each party, and the anti-collapse check (agents must not all agree or all refuse). |
| **Generative Agents** (Park et al.) — `generative-agents-simulacra` | memory stream, recency+importance+relevance retrieval, reflection | Stage 3. A party's turn must be grounded in what it "knows" (its own span + its coalition), not in the whole document — otherwise every agent is omniscient and the simulation is theatre. |
| **OASIS** (1M agents) — `oasis-social-interaction-simulation` | action taxonomy, propagation, recommendation/attention dynamics, scale | Stage 3/4. Propagation is how a move reaches parties who weren't in the document: OASIS's diffusion model is what lets the field read say "this reaches procurement teams in 6 weeks". |
| **MASS protocol** — `multi-agent-social-simulation` | control scheme, structured outputs, **reason-action logs**, validation, the 8 failure modes | Stage 3 auditability + Stage 4 evidence. The 8 failure modes are the automated grill every run's artifacts must pass before a report is emitted. |

Two of these are load-bearing for the user's trust question rather than for the output: **MASS gives
auditability** (every score traceable to a logged reason and action) and **GraphRAG gives provenance**
(every extracted field traceable to a span). A report that can show both is a different product class
from one that shows a coloured map.

---

## What happens if we do this — honestly

| | today | after |
|---|---|---|
| user effort | retype the document into 4 fields | paste a link |
| input quality | user's summary of the document | the document |
| parties named | whoever the user thought of | whoever the text names, plus labelled inferred field rivals |
| claims scoreable | prose the user wrote | the document's own assertions and numbers |
| LLM calls per run | 1 + rounds | 3 + rounds (extract, roster, sim) |
| latency | T | roughly 1.5–2× T for the same window |
| failure mode to fear | empty room read as open water (what happened) | invented parties — controlled by the span rule |
| cost | model round-trips only | ~2 extra cheap calls per run; the sim dominates either way |

The honest risk: extraction adds an LLM that can *misread* the document. The span rule makes a misread
visible — a reviewer can check the quote — and the assumption label keeps inference from being sold as
fact. That is a strict improvement over a form where the user's own paraphrase was never checked at all.

---

## Catalog-rule constraints that actually shape the build

Read against the three published guides. These are the rules that bite, not the full list.

| Rule | Constraint on us |
|---|---|
| 03 — no self-updating code | Ship **no** updater in the catalog build. Updates only via SHA-bump PR + `hermes plugins update`. Nothing in `desktop/plugin.js` may fetch its own code. |
| 06 — declared capabilities must match | `capabilities: [llm.model_override]` is currently accurate. Adding URL fetching keeps it accurate (no capability to declare), but **any new privileged surface must be declared in the same commit**. |
| 10 — dependency policy | `plugin.yaml` declares **no** `python_dependencies` while the code imports `pydantic`. A reviewer will ask for a floor **and an upper bound** (`pydantic>=2,<3`). Fix before the PR. |
| 11 — credentials through Hermes | Already correct: `ctx.llm` with host-owned credentials. Never read a key from a file. Extraction must go through the same `ctx.llm`. |
| 08 — desktop stays inside the SDK | `desktop/plugin.js` imports only `@hermes/plugin-sdk`, `react`, `react/jsx-runtime`. Keep it that way; no `eval`, no DOM patching of app markup. |
| 09 — no core overrides | Skills register via `ctx.register_skill` (already). Nothing patches a core module. |
| 05, 01 — owner submission, human-merged | We are the owner of the repo; one `plugin-catalog/strategic-arena.yaml`, one PR, reviewed pin. |
| Before you submit | Public repo, `hermes plugins validate <path> --install-deps` green, screenshots in `assets/`, README rendered as the docs page. |

**Deadline logic:** the catalog PR is due **Nov 11, 5PM EST**. The document-reader rebuild is not a
two-day job and must not be rushed into that pin. Submit 0.3.x (fetch fix + "blue must be earned"),
then land the reader as **0.4.0** with its own SHA-bump PR. A listed plugin that improves is the
normal case the catalog is built for; a listed plugin that ships half a rebuild on a deadline is a
decline.

---

## Build order

- **R5 — Document reader.** `Brief` extraction with spans and assumptions; `arena_run` accepts a URL and fills the form fields itself. Fixture: the real Arete page. *Acceptance: the extracted brief names Alibaba/Qwen, Nous, the eval, and the 52.8M-token figure, each with a span; a junk page yields a degraded run, not a brief.*
- **R6 — Roster split + blue must be earned.** *(half shipped 2026-11-09: blue must be earned is live — see
  `docs/PROGRESS.md`; the stakeholder/field split is not built)* `stakeholder` vs `field`; sea state cannot be blue without a contestable party. *Acceptance: a run whose input names no opponent returns "insufficient input", never "blue ocean".*
- **R7 — Field read.** Displaced/threatened/enabled parties ranked, counter-moves with timing, field claims scoreable. *Acceptance: report section renders with ≥3 ranked parties and ≥1 timed counter-move, each traceable to a span or labelled inferred.*
- **R8 — Persona fidelity.** Role cards, information boundaries, persisted reason-action log per turn. *Acceptance: a turn's citations are a subset of that party's boundary; log is exportable.*
- **R9 — Validation harness.** The MASS 8 failure modes run as automated checks on every run's artifacts; a failing check downgrades the report to "draft" rather than shipping it.
