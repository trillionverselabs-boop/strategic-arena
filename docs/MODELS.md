# Models — what this plugin assumes, and what it does not

Strategic Arena **ships no model**, **names no model**, and **asks you to choose no model**. A
review runs on whatever model the Hermes session is already using — the one answering you in the
app. That is a deliberate boundary: a plugin is in no position to have an opinion about which
model is best, and the app has already made that decision.

## How a model is reached

- **Agent tools and the report** go through `ctx.llm` — the host's own facade, with host-owned
  credentials, the per-plugin trust gate and usage accounting. The plugin never holds a token.
- **The desktop backend routes** use the same facade (`agent.plugin_llm.PluginLlm`), because the
  routes can be served by a process that never ran `register(ctx)`.
- **The form shows the session's model, read-only**, from the app's own state
  (`host.state.model`). It never sets it. A picker here would need a live catalogue fetched
  from whichever machine the window runs on *and* the host permission
  `plugins.entries.<id>.llm.allow_model_override`, which the desktop app does not grant — so it
  could only ever disagree with the run. The honest fix was to stop offering the choice.
- **The cost estimate is tokens, not money**, because tokens are arithmetic we can defend
  (rounds x parties x the bounded prompt window) and a price is not. `free` is printed only when
  the model's own slug says `:free`; every finished run records the model that actually served it.

## What the plugin does not assume about a model

These are engineering guards, not claims about any model's quality:

| Assumption the plugin refuses to make | What it does instead |
|---|---|
| That the model answers in clean JSON | Parses defensively — strips fences, takes the outermost object, validates the shape; an unusable reply is reported as such, never silently accepted |
| That a "successful" response contains an answer | Treats empty content as a retryable failure rather than an empty result |
| That reasoning tokens have been budgeted for | Gives the completion room to think *and* answer |
| That one bad answer means the input was bad | Counts per-call failures and marks the run degraded with the reason, instead of inventing stakeholders |
| That a document quote came back verbatim | Verifies every quoted span against the source and drops what it cannot find |

The last row is the one that matters: a report built on a fabricated quote is worse than no report,
so a span that is not in the document is dropped and listed, never kept.

## Free versus paid

Free models are a moving target by nature — rate-limited, sometimes slow, occasionally withdrawn.
The plugin treats that as an operational fact rather than a recommendation:

- the form reads `:free` from the session's model slug and says, before you start, that the wait is
  real;
- the form prints a realistic wall-clock estimate for the chosen timeline, and the timeline itself
  is suggested from the input rather than defaulted;
- a refused or unavailable model produces a message naming the cause, not a generic failure.

If a model stops working, nothing here needs changing: switch the model in the app. The plugin
follows the session.

## Why this file has no model table

An earlier version listed free models with measured timings and verdicts. That is the wrong shape
for a community plugin: the numbers date immediately, a reader cannot reproduce them without
credentials they do not have, and publishing them turns a maintenance note into an endorsement of
third-party models this plugin is not responsible for. To find out how a model behaves, run it —
the plugin reports real usage, per-call failures and a degraded flag when something misbehaves.

## Prompt lessons that are about this plugin's code

Two behaviours are worth recording because they are handled in `ingestion.py`, not because of any
particular model:

- **Field meaning has to be stated twice** — in the schema `description` and in prose. An
  instruction that opens with an imperative verb ("Read the document and extract…") can come back
  with the verb as the value; defining each field on its own line fixes it.
- **Quote repair, not blind retry.** A model paraphrases a word or two inside a quotation often
  enough that retrying is the wrong response. `verify()` locates each span in the document — exact
  match first, then an anchor on the opening six words — and rewrites it to the document's own
  wording. A span that cannot be found is dropped and listed.
