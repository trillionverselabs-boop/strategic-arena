# UI direction

Reference studied: [`RegeneratusLabs/lazy-plugin`](https://github.com/RegeneratusLabs/lazy-plugin) (v0.9.x, 70
commits, PR in review at the time of writing). Judged from its `desktop/plugin.js` and `assets/preview.png`,
not from its README claims.

## What that plugin gets right

1. **One primary action per screen.** A single input ("Give the cat a job"), one button ("make it"), results
   below. No control panel competing with the job.
2. **Verdicts are sentences, not colours.** A chip reads `needs a key — set PETBARN_API_KEY` or
   `blocked upstream — HTTP 403`. The colour is the second signal, never the only one. That is exactly the
   discipline our sea-state fix just adopted.
3. **Serif headings + mono numbers.** Cheap to do inside the SDK, and it makes the thing read as an
   *instrument* rather than a form.
4. **A receipt, not a badge.** Every build ends with `plan · files · check · try-out`, each row a tick or
   the exact failing line. "No green badge without the line underneath it." This is the single best idea
   in the project.
5. **Provenance on every card.** `2 tools · 6 files · v0.1.0` — the card tells you how much to trust it.

## What not to copy

- **A 396 KB `plugin.js`.** Most of that file is one base64 PNG backdrop. It loads slowly, it is unreadable
  at review time, and a catalog reviewer opens exactly this file. Ours is 35 KB; keep it that way — use
  CSS, not a bitmap.
- **Reimplementing the design system.** They ship their own `CC_STYLE` block with a class prefix, so the
  page looks like an app inside a tab. The SDK's `ui.*` components and theme variables make a plugin look
  *native* for free, and native is the thing that makes a plugin feel like part of Hermes.
- **Mono for body text.** Fine for numbers and ids; it costs readability for anyone reading a paragraph.
- **Themed voice everywhere.** The cat works because it is confined to names and headings. Inside the
  actual findings it would undercut the credibility of a strategic read.

## What Upfront's page should become

Three zones, top to bottom. The fix already landed for the sea read; this is the rest.

### 1. One question, one field

> **What are you deciding?**  `[ paste a link, or the decision ]`   `[ Read it ]`

Everything currently in the form that the document can answer moves out of the form. The user should not
be typing stakeholders a document already names.

### 2. The read — the part nobody else has

A `Brief` card showing *the move*, *who is making it*, and every claim with **its quote underneath**.
Clicking a quote highlights that sentence in the source pane. This is "no span, no fact" made visible: the
credibility of the whole product is that a reader can check every line in two seconds.

Also show the two counts that prove the read happened: `12.4K chars read · 11/11 spans verified`.

### 3. Two axes, side by side

| **Can it be stopped** | **What it changes for others** |
|---|---|
| friction gauge, veto player, coalitions, sea chip | displaced parties ranked by how hard it hits, counter-moves with timing |
| existing engine | R5–R7 (`docs/PRODUCT.md`) |

Under both, the **receipt line**:

```
read 12.4K chars · 11/11 spans verified · 8 parties · 3 rounds · $0.00 (Beam 501B, free)
```

That line is the trust product. It says what was read, what was checked, how much thinking happened, and
what it cost — and every number in it is already tracked by the backend.

## Ordering

UI work rides after R5 (the reader), because the page's centrepiece is the Brief. Doing the visual pass
first would mean designing a card for data that does not exist yet. The one cheap exception, done now:
the off-axis sea chip, since it stops a grey "insufficient" from rendering as an unlit axis.

## What we owe the repo (from the same reference)

- A screenshot at the top of the README, above the fold.
- A **"Limits, honestly"** section. We have better material than they do: an empty room reads as
  insufficient input, the field axis is not built yet, and the calibration ledger is empty until n ≥ 10.
- Tagged releases, so a SHA pin has something human-readable behind it.
