# Catalog PR #153750 — where it stands

State as of 2026-11-12, after the review fixes. Written down because the PR
description could not be updated (see "Known wart" below) and the reasoning
should not have to be rediscovered.

## The PR

- **PR:** NousResearch/hermes-agent#153750 — adds `plugin-catalog/strategic-arena.yaml`
- **Head branch:** `trillionverselabs-boop/hermes-agent` → `catalog/strategic-arena`, head `61d3c7f`
- **Pin:** `sha: 174fda73f7abe986d5c020ca41bfa07cd97361b5`, `version: "0.6.4"`
- **Build at the pin:** `0.6.4 · ui45`
- **Review state:** `CHANGES_REQUESTED` (expected until `teknium1` re-reviews), `MERGEABLE`
- **CI:** no checks are registered on this PR — the validate job is not wired to run
  here, so the gate is the local `hermes plugins validate` at the pin.

## What was verified

| Check | Result |
|---|---|
| `hermes plugins validate . --install-deps` on a clean clone at the pin | `Validation passed.`, `security scan — safe` |
| Plugin suite at the pin | `339 passed, 1 skipped` (the skip is the `hermes_constants` test — that module only exists inside a Hermes host) |
| `image:` / `screenshots:` / README at the pin | three `HTTP/2 200` |
| Delta comment on the PR | posted 2026-11-12 22:38, verbatim |

## Known wart: the PR description is stale

The description still reads `version: "0.6.3"`, pin `65d341c…`, badge `0.6.3 · ui36`.
The corrected text exists at `docs/PR-BODY-FINAL.md` in this repo and was never
applied, because:

- Editing a PR description is a write against `NousResearch/hermes-agent`.
- Both GitHub credentials on the dev machine (gh's fine-grained PAT and the git
  credential store) can push to `trillionverselabs-boop/strategic-arena` but return
  `403 Resource not accessible by personal access token` on `updatePullRequest`
  (GraphQL and REST alike).
- A fine-grained PAT cannot write to a public repo the user is not a member of —
  that is a documented GitHub limitation, not a configuration mistake.

The delta comment is the authoritative record, and the pinned README (which is what
the catalog page renders) is current. To close the wart, either the PR author edits
the description in the browser (copy from `docs/PR-BODY-FINAL.md`), or a token with
`pull_request: write` on the upstream repo is used:

```bash
# classic PAT with public_repo, or an OAuth token from `gh auth login --web`
GH_TOKEN=... gh pr edit 153750 --repo NousResearch/hermes-agent \
  --body-file docs/PR-BODY-FINAL.md
```

Next submission: confirm that write path **before** starting the work, not after.
