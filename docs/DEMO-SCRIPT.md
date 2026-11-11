# Demo script — 90 seconds

Paper-led, because the paper lens is the one thing nobody else has: for a paper
the *document* is the giveaway, so the read carries a clock. The other lenses get
one line at the end, over the lens dropdown.

Written so the recording needs almost no editing: two clips, one deliberate hard
cut, all on real run data — no fixtures, no staged numbers.

---

## Before you hit record

1. App updated to **`0.6.3 · ui34`** — the build pill is at the top right.
2. **One finished paper session** in history, from a real arXiv link. Use the
   KV-cache paper: the clock came back *unknown*, and saying that out loud is the
   most credible thing in the whole video.
3. **One finished non-paper session** in history, for the last beat.
4. The arXiv link ready to paste: `https://arxiv.org/pdf/<id>`.
5. Window ~1240px wide, dark theme, notifications off, history collapsed.
6. For clip 2: a 30-minute / 3-round run **already at round 1**, with the
   injection box open. A 30m run finishes in a few minutes, so the injection can
   be recorded live and then cut to the finished session.

---

## Clip 1 — the read (0:00–1:02)

### 0:00–0:08 · The claim

> "Every tool tells you what a paper says. This one tells you whether to build
> the thing — and how long you have before someone else does."

**On screen:** the Strategic Arena page, idle. Do not scroll.

### 0:08–0:18 · One link, and what it will cost

> "One arXiv link. It reads the paper as a product, not as a citation."

**Click:** `+ Start arena session` → paste the arXiv link into **Links**.
Leave the lens on auto-detect — it resolves to *research paper*.
Let the **Timeline** line show *"Suggested for this input"*, and the **Model**
line read *runs on this session's model · ≈80k tokens · free*.

> "It tells you the cost before you commit. This one is free."

### 0:18–0:38 · The answer card

**Click:** the finished paper session. Do not scroll — the card is the fold.

> "Five lines, then the evidence. **What you could build** — a gate that lets
> inference platforms reuse a cached prefix across model updates. **Who pays** —
> the inference-platform lead. **Lead time** — unknown: the paper states no basis
> for a number, so we say unknown instead of inventing one."

**Pause on *lead time*.** That hesitation is the credibility.

### 0:38–0:50 · The clock's receipt

**Click:** `show the evidence`.

> "Here's why. Four things a rebuilder gets free from the PDF — the metric, the
> evaluation setup, the analysis. Five it holds back. That ratio is the moat."

### 0:50–1:02 · The room, one screen

**Click:** `the ledger` tab, then `over time`, then `what they said`.

> "Seven parties, one line each: who's against it, who's undecided, who's already
> with you — and what each one is worth, computed by removing them in turn.
> Then the movement, then the words they actually said."

---

## Hard cut — say "and mid-run". The jump is deliberate.

## Clip 2 — the bend (1:02–1:18)

**On screen:** a live run at round 1, injection box open.

> "A live session. I can change the world it's reacting to, mid-round."

**Type:** *"We publish the full evaluation harness and the withheld configs on day
one."* → **inject**.

**On screen:** the injection lands in the feed; the room moves on the next round.

> "Watch the room move — because the argument changed, not the prompt."

---

## Clip 3 — the record (1:18–1:30)

**On screen:** the finished session, at **frozen claims**.

> "And before anyone knew the answer, it froze testable claims with dates. Come
> back when the window closes and it grades itself."

**Last beat**, over the lens dropdown open, hovering the other options:

> "Same engine for a repo README, a launch post, a pricing page, a press release
> or an internal memo. Free, local, installs from the Hermes Marketplace."

---

## What not to do

- **Don't scroll past the answer card.** The card *is* the product.
- **Don't say "Shapley".** Say "by removing each party in turn" — the same claim,
  readable in one second.
- **Don't hide the unknown clock.** "The paper doesn't say, so we don't guess" is
  stronger than any number you could invent.
- **Don't open with the architecture.** No diagrams in the first 30 seconds.
- **Don't show the transcript first.** It's a tab, not the headline.
- **Don't say "AI agents".** Say "the room" and "the parties".

## Capture settings

- 1440×900 or 1240×800, 60fps, no cursor trail.
- `ffmpeg -i raw.mov -vf "scale=1280:-2" -c:v libx264 -crf 20 -pix_fmt yuv420p assets/demo.mp4`
- Poster frame: `ffmpeg -i assets/demo.mp4 -ss 00:00:24 -frames:v 1 assets/how-it-works.png`
- Target **under 8 MB** so it loads on the plugin page and in a Discord preview.
- YouTube title: `Strategic Arena — read the room before you publish (Hermes Agent plugin)`

## Caption / YouTube description

> Strategic Arena — a Hermes Agent plugin. Give it a link; it puts the people and
> organizations who will actually react into one room, prices what each of them
> can stop, and freezes testable claims with dates. Research papers also get a
> replication clock: what the publication gives away, what it holds back, and how
> long the lead lasts.
