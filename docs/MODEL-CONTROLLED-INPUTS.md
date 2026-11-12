# Model-controlled inputs — what happens if each one is hostile?

Every value below reaches this plugin from the model, not from the user. For each
one: what it can touch, what happens if it is hostile, and the test that proves it.
Run this table before every submission. A blank cell is a finding.

| Input | Where it comes in | What it can touch | If it is hostile | Proven by |
|---|---|---|---|---|
| `urls[]` | `arena_run` (`tools.py`) | outbound HTTP(S) | a link to `169.254.169.254`, a LAN host, or a redirect into the LAN — the fetched text goes back into the run | `tests/test_fetch_ssrf.py` |
| `documents[].content` | `arena_run` | model prompts, `log.jsonl`, report text | prompt injection; already disclosed, bounded by the prompt budget | `tests/test_ingestion.py` |
| `title` | `arena_run` | file names (`decisions/<slug>.md`), report headings | path traversal in the slug — `_slug()` strips everything non-alphanumeric | `tests/test_export.py` |
| `personas[].name` | `arena_run` | graph node ids, report text | graph/node names are ids, not paths | `tests/test_agents.py` |
| `run_id` | `arena_report`, `arena_export`, `/status`, `/report`, `/verify`, `/graph`, `/events`, `/claims`, `/leverage` | filesystem paths under `runs/` | `../` walks out of `runs/`; `mark_verified` could rewrite an existing `meta.json` | `tests/test_run_id_guard.py` |
| `out_dir` | `arena_export`, `/export` | filesystem write, any path | writes a `.md` anywhere the user can write | `tests/test_export_containment.py` |
| `verdict`, `hits`, `actual_friction` | `/verify`, `mark_verified` | `meta.json` fields | already validated (`right\|partial\|wrong`); `hits` is a claim-id map | `tests/test_verify.py` |
| `as_of` | `arena_due`, `/due` | timestamp parse | unparseable value is skipped, never guessed | `tests/test_due.py` |
| `limit` | `arena_history`, `/history`, `/compare` | slice size | bounded by a default of 20 | `tests/test_endtoend.py` |
| `inject.description` | `/inject` | model prompt, mid-run | prompt injection; already disclosed | `tests/test_injection.py` |
| session model (`host.state.model`) | form display; `ctx.llm` binding | which model serves the run | not a path or a network target — but a free/throttled model is a real failure mode, so the form states which model runs and what to do on a 429 | `tests/test_free_model_disclosure.py`, `tests/test_model_gate.py` |
| provider response (`HTTP 429`) | model call path | run length; the `degraded` flag | a rate limit is retried and spaced, and a run is branded degraded only above a failure share — never a silent short report | `tests/test_model_timeout.py` |

## Before a submission

1. Add a row for every new tool parameter.
2. For each row, write the test that proves the hostile case is handled — before
   the parameter ships, not after a reviewer asks.
3. If a row's answer is "nothing, it is unbounded", that is the finding.
4. Check the neighbouring labels: a disclosure is also a consistency pass. If a
   label promises something the routing logic refuses (a tier labelled
   "Recommended" that the suggestion logic never proposes), the disclosure is
   false in the other direction.
