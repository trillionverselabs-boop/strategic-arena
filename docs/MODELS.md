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
- **Money is read, never guessed.** Tokens are arithmetic (rounds x parties x the bounded prompt
  window) and are always shown. A price comes from the public catalogue for that exact model, or
  it is absent — never interpolated. After a run, the host's own usage and cost estimate are
  reported instead, which is the number that actually happened.
- **The price route cannot choose a model.** It answers `price_for(model_id)` and nothing else;
  there is no list, no picker and no permission involved.

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

Free models work — everything in this plugin runs on one, and the demo's live runs are
built on the assumption that replies arrive slowly, arrive refused, or do not arrive.
What differs is throughput, not shape: the same review comes back, and one honest
recommendation follows from it.

**The run uses whatever model your Hermes default model setting is on.** There is no
model setting in this plugin. The form reads the session's model from the app's own
state and shows it read-only; every call — ingest, rounds, reflection, claims — goes
through that one model. To change it, change it in the app. The next run picks it up,
and nothing already finished is affected.

**A free model is the cheapest way to try one review.** Three rounds is a couple of
minutes and costs nothing. That is the right first run for most people: find out whether
anyone objects before paying to find out how much.

**A free tier is rate-limited, and a large input makes that bite.** A research paper or
a long technical post is a bigger ingest and a longer argument, so it needs more calls in
a row — exactly the shape a per-minute quota refuses. The run path now spaces calls once
a provider answers 429 and retries with backoff instead of firing eight at once, so a
throttled run usually finishes; it just takes several times longer, and a long timeline
can still end short.

**For a large input, use a paid model.** Not because the free one is wrong — the output
has the same shape and the same honesty about what it could not ground — but because
minutes instead of tens of minutes is worth the cents, and a run interrupted by someone
else's quota is a run you have to repeat.

**The wait is mostly ingestion, not rounds.** The timeline you pick changes how long the
room argues; it does not change how long the link takes to read. Fetching and decoding the
artifact happens once, before the first round appears, and on a research paper or a long
technical post it is the slowest single step in the product — a couple of minutes where a
round is seconds. Two consequences worth knowing: an early "nothing is happening" is
usually the ingest, and choosing a shorter timeline will not shorten it.

**If a run fails, change the model and run it again.** When the provider rate-limits you
(HTTP 429) the form says exactly that: nothing about your input is wrong. Switch the
session to another model — free or paid — and start the review again. The form keeps what
you typed, and every finished run stays in the list, so a rerun costs you the wait and
nothing else.

If a model stops working altogether, nothing here needs changing either: change the model
in the app. The plugin follows the session.

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
