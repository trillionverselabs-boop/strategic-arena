# Models — free tier on the Nous inference API

Measured 2026-11-09 against `https://inference-api.nousresearch.com/v1/models` (396 models) with a live
key. Five models are zero-priced; each was exercised with a real request, not read off the catalogue.

## The five free models

| Model | ctx | structured outputs | reasoning | Measured | Verdict |
|---|---|---|---|---|---|
| **`reflection/beam-1.0-501b-a23b:free`** | 262K | yes (+tools, parallel) | mandatory | structured Brief, **7/7 spans verified**, 5.0 s, 4,072 tok, **$0** | **use for the report** |
| **`upstage/solar-mini4:free`** | 524K | yes (+tools, parallel) | optional (off = fast) | correct one-sentence read in 1.7 s, 2,902 tok, $0 | **use for the cheap pre-read** |
| `meituan/longcat-2.5:free` | 1M | **no** `response_format` | on by default | correct probe answer, 3.3 s | fallback only — cannot honour the JSON contract |
| `stepfun/step-3.7-flash:free` | 262K | yes | mandatory | **HTTP 429 "temporarily at capacity upstream"** | unreliable — do not default to it |
| `stealth/crouton-alpha` | 1M | yes | mandatory | not tested | **expires 2026-11-09** — excluded |

Beam is 501B total / 23B active; Solar is 35B / 3B active. Both are genuinely $0 (`cost_details.cost: 0`).

**Decision:** `reflection/beam-1.0-501b-a23b:free` writes the report; `upstage/solar-mini4:free` does the
cheap read (roster pre-pass, title/summary). A run costs nothing, which makes the demo's cost line honest
rather than theoretical.

## Two traps found by running it, both must be handled in code

**1. Mandatory reasoning eats `max_tokens`.** Beam always thinks before answering, and the thinking is
billed against the same completion budget. With `max_tokens: 2600` on a 26K-char document, reasoning
consumed the lot and the API returned `content: null` with `finish_reason: "stop"` — a *successful*
response carrying no answer. Budget `max_tokens` as reasoning + output (8,000 worked; 637 reasoning
tokens at `reasoning_effort: "low"`), and treat `content == null` / `refusal != "null"` as retryable
rather than as an empty result.

**2. A successful response can be another document's answer.** One extraction of the Arete page
returned a perfectly-formed Brief about the 2014 film *Whiplash* — J.K. Simmons, Damien Chazelle — and
**0/3 of its spans existed in the source**. Five identical retries were correct, and a trivial probe
(`reply with ZEBRA-47`) answered correctly, so this is a transient upstream fault, not a model that
ignores input.

That is precisely why the span gate is not optional:

- verify every extracted span is a verbatim substring of the document (whitespace-normalised, case-folded);
- on failure, retry once with the same prompt;
- if it fails again, mark the run **degraded** and say so — never emit the brief.

A report built on a fabricated brief is worse than no report, and the gate catches it 100% of the time
because fabrication has no quotes.

## Prompt note

Field meaning belongs in the **JSON schema `description`**, not only in the prompt. In the first passing
run `move` came back as the literal string `"extract"` — the model echoed the instruction verb ("extract
its key inputs") into the field. `description` on each property fixes that class of error.
