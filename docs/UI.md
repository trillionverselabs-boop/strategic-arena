# UI direction — what the page is for

Rewritten 2026-11-10 after the first real screen grabs came back. The old page
failed for one reason: **it showed measurements, not the thing.** Coloured dots
with numbers, a friction bar, a list of stakeholders — all correct, and none of
it told a reader what would happen to *their decision*.

## The rule the page is built on

> A number with no sentence next to it is noise.

Every metric on the page now carries a word, a scale, and where it matters the
sentence a party actually said. Concretely:

| Old | New |
|---|---|
| `friction 52` | **A fight** · 52/100 · "At least one party is working against you and has the power to make it cost…" |
| a red dot at `-0.5` | **against it** · bar from a labelled centre · power: *can stop it* |
| a coalition hull | only drawn when 2+ parties actually agree, with their names |
| "Score the claims — did the review call it?" | **The call, frozen**, with a countdown and your running record |
| a wall of report markdown | the verdict first; the audit behind one toggle |

## What each surface is for

**Home.** One identity line, one primary action, three steps, four value tiles.
No past-runs list competing with the job, so the top can breathe.

**Your reviews.** Every run is **one line**: title, a miniature of the room (a dot
per party, position = stance, size = power), the verdict band, the blocker, the
heat score, whether it is scored, and how long ago — then a chevron. Six rows by
default, `show all` for the rest, always in the lower third. The old design used
three tall cards plus a second list, which ate the screen and said less.

**Live run.** A watcher must not get bored in a 48-hour cycle, so the run is
read as a feed: a round track (with "you are here"), a loudest-objection line,
the statements the parties just made in their own words, and a board that bends
when you inject a counter-move. Estimated time remaining, not a spinner.

**Result.** The call first — a headline sentence built from the blocker and the
heat band, then *who can stop it / what they need / your best move* as three
labelled answers. Then the room in order, the movement chart (positions over
rounds), the transcript grouped by round, and the scorecard.

## Where the five papers show up

| Paper | What it buys the page |
|---|---|
| **CAMEL** | The conversation is the artifact. `Snapshot.events` → the live floor and the transcript; the run's own frozen statements, grouped by round. |
| **Generative Agents** | Parties remember and re-act, so positions move; the movement chart is the only honest way to show that. |
| **OASIS** | Time is a dimension: rounds, a round track, "≈ 63 min left", per-round replay. |
| **GraphRAG** | A camp is a community summary, not a hull — the board names members and the coalition card only appears when it is real. |
| **MASS** | Receipts: the run line (`5 parties · 15 statements · 11 claims · served by …`), the frozen log, the calibration record. |

## Voices

The engine prompt now requires first-person speech ("I", "we") and forbids
third-person reportage. This was the single biggest warmth change: `Finance
blocks … so Finance blocks pending cost controls` reads like a status line;
`I can't sign off until the free window is capped` reads like a person you can
negotiate with. Guarded by `tests/test_events.py`.

## Typography and colour

One type scale (`T` at the top of `desktop/plugin.js`), one meaning per colour
(red = will block, amber = undecided, green = behind it, accent = your side),
and **theme variables only** for anything that reskins with the app. SVG text
uses `fontFamily: 'inherit'` so graphics and prose share the app's font.

`text-(#hex)` is not a valid Tailwind arbitrary-value form — it silently
renders nothing. The old page used it for its grey text; a guard now fails if it
comes back (`test_no_hardcoded_text_colours_that_break_the_theme`).

## What not to copy

- **A bitmap backdrop.** Everything here is CSS + inline SVG. The file is ~84 KB;
  a reviewer opens it.
- **Hardcoded colours.** Every token is `var(--ui-*)`. A plugin that hardcodes
  looks broken the moment the user changes theme.
- **Numbered dots.** The first user's words: *"the circles with numbers mean
  nothing."* They are not coming back (`test_the_room_is_readable_without_a_number_you_cannot_place`).

## Still owed

- The room is ordered by stance; it is not yet split by *camp*, so a coalition
  shows up only as a card beside the board.
- The verdict headline is composed client-side from friction + blocker + sea. A
  model-written one-line verdict would be better, and the data is already there.
- The scorecard record (`runs / scored / hit rate`) is real but thin until
  n ≥ 10 scored runs — the page says so rather than pretending.
