# The demo video

A 90-second (we ship 88) explainer that shows Strategic Arena doing the thing it is
for: point it at one artifact, watch it fill an arena with the people who would react,
price every one of them, and write down what it expects — before you commit anything.

This page is the production record: the script, the timing, the method, and how to
re-render it. It exists so a re-record after a terminology or UI change is an edit to
one HTML file and one sentence list, not a re-discovery of the whole pipeline.

---

## Where it lives

| | |
|---|---|
| **Published** | <https://youtu.be/qrlA_0MJgB4> |
| **Local master** | `/home/lisacore/work/arena-demo-video/arena-demo/strategic-arena-demo-v5-loud.mp4` |
| **Un-normalised** | same directory, `strategic-arena-demo-v5.mp4` |
| **Earlier cuts** | `strategic-arena-demo-v2-loud.mp4` (paper-led, 88.0s), `strategic-arena-demo-v3-loud.mp4`, `strategic-arena-demo-v4-loud.mp4` |
| **Production project** | `/home/lisacore/work/arena-demo-video/` |

The video is not committed into this repository. The catalog pins an exact SHA and a
large binary in the tree would move it; the file is published on YouTube and the
production project is kept separately. `assets/how-it-works.png` remains the
in-repository visual.

---

## What it says, and when

Eight beats, 88 seconds. Every line below is one narration clip, so the timing table
is also the edit list.

| # | Scene | Seconds | Beat |
|---|---|---|---|
| 1 | `scene1-hook` | 0 – 11.0 | The hook: you built something, and you find out who hates it only when it is public |
| 2 | `scene2-artifact` | 11.0 – 22.1 | What you give it: a link or the document, any kind |
| 3 | `scene3-room` | 22.1 – 32.4 | It fills an arena with the people who will actually react |
| 4 | `scene4-read` | 32.4 – 50.7 | A real run, on a paper — and what it refused to invent |
| 5 | `scene9-pivot` | 50.7 – 59.2 | **That was a research paper. Now imagine what else you'd point it at.** |
| 6 | `scene5-price` | 59.2 – 67.9 | The price: everyone valued by removing them in turn |
| 7 | `scene6-bend` | 67.9 – 73.5 | Mid-run injection: change one thing, the arena moves |
| 8 | `scene7-record` | 73.5 – 83.6 | Ten things it expects, with dates — and it checks itself |
| 9 | `scene8-range` | 83.6 – 88.0 | Anything. Free, local, no account |

### Full script (v5, as published)

```
You built something. Or someone else just shipped something in your space.
What happens next? Who pushes back? Who can actually stop it?
And what would each of them need to come round?

Strategic Arena answers that. A plugin for Hermes.

Give it a link, or the document itself. It works on anything —
a repo, a paper, a blog post, a launch post.
It fills an arena with the people who will actually react.
Who's for it. Who can stop it. What each one wants.
Then it runs them against each other, round after round.

Here's a real run, on a paper about reusing old caches when a model updates.
The arena came back almost empty. Ten out of a hundred. Nobody can stop it.
How long before someone copies it? It doesn't know. The paper doesn't say —
so it says so, instead of inventing a number.

That was a research paper. Now imagine what else you'd point it at —
anything you're about to commit engineering time or capital to.

Then the price. And the answer is backwards: there's nobody to pay off.
The people doing the most to calm things down are the authors themselves.
Mid-run, we changed one thing. The arena moved. That's the part you can't
do with a prompt.
And before anyone knew how it would turn out, it wrote down ten things it
expects to happen, with dates. When the window closes, it checks itself —
and shows you how it did.
Free. Runs on your machine. No account. Point it at yours.
```

---

## The rules this script follows

These were set by feedback during production and are worth keeping.

**Plain language, always.** No "the read", "friction", "veto player", "staffs the
room", "replication clock", "blocker", "landscape", "perceive". If a term needs a
glossary, it does not go in the video. The on-screen labels carry the same rule:
`how much fight`, `the one standing in the way`, `written down`, `checks itself`,
`NOT CHECKED YET`.

**Plugin-first, not a commercial.** The hook is the viewer's problem and the plugin's
answer. The product is never sold; it is shown.

**No distribution claims.** The video does not mention the Hermes Marketplace and does
not reference the repository. Acceptance is not something the video can assert.

**No invented numbers.** Every figure shown is from a real run (see below). Anything
the plugin does not know is said to be unknown, on screen and in the voice.

**No fixed check-in window.** The window is the user's choice, so the video says
"when the window closes" rather than naming a duration.

---

## The real run behind it

The paper example is a genuine completed run, not a mock.

| | |
|---|---|
| Run | `a3012627c1d7` |
| Artifact | arXiv **2611.14051** — reusing KV caches across model updates |
| Finding | 2.10–5.08× time-to-first-token speedup |
| How much fight | **10 / 100** |
| Arena | **7 people** |
| Shapley ledger | **35.0 floor → 10.2** |
| Authors' own company | ≈ **one fifth (20%)** of the heat |
| Things written down | **10**, with dates |
| Replication clock | **unknown** — the paper does not say |

The "it doesn't know" beat is the point of that run: asked how long before someone
copies it, the plugin said the paper does not say, rather than inventing a number.

The mid-run injection beat (`scene6-bend`) is illustrated, not a recorded run — both
live attempts during production returned `degraded` because free-model rate limits
stopped the run. It is labelled on screen as "ILLUSTRATIVE" where it is a
reconstruction.

---

## How it was made

**Engine.** [HyperFrames](https://hyperframes.studio) — HTML is the source of truth.
Each scene is a sub-composition (an HTML file with a GSAP timeline, registered on
`window.__timelines` and started paused); a root `index.html` mounts them on a track
timeline with `data-start` / `data-duration` and a caption track. Render captures
frame-by-frame and encodes with FFmpeg.

**Visual identity.** Deep navy `#0a0e17`, panel `#0d1322`, blueprint grid, azure
`#4c9bf0` accent, magenta→amber→blue spectrum for the competition axis. Space Grotesk
for display, IBM Plex Mono for labels and numbers. Taken from `assets/` so the video
and the product share one look.

**Voice.** Kokoro TTS, `am_michael` at 1.08×, one clip per sentence. Sentence-level
synthesis — not one long take — because the caption timings then come from the actual
audio and survive any reword. Clips sit in `parts9/` (the main script) and `partsX/`
(the pivot line), each followed by a 0.20s silence, concatenated into
`narration_linesF.wav`.

**Music.** A synthesized 120 BPM bed (`make_music2.py` → `musicbed2.wav`), ducked to
0.32 in the mix, so there is no licensing question and the length is exact.

**Captions.** Hard-timed from the audio offsets (`offsetsF.tsv`). Each caption group
sets its own kill at `group.end` — without that, groups leak into later ones.

**Loudness.** Normalised to YouTube's target with
`loudnorm=I=-14:TP=-1:LRA=11`, then `-c:v copy -c:a aac -b:a 192k -movflags +faststart`.
Result: −14.3 LUFS, peak −0.8 dBFS.

**Scene pacing.** Each scene's timeline is built at its natural speed and then
stretched to the narration with `tl.timeScale(Math.min(2.6, clipSeconds / tl.duration()))`.
That keeps the choreography authored once and re-timed per re-record.

### File layout

```
/home/lisacore/work/arena-demo-video/
├── arena-demo/                     the HyperFrames project
│   ├── index.html                  root composition: tracks, wipes, captions, audio
│   ├── compositions/
│   │   ├── scene1-hook.html
│   │   ├── scene2-artifact.html
│   │   ├── scene3-room.html
│   │   ├── scene4-read.html
│   │   ├── scene9-pivot.html       the "imagine what else" beat
│   │   ├── scene5-price.html
│   │   ├── scene6-bend.html
│   │   ├── scene7-record.html
│   │   └── scene8-range.html
│   ├── narration_linesF.wav         final narration
│   ├── musicbed2.wav                final music bed
│   └── strategic-arena-demo-v5-loud.mp4
├── parts9/  s00.wav … s24.wav       narration clips, main script
├── partsX/  s00.wav … s02.wav       narration clips, the pivot line
├── offsets9.tsv  offsetsX.tsv  offsetsF.tsv
├── concat9.txt  concatF.txt
├── tts_parts*.sh                    one-script-per-rewrite TTS drivers
├── make_music.py  make_music2.py
└── narration.txt                    the script as a single file
```

### Re-render

```bash
export PATH="/home/lisacore/.hermes/tools/node-26.12.1-linux-x64/bin:$PATH"
cd /home/lisacore/work/arena-demo-video/arena-demo

# 1. re-synthesise any changed sentence into its parts/ folder, then rebuild the concat
# 2. copy the audio in
cp ../narration_linesF.wav ../musicbed2.wav .

# 3. check and render
npx --yes hyperframes@0.9.34 lint
npx --yes hyperframes@0.9.34 render --quality high --output strategic-arena-demo-v5.mp4

# 4. normalise for YouTube
ffmpeg -y -i strategic-arena-demo-v5.mp4 -af loudnorm=I=-14:TP=-1:LRA=11 \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart strategic-arena-demo-v5-loud.mp4
```

Lint currently reports one warning, not an error: `#captions-comp` is a timeline
element containing a nested `div`. It renders correctly; moving it into a
sub-composition is the clean fix if the file is ever restructured.

---

## Pitfalls hit during production

- **CSS `opacity: 0` plus `gsap.from({opacity: 0})` renders nothing.** An element
  already at 0 animates 0 → 0. Leave the CSS at its visible state and let the tween
  do the work.
- **`repeat: -1` anywhere breaks the capture engine.** Use a finite repeat.
- **Build timelines synchronously.** The capture engine reads `window.__timelines`
  right after load; no `async`, `setTimeout` or Promise around construction.
- **`hyperframes transcribe` needs a build toolchain** (whisper.cpp). Sentence-level
  TTS avoids it entirely and gives better boundaries.
- **Two renders racing on the same filename** produce a file from whichever finished
  last. Always `rm` the target before rendering, and check the md5 afterwards.
- **Copying audio with the wrong relative path** renders a silent video that lint
  catches as `audio_src_not_found`. It is a hard error, not a warning.
- **Kokoro is not installed by default.** `pip install kokoro-onnx soundfile` into a
  venv and point `HYPERFRAMES_PYTHON` at it.
- **Leave no `preview` server running.** Each idle Chrome worker pegs a CPU core on a
  GPU-less host.

---

## Submission

- Catalog entry: PR [NousResearch/hermes-agent#153750](https://github.com/NousResearch/hermes-agent/pull/153750)
  — `plugin-catalog/strategic-arena.yaml`, pinned to `65d341c`.
- Validation: `hermes plugins validate --install-deps` passes on that exact commit.
- Video: <https://youtu.be/qrlA_0MJgB4>
- Hackathon form: the PR link and the video link, submitted together.
