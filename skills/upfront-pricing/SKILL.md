---
name: upfront-pricing
description: Use when briefing a price change — grandfathering, churn risk, and how competitors frame it.
---

# Briefing a price change

Pricing decisions fail on the edges, not the average: the account that just renewed, the team
whose usage jumped, the competitor who announces "we're cheaper" the same week. The review should
surface those edges by name.

**Not a prediction.** Upfront is a strategic-response review grounded in the text you paste. Its
track record is the scored ledger (`upfront_calibration`), and it needs `n >= 10` before it means
anything.

## What to paste

| Type | Content |
|---|---|
| `decision` | The exact change: old price → new price, what is included, the effective date, and the grandfathering rule (or its absence). Vagueness here is the most common cause of a useless review. |
| `evidence` | Churn from the last change, the size of the affected book, competitive price points, the renewal calendar |
| `context` | Contract terms (annual vs monthly, caps, indexation), who negotiates enterprise deals, any public pricing promise |

Paste the **grandfathering rule** verbatim. "Existing customers keep their plan until renewal" and
"existing customers keep their price forever" produce different stakeholders and a different veto
player.

Run it with `upfront_run` (`documents` or `urls`, `goal`, `window`); read the result with
`upfront_report(run_id)`.

## What the read must tell you

- **Who bears the increase**, in segments. A 12% increase on a $20 seat and a $200k annual contract
  provoke different players.
- **The churn-risk player.** If sales or the account team is below −0.30, the veto is commercial,
  not customer-side. That is a signal about the promise you already made.
- **Competitor framing.** Put the competitor's price and its marketing claim in `evidence`; without
  it the run cannot see the "they got expensive" narrative forming.
- **The grandfathering trade.** Grandfathering lowers churn and creates a two-tier book that sales
  will complain about later. Both players should appear.

## Timeline

- `6h` — enough for the account-team reaction and the first customer coalition (10 rounds).
- `24h` — the default for a change that takes effect within a quarter (16 rounds).
- `48h` — regulated pricing, public-sector contracts, or a change that reverses an earlier promise.

## Checklist

- [ ] Old price, new price, effective date and inclusions are in `decision`
- [ ] The grandfathering rule is quoted, not summarised
- [ ] Churn or renewal data from the previous change is in `evidence`
- [ ] At least one competitor price point is in `evidence`
- [ ] `goal: "campaign"` when the change is also a repositioning, else `adoption`
- [ ] Report's veto player checked against the segment that actually carries the increase
- [ ] Counter-moves compared: phased rollout vs grandfathering vs grandfathered-with-cap
- [ ] Follow-up scheduled with `upfront_due`

## Worked example

Input: `decision` — "Seat price $20 → $24 from March 1; existing annual contracts grandfather at
$20 until renewal." `evidence` — "Last increase (2025): 4.1% logo churn in SMB, 0.3% in enterprise.
Competitor X advertises $19/seat, annual only." `context` — "Sales compensates on ARR; three
enterprise renewals in March."

Useful output is not the friction number. It is: *Sales is the veto player, because three March
renewals collide with the increase and the grandfathering rule gives them a discount to give away.
The counter-move is to move the effective date past the renewals — not to soften the price.*

## After the run

`upfront_export(run_id)` puts the review in `decisions/` next to the pricing memo, so it can be
linked from the change ticket. Score the claims at the window close.
