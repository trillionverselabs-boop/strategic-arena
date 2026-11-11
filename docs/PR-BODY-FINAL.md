## What does this PR do?

**What it solves.** People commit engineering time and money to a decision — a launch, a price change, a repo release, an arXiv paper — and find out who objects, or that the landscape is different, only after it is public. Generic AI summarizers tell you what the artifact says, not who it will land on, and building a simulation of that reception for one decision is not something an individual can do.

**Why this approach.** Strategic Arena runs the room: it ingests the artifact, staffs it with the parties who would actually react, simulates the debate over rounds, and prices each objection with exact Shapley attribution over the room's own friction — then freezes testable claims with dates so the read is scored later instead of argued about. It is a scored read of the room, explicitly not a prediction, and it runs entirely on the user's own machine and model.

**Why a Hermes plugin.** The decision happens inside Hermes, where the link, the repo and the model already are. A prompt answers in one turn; this runs a hundred-plus model calls over minutes in the background, borrows whatever model the session is already on through Hermes' own credentials — no picker, no stored key — writes each run and its frozen claims to disk, and renders the live room in the sidebar. A prompt cannot do any of that.

## Related Issue

N/A — catalog entries arrive as PRs (rule 01), not through the issue tracker. Submitted by the repository owner (`trillionverselabs-boop`), per rule 05.

Fixes # (no issue)

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality) — a new plugin listed in the catalog
- [ ] 🔒 Security fix
- [ ] 📝 Documentation update
- [ ] ✅ Tests
- [ ] ♻️ Refactor
- [ ] 🎯 New skill

No box fits a catalog entry exactly — this PR adds no Hermes code, only `plugin-catalog/strategic-arena.yaml` — so "New feature" is ticked as the closest and said out loud rather than left ambiguous.

## Changes Made

- `plugin-catalog/strategic-arena.yaml` — new entry (36 lines):
  - `name: strategic-arena`, `repo:` the public upstream, `sha:` the full 40-char pin `65d341c…`
  - `tier: community`, `category: tools`, `version: "0.6.3"`, `requires_hermes: ">=0.23.0"`
  - `capabilities.provides_tools`: the seven `arena_*` tools the plugin registers at that commit
  - `capabilities.provides_hooks` / `provides_middleware` / `requires_env`: empty — the plugin declares no hooks, middleware or env vars
  - `image:` and one `screenshots:` URL, both pinned to the same sha
  - `known_issues`: four informational strings (session model, free-model rate limits, desktop half loading from the app's machine, unreadable PDFs reported as SKIPPED)

No other file is touched: no core modules, no tests, no docs, no dependency changes.

## How to Test

1. Validate the tree at the pinned commit (this is exactly what catalog CI does):

   ```
   git clone https://github.com/trillionverselabs-boop/strategic-arena /tmp/strategic-arena
   cd /tmp/strategic-arena && git checkout 65d341c624f992c8e5636a9ba156dc8bd39f91d5
   hermes plugins validate . --install-deps
   ```

   → `Validation passed.` (desktop surface OK · no core override · security scan clean)

2. Install and confirm it surfaces:

   ```
   hermes plugins install /tmp/strategic-arena --enable
   ```

   → Capabilities → Plugins lists Strategic Arena, enabled; the left sidebar gains a Strategic Arena page; the header badge reads `build 0.6.3 · ui36`.

3. Run a review end to end: on that page press **+ Start arena session**, paste any public repo README or an arXiv link, choose the 30-minute / 3-round timeline, and run.

   → 2–10 minutes later: the six outputs (What it means · The room · Who decides · The field · The price · The record) and 2–4 frozen claims with dates.
   → `arena_calibration()` then returns the ledger entry for that run.

Optional cleanup check: `hermes plugins remove strategic-arena && python3 scripts/uninstall-clean.py strategic-arena` removes the 18 paths a plain remove leaves behind.

## Checklist

### Code

- [x] I've read the [Contributing Guide](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md)
- [x] My commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat(catalog): add strategic-arena`)
- [x] I searched for [existing PRs](https://github.com/NousResearch/hermes-agent/pulls) to make sure this isn't a duplicate
- [x] My PR contains **only** changes related to this fix/feature (no unrelated commits) — one file, `plugin-catalog/strategic-arena.yaml`
- [ ] I've run `just test` on the tests for the code I changed, and they pass — **N/A**: this PR changes no Hermes code, so there is no repo test to run. The plugin's own suite (301 tests) is green at the pinned sha.
- [ ] `just check` passes (the blocking lint and code-health checks CI runs) — **N/A**, same reason. Catalog CI (`hermes plugins validate`) is what gates this change, and it passes.
- [ ] I've added tests for my changes (required for bug fixes, strongly encouraged for features) — **N/A**: the entry is validated by catalog CI; the plugin carries its own suite in its repository.
- [x] I've tested on my platform: Ubuntu 26.04.1 LTS (Linux), Hermes Agent v0.23.0

### Documentation & Housekeeping

- [x] I've updated relevant documentation — N/A here: the plugin's README at the pinned sha renders on `/docs/plugins/strategic-arena`, and `image:`/`screenshots:` are pinned to that same sha
- [x] I've updated `cli-config.yaml.example` if I added/changed config keys — N/A, no config keys added
- [x] I've updated `CONTRIBUTING.md` or `AGENTS.md` if I changed architecture or workflows — N/A, no architecture or workflow change
- [x] I've considered cross-platform impact (Windows, macOS) — N/A for `hermes-agent`; the plugin is pure Python plus one desktop ESM file, tested on Linux, and its desktop half loads from whichever machine runs the app
- [x] I've updated tool descriptions/schemas if I changed tool behavior — N/A, no core tool behavior changes

## Screenshots / Logs

<img width="1200" height="600" alt="how-it-works" src="https://github.com/user-attachments/assets/6acf6147-2ac6-43c2-a41d-6d0ee08c7302" />
<img width="1200" height="600" alt="marketplace" src="https://github.com/user-attachments/assets/58a1ea97-168a-45c5-b783-a15bb5985bcc" />

Validation at the pinned sha (`65d341c`):

```text
$ hermes plugins validate . --install-deps

✓ manifest — plugin.yaml parses
✓ manifest fields — name, version, description present
✓ requires_hermes — spec '>=0.23.0' parses
✓ config schema — not declared
✓ requires_env — all entries UPPER_SNAKE
✓ loadable — entry: __init__.py, desktop/plugin.js
✓ python dependencies — none declared
✓ capability probe — register() ran in isolation
✓ declared tools — matches registrations
✓ declared hooks — matches registrations
✓ declared middleware — matches registrations
✓ built-in tool collisions — no collisions
✓ security scan — safe
✓ no core override — no runtime rebinds of Hermes core
✓ desktop surface — stays inside the plugin SDK surface

Validation passed.
```

We ran entirely on the user's machine: no account, no cloud service, no telemetry.
