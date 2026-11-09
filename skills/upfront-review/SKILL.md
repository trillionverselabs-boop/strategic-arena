---
name: upfront-review
description: Use when an Upfront review's window closes — rescore the frozen claims and keep the track record honest.
---

# Closing the loop on an Upfront review

Upfront produces a **strategic-response review**, not a forecast. Its only accuracy claim is the
scored ledger: runs that were checked against what actually happened. A run nobody scores is a
wasted claim, so the system owns the follow-up — you schedule it, the user answers it.

**Boundary, stated once:** the report is a structured read of how players will respond to a move.
It is not a prediction of the outcome, and a single scored run proves nothing. Only
`upfront_calibration` with `n >= 10` is evidence.

## When a review is filed

1. Note the window the user chose (`30m` / `1h` / `4h` / `6h` / `12h` / `24h` / `48h`) — it sets
   when the claims become checkable, not how long the analysis is valid.
2. Create a **one-shot cron job at the window close** (use the cronjob tool; do not build a timer).
   Its prompt should be exactly this job:

   > Call `upfront_due`. For each due run, ask me to score its claims ✓/✗ and give a verdict
   > (right / partial / wrong), plus the friction I actually saw. Then call `upfront_calibration`.

3. Tell the user in one line that the follow-up is scheduled and what it will ask for.

Never schedule a recurring poll — one job per review, fired once at `due_at`.

## When the job fires (or the user says "score it")

1. `upfront_due` → rows with `{run_id, title, due_at, window, claims[]}`.
2. If a row's window is long (`24h`/`48h`) and the user has no evidence yet, ask again tomorrow
   instead of scoring on vibes. Scoring a guess corrupts the ledger.
3. For each claim, get a real ✓ or ✗ — point to what happened. No "probably".
4. Write it back: score in the desktop (Score a claim → set verdict), or call the backend route
   `POST /api/plugins/upfront/verify/{run_id}` with
   `{verdict, note, hits: {claim_id: bool}, actual_friction}`. In code, `reporting.mark_verified`
   does the same thing. Never hand-edit `meta.json`.
5. `upfront_calibration` → report runs, verified count, claim hit rate, mean friction error.
   Say the `n` out loud; under 10 it is an anecdote.

## Verdict definitions

| Verdict | Means |
|---|---|
| `right` | The named veto player was the binding constraint and friction landed in the band |
| `partial` | The shape was right, the ranking or magnitude was off |
| `wrong` | A different player blocked it, or friction was outside the band |

`partial` is the common honest answer. Do not stretch a `partial` into a `right`.

## Checklist

- [ ] Window noted at filing time
- [ ] One-shot cron at `due_at`, prompt calls `upfront_due`
- [ ] Every claim scored ✓ or ✗ with evidence, not impression
- [ ] `actual_friction` recorded when the user has a real number
- [ ] `upfront_calibration` reported with `n`
- [ ] Ledger never edited by hand — only through verify
