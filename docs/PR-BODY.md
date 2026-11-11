# PR body — catalogue submission (`plugin-catalog/strategic-arena.yaml`)

Paste this into the pull request against `NousResearch/hermes-agent`. Rule 13 asks
for disclosure; rule 05 asks that the submitter be the repo owner or a major
contributor — the first line is what makes that legible.

---

## What this is

**Strategic Arena** (`strategic-arena`) — read what it means before it reads you.

Give it a link — a repo README, a blog post, a whitepaper, a case study, a press
release, a tweet — and it opens a room of the people who will actually react. It
names who holds real power over the outcome (who can block it, who can amplify it,
who can only complain), prices each party's leverage against the room's own
friction with exact Shapley attribution, and shows what each concession buys. Then
it freezes testable claims with dates and scores them, so the record argues for
itself.

**Submitted by the repository owner.** I'm Lisa — `LeMultiFox` in the Nous Research
Discord, and `trillionverselabs-boop` is the org this repo lives in. TrillionVerse
Labs is the studio name the work is made under. The copyright is mine personally;
**LDMA Partners** is the entity that receives prize payments where applicable. The
README says which is which rather than making a reviewer work it out.

Repo: https://github.com/trillionverselabs-boop/strategic-arena
Pinned: `<SHA>` (full 40-char commit — see the entry)

## Why it is a plugin and not a prompt

The medium sets the room. A README is judged by maintainers deciding whether to
merge and security reviewers deciding whether the install is allowed; a tweet is
judged by the people who quote it. The extractor carries a per-medium lens, so the
room is staffed by the parties who can actually affect that artifact — that's the
part a generic "summarise this link" prompt cannot do.

The analytics are arithmetic, not vibes: `leverage.py` computes exact Shapley over
the run's own friction function (2^n subsets, ~0.5 ms for a 5-party room), so
"Legal is worth 21 of the 51 points" is reproducible, and clearing Finance plus
Legal moves the call from a fight to quiet ground with no veto left.

## Hermes surfaces used

| Surface | Use |
|---|---|
| `register_tools` (7 tools) | `arena_run`, `arena_status`, `arena_report`, `arena_history`, `arena_calibration`, `arena_due`, `arena_export` |
| `ctx.llm` | every model call; credentials stay host-owned, no key is read or stored. A run uses the **session's** model: no picker, and the manifest declares no capability |
| `ctx.register_skill` | 5 bundled skills (launch, pricing, deprecation, open-weight, the review loop) |
| `dashboard/plugin_api.py` | backend at `/api/plugins/strategic-arena/` (run, status, report, graph, claims, events, leverage, history, calibration, due, verify, compare, price, ui, health) |
| `desktop/plugin.js` | the whole UI: sidebar nav + route, SDK components and theme tokens only; the model readout is `host.state.model`, read-only |

## Rule 13 disclosure

- **No self-updating code** (rule 03). There is no update route, no download, no
  remote `plugin.js`, no save bridge. `tests/test_no_self_update.py` fails the build
  if one appears. A stale window reports its build and points at the app's own
  Install/Update.
- **No core overrides** (rule 09). `validate` reports *no core override*; the plugin
  registers through public `ctx` APIs and the desktop SDK only.
- **Desktop surface only** (rule 08). The UI imports `@hermes/plugin-sdk`, `react`
  and `react/jsx-runtime` — nothing else, asserted by a test. No DOM reaching, no
  `data-slot` queries, no injected stylesheets, no `eval`.
- **No credentials from files** (rule 11). No `.env`, no `auth.json`, no vendor CLI
  token, no keychain. Model access is `ctx.llm`.
- **No approvals bypassed** (rule 12). No auto-approval, no guard disabled. There is no
  model override to gate: a run uses the session's model, read from the app
  (`host.state.model`) and never set by the plugin.
- **Network calls, disclosed.** `ctx.llm` for the model; the public Nous catalogue
  (anonymous, no credentials, cached 6h) only to read the published price of the model
  already in use — it cannot select one, and if it is unreachable the form shows tokens
  and no money; and, only when the user supplies links, those links are fetched as text
  (http/https, size- and length-capped, hard timeout). No telemetry.
- **No Python dependencies** (rule 10). The only third-party modules the shipped code
  imports are `pydantic` and `fastapi`, both required and pinned by Hermes
  (`pydantic==2.14.1`, `fastapi>=0.104,<1`). The manifest declares none so a plugin floor
  cannot try to move a Hermes pin; `tests/test_packaging_declares_nothing.py` pins the
  imported set and checks it against Hermes's own dependency list, so the repo proves it.

## Licensing and attribution

MIT, copyright **Lisa Martin (LeMultiFox)** — studio: TrillionVerse Labs; prize
payouts where applicable: LDMA Partners.
**`CREDITS.md` cites every paper the design
draws on**, with identifiers — CAMEL, OASIS, MASS, GraphRAG, Generative Agents,
Shapley Counterfactual Credits, Market Regime Council, two forecasting/Brier papers,
the multi-party negotiation benchmark, the virtual-respondent study, and Shapley
1953.

**MiroFish is AGPL-3.0; this repository contains none of it** — no code, no assets,
no prompts. That is the only reason an MIT licence is coherent here, so it is stated
in `CREDITS.md` and asserted by a test in both directions (the statement exists, and
a scan finds no MiroFish import or file).

## Verification

```
$ hermes plugins validate . --install-deps
Validation passed.        # desktop surface ✓ · no core override ✓ · security scan clean

$ python -m pytest -q
291 passed
```

Runs entirely on the user's machine. No account, no cloud service, no telemetry.

## Screenshots

Finished review (the call, the priced ledger, the frozen claims) and the live
session (the room, the counter-move injection, the movement track) — attached below
and linked from `screenshots:` in the entry.
