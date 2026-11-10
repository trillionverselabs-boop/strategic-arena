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

**Live run — the roundtable.** A watcher must not get bored in a 48-hour cycle,
so the run is read as a feed: a round track (with "you are here"), **both loudest
voices quoted** (for and against), the statements the parties just made in their
own words, and a board that bends when you inject a counter-move. Estimated time
remaining, not a spinner. The board names its three groups and counts them —
*will block it · undecided · behind it* — because a colour legend is not a scale.

**The ledger.** Under the call: *what each party is worth*. A waterfall from the
neutral floor (35 on this scale — the decision itself, not a person) through every
hostile party, the supporters who subtract, and the number the room actually ends on.
Then the ledger proper (share / points / veto), "the read" from the arithmetic, the
coalition by what it does, and concession cards showing the re-read room for each
satisfied party. Points are heat; the veto column is power. Never conflate them.

**Result.** The call first — a headline sentence built from the blocker and the
heat band, then *who can stop it / what they need / your best move* as three
labelled answers, then **what ends this objection** (their condition verbatim and
the artefact it points at). Then the room in order, **what each party is standing
on** (the provenance graph: cited spans → parties), the movement chart, the
transcript grouped by round, and the scorecard.

## What the product gives (the output contract)

The input is an **artefact**, not a decision form: a link or the text itself — a repo
README, a launch post, a whitepaper, a case study, a press release, a tweet. The
output is a **landscape read**, defined once and shown on the first screen:

| # | Comes back | Means |
|---|---|---|
| 1 | **The room** | who actually reacts — customers, competitors, partners, the marketplace that would list you — named, from your own text |
| 2 | **Who decides** | the parties with real power over the outcome: who can veto it, who can amplify it, who can only complain |
| 3 | **The field** | how contested the ground already is, and whether you will be read as a new category, another entrant, or noise |
| 4 | **The price** | what each concession buys, computed from the room (settle Finance and Legal and the call goes from a fight to quiet ground) |
| 5 | **The record** | claims frozen at run time with dates, scored when the window closes |

The contract is the home page's spine, not a tooltip: it renders by default and each
tile names one output. "Who can stop you" survives inside tile 2 — it is the sharpest
case of "power over the outcome", not the whole product.

## Palette

| role | hex | meaning |
|---|---|---|
| accent / "behind it" | `#4c9bf0` | the brand blue, and every primary action |
| "undecided" | `#e5b54a` | gold |
| "will block it" | `#d9538f` | rose |
| "your own document named them" | `#9b7be0` | violet |

A cool→warm ramp rather than a red/green stoplight. Hue never carries meaning alone —
the labels and the position do — so a colour-blind reader loses nothing. Fills use the
hue; text uses `textTone()` (74% hue toward white) because small rose on near-black
smudges.

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
