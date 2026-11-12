# Catalog PR #153750 — where it stands

State as of 2026-11-12, after the review fixes. Written down so the state, and the
permission boundary behind it, do not have to be rediscovered.


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

## The description: fixed 2026-11-12 23:03

The description now names pin `174fda73`, `version: "0.6.4"`, build `0.6.4 · ui45`,
and carries the model-requirements, model-controlled-inputs and post-submission
sections. Verified by reading it back: zero occurrences of `65d341c`, `0.6.3`,
`ui36` or `83563c`; three of `174fda73`.

It had been stuck because:

- Editing a PR description is a write against `NousResearch/hermes-agent`.
- Both GitHub credentials on the dev machine (gh's fine-grained PAT and the git
  credential store) can push to `trillionverselabs-boop/strategic-arena` but return
  `403 Resource not accessible by personal access token` on `updatePullRequest`
  (GraphQL and REST alike).
- A fine-grained PAT cannot write to a public repo the user is not a member of —
  that is a documented GitHub limitation, not a configuration mistake.

Resolved by re-authenticating the machine instead of handling a token: `gh auth login
--web` (device flow) gave `gh` an OAuth token with scopes `gist, read:org, repo`, which
can write to the upstream repo. That is the right first move when this comes up —
hand the user a one-time code, not a secret to store.

The equivalent command, if a token with `pull_request: write` is ever at hand:

```bash
# classic PAT with public_repo, or an OAuth token from `gh auth login --web`
GH_TOKEN=... gh pr edit 153750 --repo NousResearch/hermes-agent \
  --body-file docs/PR-BODY-FINAL.md
```

Next submission: confirm that write path **before** starting the work, not after.
