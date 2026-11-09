---
name: upfront-deprecation
description: Use when briefing a sunset or breaking change — affected segments, migration path, notice period.
---

# Briefing a deprecation

A sunset is only contested where the migration path is missing or the notice period is short.
The review should rank segments by *how much work you are asking of them*, not by how loud they are.

**Not a prediction.** Upfront reads the reaction of the players named in your input. It does not
forecast whether the deprecation succeeds; the scored ledger (`upfront_calibration`) is the only
accuracy claim, and only after enough runs have been checked.

## What to paste

| Type | Content |
|---|---|
| `decision` | What is going away, the date it stops working, the replacement, and the write-only/patch escape hatch if one exists |
| `evidence` | Usage by segment, the number of affected integrations, support tickets from comparable sunsets, SLAs or contractual notice terms |
| `context` | Who owns the migration on the customer side, any promise made at sale time, partner dependencies |

Quantify who is affected. "Some customers use v1" produces a fictional stakeholder; "412 accounts,
60 of them enterprise API integrations" produces the real one.

Run it with `upfront_run` (`documents` or `urls`, `goal: "deprecation"`, `window`); read the result
with `upfront_report(run_id)`.

## What the read must tell you

- **The largest migration burden.** The segment facing the most work is usually the veto, even when
  it is quiet.
- **Whether support or professional services is the blocking player.** They inherit the migration;
  if they are below −0.30, the date is not credible.
- **The contract collision.** Any SLA or notice clause shorter than your window is a legal veto,
  not a customer-relations problem.
- **The escape hatch.** "Read-only for 90 days" changes the read more than a month of extra warning.

## Timeline

- `6h` — internal read before you commit to a date (10 rounds).
- `24h` — the default for a public announcement (16 rounds).
- `48h` — contractual sunsets, partner ecosystems, or anything with a regulator in the loop.

## Checklist

- [ ] `decision` gives the exact stop date and the replacement
- [ ] Affected accounts and integrations are counted, by segment
- [ ] Notice period checked against every SLA and contract term in `context`
- [ ] Migration workload per segment stated in `evidence`
- [ ] `goal: "deprecation"`
- [ ] Report checked for support/services as a named player, not only customers
- [ ] Counter-moves compared: longer notice vs read-only bridge vs per-account extension
- [ ] Follow-up scheduled with `upfront_due`

## Worked example

Input: `decision` — "v1 API is retired 2026-06-30; v2 has a different auth model; no read-only
period." `evidence` — "412 accounts on v1, 60 enterprise integrations, 3 partner SDKs. Comparable
2024 sunset: 11% of affected accounts churned." `context` — "Enterprise contracts promise 90 days'
notice; support owns migration assists; one partner SDK is maintained by a third party."

Useful output is not "friction 58". It is: *the partner SDK is the veto — it cannot ship a v2
client before Q3, so the June date fails on someone else's roadmap. The counter-move is a read-only
bridge to Q3, which converts a contract breach into a schedule.*

## After the run

`upfront_report(run_id)` for the announcement brief, `upfront_export` to file it beside the
deprecation notice. Score the claims when the window closes.
