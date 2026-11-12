# Working with the Nous Research Hermes marketplace

Everything learned getting this plugin listed, written down so the next one costs
an afternoon instead of a week. The authority is the catalog's own rules — this is
the operational layer on top of them.

Links: [catalog submission](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission) ·
[plugin guide](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins) ·
[desktop plugin SDK](https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk)

## What the listing actually is

A one-line entry file, `plugin-catalog/<name>.yaml`, in `NousResearch/hermes-agent`,
merged by a human. The `sha:` is the trust model: **installs clone the repo and check
out exactly that commit.** So the listing is a pin, not a branch — pushing to your own
repo changes nothing about what users install until a new PR moves the pin.

Five rules decide whether an entry survives contact with review:

| Rule | What it means for us |
|---|---|
| **03** no self-updating code | the plugin must never fetch/replace its own files; the pin is the only update path |
| **06** declared capabilities match reality | `capabilities:` / `provides_tools` must equal what `register()` registers — undeclared creep is a security finding |
| **08** desktop stays inside the SDK | no prototype patching, no `eval`, no reaching into app markup; SDK imports only |
| **09** no runtime overrides of core | no rebinding core functions, no `sys.modules` tricks, no writes into core tables |
| **13** risky behaviour is disclosed | network calls, reads outside the data dir, shell, background processes, credential handling — **in the PR description and the README** |

## The loop

1. **Freeze the tree.** Nothing changes after the pin unless you re-pin.
2. **Validate exactly what CI validates**, on a clean clone at that commit:
   `hermes plugins validate . --install-deps` → `Validation passed.`, `security scan — safe`.
3. **Build the entry** from `docs/catalog-entry.draft.yaml`: full 40-char `sha:`,
   quoted `version:`, `image:`/`screenshots:` pointing at the same sha, `known_issues`
   limited to things a user needs *before* installing.
4. **Push the branch in the fork**, open the PR against `NousResearch/hermes-agent`.
5. **Review** returns either a merge, or a list of findings and "push the fix, re-pin,
   and comment when it's in; we'll review the delta from `<old sha>`".
6. **Fix → validate → push → re-pin → comment.** The comment is the deliverable: what
   changed, why, the test count, and any limit you chose not to close.

## The permission trap (this cost an hour once)

The PR lives in **their** repo. Writing to it — a comment, or the description — needs
write access *there*, not on your plugin repo and not on your fork.

- A **fine-grained PAT cannot do it.** GitHub: *"Using fine-grained personal access
  token to contribute to public repos where the user is not a member"* is an
  unsupported case. It 403s on `addComment` and `updatePullRequest`, REST and GraphQL
  alike, no matter which repository access you pick.
- A **classic PAT with `public_repo`** works.
- The **device flow works and needs no secret handling**: `gh auth login --web` prints
  an 8-character code and `https://github.com/login/device`; the user types the code,
  clicks Authorize, and `gh` holds an OAuth token with `repo` scope.

**Check this before the work starts.** Discovering it at the end leaves a stale
description and drags the user into a process they never wanted.

## Re-pin mechanics

Four fields move together, in one commit, on the PR branch:

```yaml
sha: <full 40-char sha>
version: "<matches plugin.yaml>"
image: https://raw.githubusercontent.com/<owner>/<repo>/<sha>/assets/marketplace.png
screenshots:
  - https://raw.githubusercontent.com/<owner>/<repo>/<sha>/assets/how-it-works.png
```

`known_issues` is reworded in the same PR when user-facing facts change. Verify the
URLs serve (`curl -sI … | head -1` → `HTTP/2 200`) before commenting: a dead image is
the first thing a reviewer sees.

## What reviewers actually look at

1. **The three model-controlled inputs.** A **URL** the model supplies that gets
   fetched (SSRF: resolve the host, refuse anything not global, on the request *and*
   every redirect). A **path** the model supplies that gets written (resolve it,
   refuse outside `data_root()`). An **id** joined into a path (validate against the
   minted format before the join). Each needs a test that fails without the guard.
2. **Disclosure completeness** — rule 13, in the PR *and* the README.
3. **The desktop file** — SDK-only, no core reach-through.
4. **The delta**: read the diff between the old pin and the new one, not the prose.

## Our failure catalogue

| Symptom | Cause | The rule |
|---|---|---|
| PR description can't be edited | fine-grained PAT, upstream repo | device flow before you start |
| `test.sh` "No module named pytest" then a commit goes out untested | the runner honours `PYTHON=`, and a `&&` chain hides the failure | check the interpreter exists; never chain a test into a commit |
| dialog title vanished for two builds | title lived inside the scroll container; then `sticky` didn't survive the app's dialog wrapper; then a documented SDK component got blamed | dashboard has a resolved height, header and footer **outside** the scroller |
| results/rounds unreachable | page `h-full` resolved to `auto` under a route host | `h-full min-h-0 flex-1 overflow-y-auto` on the page root |
| a $0.017 run warned about free tiers | caveat derived from a boolean computed from fetched data | model the state (loading/free/paid/unknown); never claim what you can't prove |
| a tier labelled "Recommended" the router never suggests | a label and a rule drifted | grep the claim strings against the logic that decides |
| an invented "$0.02 per run" in `known_issues` | a number nobody could publish | the product prints only catalogue prices; the entry does too |
| removed `DialogHeader` on an inference | a correlation, not a proof | documented SDK components stay; change *how* you use them |

## Where the pieces live

| Piece | Path |
|---|---|
| Plugin scaffold for the next one | `~/work/example-plugin/` (validates clean; `CHECKLIST.md` inside) |
| Submission skill | `hermes-plugin-catalog-submission` (procedure, gates, pitfalls) |
| Entry draft | `docs/catalog-entry.draft.yaml` |
| PR body to copy | `docs/PR-BODY-FINAL.md` |
| This PR's state | `docs/CATALOG-PR-153750.md` |
| Disclosure to fill | `docs/DISCLOSURE.md` (in the template) |
| Model-input inventory | `docs/MODEL-CONTROLLED-INPUTS.md` |
