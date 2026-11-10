# Demo script — 60 seconds

Recorded once testing is done. Written so the recording needs no editing beyond
trimming the ends: every step is a click that already exists, on real run data.

**Setup before you hit record**

- One finished, scored run in history (the demo card picks a scored one first).
- One link ready to paste: a repo README you actually care about — not a fixture.
- Window at ~1240px wide, dark theme, notifications off.
- Two runs of the same open in two tabs if you want the "counterfactual" beat.

---

## 0:00–0:12 — The claim

> *"Most AI tools summarise the link. This one tells you what the room will do with it."*

**On screen:** the home page. Hero headline *"Read what it means before it reads you."*
Do not scroll. The six contract tiles are visible: what it means, the room, who
decides, the field, the price, the record.

## 0:12–0:25 — One click to a finished review

> *"This is a real session, not a fixture. One click."*

**Click:** *See the finished review* on the demo card. Land on the condensed read.

> *"What it means: the claim, what it displaces, the opening it creates. Then the
> call — who can stop it, what they need, the move that gets you past them."*

## 0:25–0:42 — The price

> *"Every party priced. Not an opinion — exact Shapley over the room's own friction.
> Legal is worth 21 of the 51 points. Clearing Legal alone still leaves Finance's
> veto; clear both and the room goes to 18.9 with nobody left who can stop it."*

**Scroll slightly** to the waterfall, then the concession cards. Hover nothing;
just let the two numbers land.

> *"That's the thing a spreadsheet can't tell you: which week of work actually
> moves the call."*

## 0:42–0:52 — The record

> *"And it can be wrong in public. These claims were frozen before anyone knew the
> answer, with probabilities and dates. It was graded 'right'. Here's the track
> record: n equals five, because pretending otherwise is how these tools lose trust."*

**On screen:** the graded claim block. Say the `n` out loud — it's the credibility.

## 0:52–1:00 — The lens

> *"Same engine, different room. A README brings maintainers and security reviewers.
> A tweet brings the people who quote it. The medium decides who could possibly
> react — which is the whole reason a generic prompt can't do this."*

**Click:** *Start arena session* → the *What are you adding?* dropdown. Open it,
show the seven media, close it. **Cut.**

---

## What not to do

- **Don't open with the architecture.** No diagrams in the first 30 seconds.
- **Don't scroll the full result page.** It's a deep tool; the first screen is the
  pitch. The waterfall and the record are the only two things worth a scroll.
- **Don't say "AI agents".** Say "the room" and "the parties". The jargon makes it
  sound like a toy; the names make it sound like a meeting.
- **Don't hide the `n`.** A thin track record admitted in the demo is worth more
  than a thick one claimed.

## Capture settings

- 1440×900 or 1240×800, 60fps, no cursor trail.
- `ffmpeg -i raw.mov -vf "scale=1280:-2" -c:v libx264 -crf 20 -pix_fmt yuv420p assets/demo.mp4`
- Poster frame: the finished-review screen → `ffmpeg -i assets/demo.mp4 -ss 00:00:18 -frames:v 1 assets/how-it-works.png`
- Target: **under 8 MB**, so it loads on the plugin page and in a Discord preview.
