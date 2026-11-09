---
name: upfront-launch
description: Use when briefing a product or feature launch before it ships — what to paste, what evidence to demand, which timeline.
---

# Briefing a launch

A launch review answers one question: **who can stop this, and what do they need to see first?**
Run it before the announcement, not after the pushback.

**Not a prediction.** Upfront returns a structured read of how the named players react to your
move, grounded in text you paste. Its accuracy is only ever the scored ledger
(`upfront_calibration`) — never a single run.

## What to paste

Give `upfront_run` a `documents` array, or a `urls` array when the material lives online:

| Type | Content | Why it matters |
|---|---|---|
| `decision` | The launch plan: what ships, to whom, when, and what changes for existing users | This is the thing being reacted to. Without it, the run has nothing to simulate. |
| `evidence` | Real numbers, quotes, security-review outcomes, pilot results | Every grounded stance cites one of these. No evidence → low confidence, wide ±. |
| `context` | The org chart of the decision, prior failed launches, contractual constraints | Prevents the model from inventing a buyer who does not exist. |

Do **not** paste a marketing brief and call it a decision. The run reads what you give it; a
flattering document produces a flattering, useless review.

## Evidence to demand before you trust the run

- **Who signs off?** If no named person appears in the stakeholders, the input is too thin.
- **What is the blocking threshold?** The veto player is the player below −0.30. If the report says
  "none identified", the launch is uncontested or the input hid the opposition — check which.
- **Which segment carries the risk?** Enterprise IT, procurement, and legal object for reasons that
  sound alike and are not. Read the cited reason, not the label.
- **What did last time look like?** One line of history in `context` changes the read more than
  three paragraphs of positioning.

## Timeline

- `30m` — sanity check. Does anyone care? Use it to kill a dead idea cheaply (3 rounds).
- `6h` — the default. Positions form, the first coalition appears (10 rounds).
- `24h` — the real read before an irreversible announcement (16 rounds).
- `48h` — only when the launch is expensive or the audience is regulated (20 rounds).

Spend rounds on decisions you cannot take back, not on ones you can.

## Checklist

- [ ] `decision` document names what ships, to whom, when, and the migration for existing users
- [ ] At least one `evidence` document with a real number or an external commitment
- [ ] `context` names the approver and any prior launch that failed
- [ ] `goal: "adoption"` (open-weight, deprecation and campaign launches use their own pack)
- [ ] Timeline chosen before the run, not after seeing the result
- [ ] Report read against the claim list — every claim is something you can check in the window
- [ ] Veto player's cited reason maps to a document paragraph you supplied
- [ ] Follow-up scheduled with `upfront_due` at the window close

## Worked example

Input: `decision` — "We ship the hosted inference beta to all enterprise accounts on Monday;
existing self-hosted customers keep their plan until renewal." `evidence` — "Q2 survey of 400 CIOs:
61% cannot route inference through an external API for compliance." `context` — "Security review
owns the sign-off; last year's SSO launch slipped six weeks on IT review."

A useful read is not "friction 47". It is: *Enterprise IT is the veto player; its objection is the
routing constraint, so the counter-move is a self-hosted beta track — not a discount.* Then you run
the same decision at `6h` with that counter-move injected and compare.

## After the run

`upfront_report(run_id)` for the markdown, `upfront_export` to keep it next to the launch ticket.
Score the claims when the window closes — an unscored launch review teaches you nothing.
