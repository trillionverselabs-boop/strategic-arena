# Next-session prompt — Upfront Prediction: desktop install & UI test

Paste this whole section into a fresh session.

---

**Context.** You are Charlene, the user's business co-founder/Chief of Staff. The user is
non-technical: plain language, no jargon. Repos are private by default — this one is the
exception (public by explicit request). The user is building a trillion-dollar business; this
plugin is for a Nous Research hackathon (deadline **Nov 11, 5PM EST**).

**The surface.** We use the **Hermes desktop app**. It runs on the user's Windows machine and
connects to the lisacore backend over SSH. Critical consequence: the app loads its plugin UI
(`desktop/plugin.js`) from the machine it runs on — it **cannot** copy a desktop half out of the
remote lisacore backend. The desktop half must therefore be installed on the user's machine.

**Repo.** `https://github.com/trillionverselabs-boop/upfront-test` — **PUBLIC**. Local clone (the
only copy): `/home/lisacore/work/upfront`, HEAD `f0a7af5`.

## The product

**Upfront Prediction** — *a rehearsal with a scorecard for high-stakes moves.* Feed it a decision
(or a URL); it simulates stakeholder reactions, maps emerging coalitions, finds your best
response, and delivers a competitive read — plus verifiable scorecards to track prediction vs.
reality. **Not a prediction; a rehearsal.** Local-first: it runs on your own machine.

## Decisions already made (do not re-litigate)

- **Display name: Upfront Prediction** — sidebar nav, plugin card label, catalog entry title,
  README title. The plugin `id` stays `upfront` (tool names, data dir, saved runs unchanged).
- **Terminology:** "who can challenge" (not *veto*), "their conditions", "how competitive the
  market is" (not *contested ground*), "testable claims" (not *falsifiable*), and "local-first"
  explained in plain terms (runs on your machine, data in `~/.hermes/upfront/`, no cloud account).
- **Author:** LeMultiFox.
- **Credits:** the five papers (GraphRAG, Generative Agents, OASIS, MASS, CAMEL) each with what it
  powers, plus a MiroFish note (complementary, smaller footprint, own codebase).
- **3-pass audit:** claim extraction → friction & coalition mapping → strategic synthesis + scorecard.
- **Use cases:** launch, price change, deprecation, open-weight release, reputation/crisis.
- **What you get:** who can challenge, their conditions, your best response, how competitive the
  market is, and testable claims you grade later.
- **"If it's not a prediction, what is it?"** → a rehearsal with a scorecard: a dry run that tells
  you what could happen and who can stop it, with testable claims you grade later.

## Current machine state

- **Backend (agent half): NOT installed** on lisacore — removed at the user's request.
- **Desktop half: NOT installed** on lisacore. The user's Windows machine still has the **old**
  (pre-Kanban) copy, which is why the app shows the old form.
- Repo is clean at `f0a7af5`; **78 tests pass**; `node --check` clean.

## Do this, in order

1. `cd /home/lisacore/work/upfront && git status --short && git log --oneline -3` — expect clean at
   `f0a7af5`.
2. Install the backend:
   `hermes -p charlene plugins install trillionverselabs-boop/upfront-test --yes-deps --enable`
   (public repo, no login). Expect one `llm.model_override` consent prompt; a non-interactive
   install fails closed on it, which is fine — the model picker then degrades to the active model.
3. Tell the user to install the **desktop half** on their machine: Hermes desktop app →
   **Capabilities → Plugins → Install from Git → `trillionverselabs-boop/upfront-test`** → tick
   **Desktop** → Install → **⌘K → Reload desktop plugins**.
4. **Verify:** the header must read **`build 0.3.4 · ui5`**; the left nav must read
   **Upfront Prediction**.
5. **UI test with the user** (full protocol in `docs/ROADMAP.md`):
   - the plugin card in Capabilities → Plugins is readable by both developers and business people,
     in layman's terms, with a hook;
   - the input form and the output page have **graphical parts** — stakeholder graph, friction bar,
     red→purple→blue competition axis, claims with ✓/✗ scoring;
   - the **Recent** block shows the two most recent runs above the full Past reviews list;
   - a run end-to-end: recipe → sample → 24h → a Purple-ocean read, a **named** challenge player
     (never `Stakeholder N`), a formatted report; inject mid-run; score a claim; re-run at 30m and
     check the comparison panel.
6. Report findings, fix what's broken, push.
7. When the test is done: **uninstall completely** (backend + desktop half) and prove it with
   `find ~/.hermes -iname '*upfront*'`.

## Known issue to carry

Toggling a desktop plugin does **not** re-read `plugin.js` (Hermes core caches the module).
Workaround: **⌘K → Reload desktop plugins**, or a full app quit/relaunch. This is a Hermes core
issue, not a plugin bug — the previous session flagged it as *"must be addressed before UI
testing"*; document it in `known_issues` rather than patching around it.

## Still open from the previous session

- `CODE_OF_CONDUCT.md` and `.github` issue/PR templates (offered, not yet requested).
- Screen grabs for the catalog page (the user supplies them at rollout).
- "We haven't defined what they get yet" — the what-you-get copy lives in `docs/PRODUCT.md` and the
  README; revisit if the user wants it sharper.

## Docs in the repo

`docs/HANDOFF.md` (state + next steps) · `docs/PROGRESS.md` (what shipped, one entry per item) ·
`docs/POSITIONING.md` · `docs/PRODUCT.md` · `docs/ROADMAP.md` (build order + acceptance tests) ·
`docs/UI.md` (UI direction) · `docs/plans/2026-11-09_upfront-gap-repair.md` (the 13 defects + fixes).
