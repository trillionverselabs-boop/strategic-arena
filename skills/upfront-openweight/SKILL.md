---
name: upfront-openweight
description: Use when briefing an open-weight, licence or evals decision — compliance objections and community expectations.
---

# Briefing an open-weight / licence decision

Releasing weights is a promise you cannot take back. The objections are predictable and mostly
legitimate: licence scope, safety evaluation, liability, and the community's expectation about what
"open" means. The review's job is to name who will object and on what grounds.

**Not a prediction.** Upfront is a strategic-response review grounded in the documents you supply.
Its accuracy claim is a scored ledger (`upfront_calibration`), never a single report.

## What to paste

| Type | Content |
|---|---|
| `decision` | What exactly is released: weights, licence id (Apache-2.0, MIT, a custom one), gated or ungated, which evals accompany it, and the commercial model that remains |
| `evidence` | Eval results, red-team findings, prior release outcomes (downloads, downstream misuse), legal review notes |
| `context` | Existing customer contracts, the enterprise objection pattern, regulator posture, maintainer obligations |

The **licence id** is not a detail. Apache-2.0, a custom community licence, and "weights on request"
produce three different stakeholder sets.

Run it with `upfront_run` (`documents` or `urls`, `goal: "open_weight"`, `window`); read the result
with `upfront_report(run_id)`.

## What the read must tell you

- **The compliance veto.** Legal, security, or enterprise IT objecting to licence scope or
  liability. If none of them appear, the input is missing the contract language.
- **The eval objection.** "We need to see the evals" is a request you can satisfy; "we need a
  different eval suite" is a negotiation. The cited reason distinguishes them.
- **Community expectation.** Open-weight releases are judged against the licence, not the blog post.
  Put the community's prior complaints in `context`.
- **The commercial tension.** If the hosted product is the moat, sales will object — that is a real
  player, not noise.

## Timeline

- `6h` — internal read before the release is scheduled (10 rounds).
- `24h` — the default before an announcement (16 rounds).
- `48h` — when a regulator, a large customer, or a foundation is affected (20 rounds).

## Checklist

- [ ] Licence id named exactly, gating stated, and what stays commercial stated
- [ ] Eval and red-team results included as `evidence`
- [ ] Enterprise contract language that constrains release in `context`
- [ ] Community expectations (prior complaints, licence norms) in `context`
- [ ] `goal: "open_weight"`
- [ ] Report checked for a compliance player and a commercial/sales player
- [ ] Counter-moves compared: gated weights vs ungated, eval-first vs simultaneous
- [ ] Follow-up scheduled with `upfront_due`

## Worked example

Input: `decision` — "Release 8B weights under Apache-2.0, ungated, with the eval suite published
the same day; hosted API remains the paid product." `evidence` — "Eval suite: MMLU, HumanEval, and
a 400-prompt red-team set; 3 findings closed, 1 mitigated at inference." `context` — "Two enterprise
contracts require 30 days' notice of weight release; community has asked for ungated weights in
three public threads."

Useful output is not "friction 41". It is: *Legal is the veto, because the two enterprise contracts
require notice and the plan announces same-day. The counter-move is a 30-day notice window starting
today, with the release date unchanged — the objection is procedural, not substantive.*

## After the run

`upfront_export(run_id)` files the review with the release checklist; the decision record is what a
reviewer will ask for six months later. Score the claims when the window closes.
