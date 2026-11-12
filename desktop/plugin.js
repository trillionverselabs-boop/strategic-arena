// Upfront — desktop plugin (unified package, desktop half).
//
// Loads UNCOMPILED: no JSX. Only imports @hermes/plugin-sdk, react, react/jsx-runtime.
// Surfaces: LEFT sidebar nav row + full center page (ROUTES_AREA).
//
// Look: the app's own design language — SDK components, theme tokens, one type
// scale (T below), and colours used only to mean one thing each. No bitmaps, no
// custom font files, no prototype patching: everything here is theme variables
// and inline SVG, so the page reskins with every app theme.
//
// The design rule this file is built on: a number with no sentence next to it is
// noise. Every metric gets a name, a plain-language meaning, and — where it
// matters — the sentence a party actually said. That is what makes a 48-hour run
// watchable and a finished review worth keeping.

import {
  host,
  haptic,
  useValue,
  cn,
  Codicon,
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Select,
  SelectContent,
  Tabs,
  TabsList,
  TabsTrigger,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
} from '@hermes/plugin-sdk'
import React from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const BUILD = '0.6.4 · ui41'          // bump on every UI change — how you know the app reloaded
const PRODUCT_NAME = 'Strategic Arena'   // display only — one line to rename the product
const TAGLINE = 'Point it at a repo, a paper, a post — yours or someone else’s.'
// The line under the wordmark: what the product is *for*, in the fewest words
// that still say "this costs money you have not spent yet".
const SUBTITLE = 'Understand the landscape before investing valuable resources'
// The room has a name, and the name is the vocabulary: a session opens a
// Strategic Arena, the Arena debates, the Arena closes and writes the call.
const ARENA = 'Strategic Arena'
const SESSION = 'session'

// ── one type scale, used everywhere ───────────────────────────────────
// Inside SVG, `fontFamily: 'inherit'` picks up the app's own font, so the
// graphic and the prose share a voice instead of looking like two programs.
const T = {
  display: 'text-[1.6rem] font-semibold leading-[1.12] tracking-[-0.025em]',
  h1: 'text-[1.0625rem] font-semibold leading-tight tracking-[-0.015em]',
  h2: 'text-[0.875rem] font-semibold leading-tight',
  body: 'text-[0.8125rem] leading-[1.6]',
  small: 'text-[0.75rem] leading-[1.5]',
  micro: 'text-[0.6875rem] leading-[1.45]',
  label: 'text-[0.625rem] font-semibold uppercase tracking-[0.15em]',
}
const NUM = 'tabular-nums'

// Hue is for fills; text needs a lighter step of the same hue or it smudges into
// the dark background at 11px. One helper, so the graph and the prose agree.
const textTone = (hex) => `color-mix(in srgb, ${hex} 74%, white)`

// One meaning per colour. Nothing decorative is coloured.
// The SDK's default Button wears the app's `bg-primary`. A plugin may not restyle
// core UI, but it may style its own instance — so the product's primary action is
// the brand blue here, on the button, and nowhere else in the app.
// Two weights, one palette: the header carries the highest-contrast action (white
// on near-black), and actions inside a panel stay on the brand blue. A green
// button next to a blue one is how a palette starts looking accidental.
function LightAction({ children, className, style, ...rest }) {
  return jsx(Button, {
    ...rest,
    className: cn('transition-opacity hover:opacity-88', className),
    style: { backgroundColor: '#f1f4f9', color: '#0a0d12', ...(style || {}) },
    children,
  })
}

function PrimaryAction({ children, className, style, ...rest }) {
  return jsx(Button, {
    ...rest,
    className: cn('transition-opacity hover:opacity-88', className),
    style: { backgroundColor: BRAND.blue, color: '#04121f', ...(style || {}) },
    children,
  })
}

// One palette, built off the blue the product already reads as.
//
// Blue (behind it) and rose (will block it) are a complementary pair, with gold
// held between them for undecided — a cool→warm ramp instead of the red/green
// stoplight, which every dashboard uses and nobody reads. Direction is carried
// by the words on the labels and by *where* a party sits, never by hue alone:
// rose and blue are close in luminance, so a colour-blind reader loses nothing.
const BRAND = {
  blue: '#4c9bf0',        // the accent, and "behind it"
}
// Three meanings and a grey ramp. Violet used to mark "your side" and the
// interventions — a fourth hue doing a job that a word and a ring already do,
// and the one thing that made a page of charts read as a rainbow. Retired.
const C = {
  against: '#d9538f',   // will block — rose, the warm end of the ramp
  hold: '#e5b54a',      // undecided / conditional
  for: BRAND.blue,      // behind it, the primary action, and your own side
  ink: '#e8ecf2',       // label text on a canvas
  grey: '#7d8798',      // the neutral floor, and a quiet room
  // violet survives for exactly one job: the "purple ocean" badge on the field
  // read. It never colours a party, so it never sits in the same chart as a
  // stance and cannot muddy the ramp.
  halo: 'rgba(6,8,12,.86)',
}
const SEA = {
  red: { label: 'Red ocean', color: '#d9538f', meaning: 'everyone is fighting for the same fish — you will be read as another entrant' },
  purple: { label: 'Purple ocean', color: '#9b7be0', meaning: 'contested middle — winnable ground, but not free' },
  blue: { label: 'Nobody is fighting this yet', color: '#4c9bf0', meaning: 'no competitor, regulator or incumbent has engaged — which is good news and a warning: the risk here is indifference, not opposition' },
}
const SEA_ORDER = ['red', 'purple', 'blue']

const ACTION_WORD = {
  blocks: 'against it', supports: 'behind it', shares: 'conditional',
  waits: 'holding back', intervention: 'you changed the situation',
}

// eta = realistic wall-clock on a free, rate-limited model — the number that
// decides whether a 24h review is a 5-minute check or a 30-minute wait.
// What was handed in sets the room. Auto-detect reads it off the link; the
// chooser is there for when the link is ambiguous or the text is a draft.
const KINDS = [
  { v: 'auto', label: 'Auto-detect from the link' },
  { v: 'repo', label: 'Repo / README' },
  { v: 'post', label: 'Blog post / essay' },
  { v: 'whitepaper', label: 'Whitepaper / spec (defensibility review)' },
  { v: 'paper', label: 'Research paper — what product, who fights it' },
  { v: 'case_study', label: 'Case study' },
  { v: 'press', label: 'Press release / announcement' },
  { v: 'tweet', label: 'Social post' },
  { v: 'decision', label: 'Internal decision / memo' },
]
const KIND_ROOM = {
  repo: 'maintainers, security reviewers, downstream developers, the project it displaces, the registry that lists it',
  post: 'the reader who quotes it, the competitor it attacks, the parties it cites, the curator who decides if it travels',
  whitepaper: 'the reviewer who checks the method, procurement, the peer it extends or contradicts, the implementer',
  paper: "the incumbent it attacks, the fast follower who can ship it, the buyer with the budget, the integrator whose switching cost is the moat, the channel, and the authors' own lab",
  case_study: 'the customer named, the buyer who needs a comparable, procurement, the competitor in the same evaluation',
  press: 'the journalist, the incumbent, the regulator, the existing customers',
  tweet: 'the reply-guy, the quote-tweeter, the silent majority, the account it names',
  decision: 'approvers with a veto, the teams whose work changes, customers, the market it enters',
}

const TIMELINES = [
  { v: '30m', label: '30 minutes', rounds: 3, note: 'Sanity check — does anyone care at all? Cheapest.', eta: '2–5 min' },
  { v: '1h', label: '1 hour', rounds: 5, note: 'First reactions only. Good for a fast no.', eta: '4–8 min' },
  { v: '4h', label: '4 hours', rounds: 8, note: 'Positions form. Catches the obvious blocker.', eta: '6–12 min' },
  { v: '6h', label: '6 hours', rounds: 10, note: 'Coalitions start to show.', eta: '8–15 min' },
  { v: '12h', label: '12 hours', rounds: 12, note: 'Counter-moves get tested.', eta: '10–20 min' },
  { v: '24h', label: '24 hours', rounds: 16, note: 'Confirmation, not discovery — past the plateau, this re-tests what the room already settled.', eta: '15–30 min' },
  { v: '48h', label: '48 hours', rounds: 20, note: 'The longest window: room for a late counter-move. ~2x the calls of 1 hour for almost no new position.', eta: '25–45 min' },
]
const WINDOW_HOURS = { '30m': 0.5, '1h': 1, '4h': 4, '6h': 6, '12h': 12, '24h': 24, '48h': 48 }

// ── what a run will cost, before it runs ──────────────────────────────
// Two honest numbers and one honest refusal. Tokens are arithmetic: rounds x
// parties, plus the setup calls, times the size of the prompt the engine will
// actually send — and that prompt is bounded (ingestion.PROMPT_BUDGET), so the
// estimate cannot drift with the length of the paper you paste.
//
// Money is NOT arithmetic. A price needs the live catalogue and the provider's
// own rate; a number we invented would look like data, which is the one thing
// this product refuses to print. So it says "free" only when the model's own
// slug says free, and otherwise says nothing: every finished run records the
// model that actually served it.
const PARTIES_GUESS = 6          // the room is drawn after the read; 5-7 is typical
const INSTRUCTION_TOKENS = 2200  // lens + room instructions + output schema, per call
const DOC_TOKEN_CAP = 3000       // the excerpt window (~12k chars) is ~3k tokens
const OUT_TOKENS = 140           // one party's move per round is short JSON

function tokensOfInput(shape) {
  const chars = (shape.decision || '').length + (shape.evidence || '').length
    + (shape.urls || []).length * 12000     // each link is fetched, then windowed
  return Math.min(DOC_TOKEN_CAP, Math.round(chars / 4))
}

function runEstimate(tl, shape) {
  // a paper pays one extra call: the moat decode, before the room is drawn
  const setup = shape.kind === 'paper' ? 3 : 2
  const calls = tl.rounds * PARTIES_GUESS + setup
  const perCallIn = INSTRUCTION_TOKENS + tokensOfInput(shape)
  return { calls, parties: PARTIES_GUESS, tin: calls * perCallIn, tout: calls * OUT_TOKENS }
}

function kTokens(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : `${n}`
}

// The recommendation is about the INPUT, not about a default. One internal memo
// and a public launch do not want the same room-length, and the engine's own
// evidence is that positions stop moving after 8-10 rounds — past that you pay
// again for the same answer.
function suggestWindow(shape) {
  const external = ['press', 'tweet', 'repo', 'paper'].includes(shape.kind)
    || (shape.urls || []).length > 0
  const grounded = (shape.evidence || '').trim().length > 0
  if (external && grounded) return { v: '12h', why: 'the parties are external, and you gave them evidence to argue with' }
  if (external) return { v: '6h', why: 'the parties are external, but nothing here grounds their reaction — expect the read to stay broad' }
  if (grounded) return { v: '4h', why: 'an internal decision with evidence behind it' }
  return { v: '1h', why: 'one internal document — this answers "does anyone care?"' }
}

const URL_TYPES = [
  'repo README', 'blog post', 'news article', 'product / landing page',
  'pricing page', 'forum or Reddit thread', 'whitepaper / PDF', 'internal memo (if public)',
]

// Recipes: which sources produce which kind of review. This is the bridge between
// "what do I paste" and "what result do I want".
const RECIPES = [
  {
    id: 'launch', label: 'Launch / adoption', goal: 'adoption',
    title: 'Launching <product> — will they adopt it?',
    decision: 'We are launching <product> on <date>. It does <what>, for <who>, at <price>. ' +
      'The change for them is <what changes>. Support will be <plan>.',
    evidence: 'Adoption data you already have: waitlist size, pricing tests, competitor share, ' +
      'survey results, churn numbers — anything factual a stakeholder would react to.',
    urls: 'product landing page, competitor pricing page, community thread about the problem',
  },
  {
    id: 'price', label: 'Price change', goal: 'campaign',
    title: 'Raising prices <x>%',
    decision: 'We are raising <plan> from <old> to <new> on <date>, with <notice period> notice. ' +
      'Existing customers <grandfathering terms>. Sales commission changes <how>.',
    evidence: 'Current price, churn, gross margin, competitor prices, win/loss reasons.',
    urls: 'pricing page, competitor pricing page, forum threads complaining about price',
  },
  {
    id: 'deprecate', label: 'Deprecation', goal: 'deprecation',
    title: 'Retiring <feature / API>',
    decision: 'We are retiring <thing> on <date>. Migration path is <plan>. Support ends <when>. ' +
      'Who is affected: <segments>.',
    evidence: 'Usage share of the feature, number of accounts affected, migration effort estimates.',
    urls: 'changelog entry, docs page being removed, forum thread where users discuss it',
  },
  {
    id: 'openweight', label: 'Open-weight release', goal: 'open_weight',
    title: 'Open-weighting <model>',
    decision: 'We are releasing the weights for <model> under <licence>, with <training data / evals> ' +
      'published. Hosted API <stays / changes> for <period>.',
    evidence: 'Licence terms, benchmark results, enterprise compliance survey data, download trends.',
    urls: 'model card, licence page, competitor open-weight release, compliance blog post',
  },
  {
    id: 'crisis', label: 'Reputation / crisis', goal: 'campaign',
    title: 'Responding to <incident>',
    decision: 'We are publishing a response to <incident> on <date>. We accept <what>, deny <what>, ' +
      'and commit to <remedy>. The tone is <apologetic / factual / firm>.',
    evidence: 'Incident timeline, affected customer count, what competitors did in similar cases.',
    urls: 'news article covering it, the social thread, our public postmortem',
  },
]

const SOURCE_GUIDE = [
  ['Decision memo / release note', 'the move and its scope — the core input'],
  ['Survey, metrics, quotes', 'calibrated stances instead of invented ones (biggest quality lever)'],
  ['Repo README', 'technical objections, the developer audience'],
  ['Blog post', 'public positioning — how it will be read'],
  ['News article', 'reputational and regulator attention'],
  ['Pricing page', 'commercial objections: procurement, competitors'],
  ['Forum / Reddit thread', 'the loud minority and the real objections'],
  ['Whitepaper / PDF', 'enterprise and regulatory framing'],
]

// The sample is the demo. It has to show a real fight with a winnable middle, not a
// room where everyone agrees: one party who can stop it, two with conditions, and the
// people who gain. That is what a dry run means on screen.
const SAMPLE = {
  title: 'Open-weight Arete-27B',
  decision:
    'Nous is considering open-weighting Arete-27B. The weights ship under a permissive licence ' +
    'on release day, with the full training data and eval suite published alongside. The hosted ' +
    'API stays free for the first 90 days so people can try it before committing.',
  evidence:
    'Q2 survey of 400 enterprise CIOs: 61% said they cannot route inference through an external ' +
    'API for compliance reasons, and open-weight model downloads tripled quarter over quarter. ' +
    'Community fine-tunes now outnumber closed-model adaptations 3:1. Finance has reservations: it ' +
    'wants the 90-day free API window capped at a fixed budget before it will sign off. Two ' +
    'enterprise resellers have asked for a protection clause, which they call a fixable detail ' +
    'rather than a veto. Legal needs the two vendor data licences cleared before the training set ' +
    'can be published.',
}

// ── atoms ─────────────────────────────────────────────────────────────

const FIELD_LABEL = `${T.label} text-(--ui-text-quaternary)`

function Field({ label, hint, right, children }) {
  return jsxs('label', { className: 'flex flex-col gap-1', children: [
    jsxs('span', { className: 'flex items-center justify-between', children: [
      jsx('span', { className: FIELD_LABEL, children: label }),
      right || null,
    ]}),
    children,
    hint ? jsx('span', { className: 'text-[0.625rem] leading-tight text-(--ui-text-quaternary)', children: hint }) : null,
  ]})
}

function Section({ label, action, children }) {
  return jsxs('section', { className: 'flex flex-col gap-1.5', children: [
    jsxs('div', { className: 'flex items-center justify-between', children: [
      jsx('div', { className: FIELD_LABEL, children: label }),
      action || null,
    ]}),
    children,
  ]})
}

// Tinted advisory panel: a tone-washed body with a matching left rule.
function Callout({ icon = 'info', title, tone = 'var(--ui-accent)', children }) {
  return jsxs('div', {
    className: 'flex flex-col gap-1.5 rounded-lg p-3',
    style: { backgroundColor: `color-mix(in srgb, ${tone} 8%, transparent)`, borderLeft: `2px solid ${tone}` },
    children: [
      jsxs('div', { className: 'flex items-start gap-2 text-[0.8125rem] font-medium', style: { color: tone }, children: [
        jsx(Codicon, { className: 'mt-px shrink-0', name: icon, size: '0.85rem' }),
        jsx('span', { children: title }),
      ]}),
      children,
    ],
  })
}

// The board's card: elevated fill, hairline border, generous padding. `tone` adds
// a coloured left rule, used only where a card is making a claim.
function Card({ children, className, tone, pad }) {
  return jsx('div', {
    className: cn('flex flex-col gap-2.5 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated)',
      pad === 'none' ? '' : 'p-4', className),
    style: tone ? { borderLeftWidth: 2, borderLeftColor: tone } : undefined,
    children,
  })
}

function Label({ children, className }) {
  return jsx('div', { className: cn(FIELD_LABEL, className), children })
}

// ── mark ──────────────────────────────────────────────────────────────
// The axis is the product: left = against the move, right = behind it, and the
// ringed dot is the party who can actually stop it. Drawn from theme variables
// so it survives every theme.

function Mark({ size = 40 }) {
  const s = size
  return jsxs('svg', {
    width: s, height: s, viewBox: '0 0 48 48', fill: 'none',
    'aria-hidden': 'true', className: 'shrink-0',
    children: [
      jsx('rect', { x: 0.75, y: 0.75, width: 46.5, height: 46.5, rx: 11.5,
        style: { fill: 'color-mix(in srgb, var(--ui-accent) 10%, transparent)', stroke: 'color-mix(in srgb, var(--ui-accent) 34%, transparent)', strokeWidth: 1.5 } }),
      jsx('line', { x1: 7, y1: 27, x2: 41, y2: 27, stroke: 'url(#upaxis)', strokeWidth: 2.2, strokeLinecap: 'round' }),
      jsx('defs', { children: jsxs('linearGradient', { id: 'upaxis', x1: '0', y1: '0', x2: '1', y2: '0', children: [
        jsx('stop', { offset: '0', stopColor: C.against }),
        jsx('stop', { offset: '0.55', stopColor: C.hold }),
        jsx('stop', { offset: '1', stopColor: C.for }),
      ]}) }),
      // the scale itself: three parties of different weight on one axis, and
      // the ring marks the one that decides the room. Deliberately monochrome
      // so it can never be read as window chrome.
      jsx('circle', { cx: 11, cy: 27, r: 3.2, style: { fill: 'var(--ui-text-quaternary)' } }),
      jsx('circle', { cx: 24, cy: 27, r: 4.6, style: { fill: 'var(--ui-text-secondary)' } }),
      jsx('circle', { cx: 37, cy: 27, r: 6.4, style: { fill: 'var(--ui-text-primary)' } }),
      jsx('circle', { cx: 37, cy: 27, r: 10.4, fill: 'none',
        style: { stroke: 'var(--ui-accent)', strokeWidth: 1.8 } }),
      jsx('circle', { cx: 37, cy: 27, r: 13.6, fill: 'none',
        style: { stroke: 'var(--ui-accent)', strokeWidth: 0.9, opacity: 0.4 } }),

    ],
  })
}

function Wordmark({ size = 40 }) {
  return jsxs('div', { className: 'flex items-center gap-2.5', children: [
    jsx(Mark, { size }),
    jsxs('div', { className: 'flex min-w-0 flex-col', children: [
      jsx('div', { className: 'text-[0.9375rem] font-semibold leading-none tracking-[-0.01em]', children: PRODUCT_NAME }),
      // the subtitle is a sentence, not a label: it wraps to two lines in a
      // 260px sidebar rather than clipping, and min-w-0 is what lets it.
      jsx('div', { className: cn(T.label, 'mt-1 max-w-[16rem] leading-[1.3] text-(--ui-text-quaternary)'), children: SUBTITLE }),
    ]}),
  ]})
}

// ── small formatters ──────────────────────────────────────────────────

function ago(iso) {
  if (!iso) return ''
  const t = Date.parse(iso)
  if (!t) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 90) return 'just now'
  const m = s / 60
  if (m < 60) return `${Math.round(m)} min ago`
  const h = m / 60
  if (h < 24) return `${Math.round(h)} h ago`
  const d = h / 24
  if (d < 7) return `${Math.round(d)} d ago`
  return `${Math.round(d / 7)} w ago`
}

function until(iso) {
  if (!iso) return ''
  const t = Date.parse(iso)
  if (!t) return ''
  let s = (t - Date.now()) / 1000
  if (s <= 0) return 'due now'
  const h = s / 3600
  if (h < 1) return `${Math.max(1, Math.round(s / 60))} min`
  if (h < 48) return `${Math.round(h)} h`
  return `${Math.round(h / 24)} d`
}

function signed(v) {
  const n = Number(v)
  if (!isFinite(n)) return '0.0'
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`
}

function dueAt(run) {
  const hours = WINDOW_HOURS[run.window] || 24
  const t = Date.parse(run.created_at || '')
  if (!t) return ''
  return new Date(t + hours * 3600 * 1000).toISOString()
}

// ── stance vocabulary ─────────────────────────────────────────────────
// The number is the machine's. The reader gets the word and the colour, and the
// number survives only as a small tie-breaker between two parties.

function stanceTone(s) {
  const n = Number(s) || 0
  if (n <= -0.6) return { color: C.against, word: 'will block it', short: 'blow it up' }
  if (n <= -0.3) return { color: C.against, word: 'against it', short: 'against' }
  if (n < 0.3) return { color: C.hold, word: 'undecided', short: 'undecided' }
  if (n < 0.6) return { color: C.for, word: 'leaning in', short: 'leaning in' }
  return { color: C.for, word: 'behind it', short: 'behind it' }
}

function powerWord(cap) {
  if (cap == null) return 'power not assessed'
  const n = Number(cap)
  if (n >= 0.7) return 'can stop it outright'
  if (n >= 0.4) return 'can slow it or charge you for it'
  return 'can complain, not stop it'
}

function frictionBand(f) {
  const n = Number(f) || 0
  if (n < 20) return { name: 'Nobody is in your way', color: C.grey,
    why: 'Either most of the people who matter are behind it, or nobody with power has bothered to engage. Those look the same on a score and are very different in reality, so read the claims below more carefully than the number: a quiet room can hide indifference.' }
  if (n < 45) return { name: 'Winnable ground', color: C.for,
    why: 'Somebody objects, but nobody is dug in. This is the band where a single good counter-move changes the outcome.' }
  if (n < 65) return { name: 'A fight', color: C.hold,
    why: 'At least one party is working against you and has the power to make it cost. Expect a hard conversation before this lands.' }
  return { name: 'A brawl', color: C.against,
    why: 'Several parties are against it and at least one can stop it. Do not launch on this read — talk to the objectors first.' }
}

// A number the reader can place: where 52 sits on the only scale that matters.
function FrictionGauge({ friction, width = 200, height = 8 }) {
  const pct = Math.max(0, Math.min(100, Number(friction) || 0))
  const band = frictionBand(friction)
  return jsxs('div', { className: 'flex items-center gap-2.5', children: [
    jsxs('div', {
      className: 'relative overflow-hidden rounded-full',
      style: {
        width: `${width}px`, height: `${height}px`,
        // cool → warm: the same ramp the parties use, so the gauge and the room
        // cannot read as two different scales
        background: `linear-gradient(90deg, ${C.for} 0%, ${C.for} 22%, ${C.hold} 45%, ${C.hold} 62%, ${C.against} 84%, ${C.against} 100%)`,
        opacity: 0.28,
      },
      children: [
        jsx('div', {
          className: 'absolute top-0 h-full rounded-full',
          style: { width: `${pct}%`, backgroundColor: band.color, opacity: 0.9 },
        }),
      ],
    }),
    jsxs('span', { className: `flex items-baseline gap-1.5 ${T.small}`, children: [
      jsx('span', { className: `font-semibold ${NUM}`, style: { color: band.color }, children: band.name }),
      jsx('span', { className: `text-(--ui-text-tertiary) ${NUM}`, children: `${pct.toFixed(0)}/100` }),
    ]}),
  ]})
}

// ── the room: one ordered board, no numbered dots ─────────────────────
// Sorted from "will block" to "behind it". Each row carries a gauge centred on
// neutral, so a reader can see direction and distance without reading a number,
// and a power meter, so "can this party stop me" is answered in the same glance.

function StanceMeter({ value, height = 9 }) {
  const v = Math.max(-1, Math.min(1, Number(value) || 0))
  const pct = Math.abs(v) * 50
  const tone = stanceTone(v).color
  return jsxs('div', {
    className: 'relative w-full overflow-hidden rounded-full bg-(--ui-bg-quaternary)',
    style: { height: `${height}px` },
    children: [
      jsx('div', { className: 'absolute top-0 h-full', style: {
        left: v >= 0 ? '50%' : `${50 - pct}%`, width: `${pct}%`, borderRadius: 999,
        // faint at the neutral line, saturated at the far end: length is the
        // direction, depth is how hard they mean it
        background: v >= 0
          ? `linear-gradient(90deg, color-mix(in srgb, ${tone} 22%, transparent), ${tone})`
          : `linear-gradient(270deg, color-mix(in srgb, ${tone} 22%, transparent), ${tone})`,
      } }),
      jsx('div', { className: 'absolute inset-y-0', style: { left: '50%', width: '1px',
        backgroundColor: 'var(--ui-stroke-secondary)' } }),
    ],
  })
}

function PowerPips({ cap, color }) {
  const n = cap == null ? 0 : Math.max(0, Math.min(1, Number(cap)))
  const filled = Math.round(n * 3)
  return jsx('span', {
    className: 'flex items-center gap-0.5',
    title: powerWord(cap),
    children: [0, 1, 2].map(i => jsx('span', {
      key: `p${i}`,
      className: 'inline-block rounded-[1px]',
      style: {
        width: '4px', height: `${7 + i * 2}px`,
        backgroundColor: i < filled ? (color || 'var(--ui-accent)') : 'var(--ui-stroke-secondary)',
        opacity: i < filled ? 0.95 : 0.55,
      },
    })),
  })
}

function PowerWord({ cap }) {
  if (cap == null) return null
  const n = Number(cap)
  const w = n >= 0.7 ? 'can stop it' : n >= 0.4 ? 'can slow it' : 'can only complain'
  return jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: w })
}

// Three groups, named and counted, so the scale is a reading of the room and not
// a colour legend. Counts come from the parties themselves.
function ZoneStrip({ list }) {
  const zones = [
    { key: 'against', label: 'will block it', tone: C.against,
      hint: 'can stop you or make it cost',
      n: list.filter(n => (Number(n.stance) || 0) <= -0.3).length },
    { key: 'undecided', label: 'undecided', tone: C.hold,
      hint: 'moves if the reason is good',
      n: list.filter(n => (Number(n.stance) || 0) > -0.3 && (Number(n.stance) || 0) < 0.3).length },
    { key: 'for', label: 'behind it', tone: C.for,
      hint: 'already with you',
      n: list.filter(n => (Number(n.stance) || 0) >= 0.3).length },
  ]
  return jsxs('div', { className: 'flex items-stretch gap-3 pb-2', children: [
    jsx('div', { className: 'w-[10rem] shrink-0' }),
    jsxs('div', { className: 'grid flex-1 grid-cols-3 gap-1.5', children: zones.map(z => jsxs('div', {
      className: 'flex flex-col gap-0.5 rounded-md px-2 py-1.5',
      style: {
        backgroundColor: `color-mix(in srgb, ${z.tone} 9%, transparent)`,
        borderTop: `2px solid ${z.tone}`,
      },
      children: [
        jsxs('div', { className: 'flex items-baseline gap-1.5', children: [
          jsx('span', { className: `${T.micro} font-semibold uppercase tracking-[0.1em]`, style: { color: z.tone },
            children: z.label }),
          jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-tertiary)`, children: String(z.n) }),
        ]}),
        jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: z.hint }),
      ],
    })) }),
    jsx('div', { className: `w-[6.5rem] shrink-0 text-right ${T.label} text-(--ui-text-quaternary)`, children: 'power to stop' }),
  ]})
}

function RoomBoard({ nodes, previous, ownSide, blocker, deltas }) {
  const list = (nodes || []).slice().sort((a, b) => (Number(a.stance) || 0) - (Number(b.stance) || 0))
  // One line per party, grouped by what it means. The old version gave every
  // party a paragraph, three lines and a meter — seven parties filled a screen
  // and a half, and the reader scrolled past the answer to find the room. The
  // reason is still here: on the row's title, and behind one toggle that opens
  // all of them for anyone who wants the argument.
  const [showWhy, setShowWhy] = React.useState(false)
  if (!list.length) {
    return jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: 'No parties yet.' })
  }
  const own = new Set(ownSide || [])
  const zones = [
    { key: 'against', label: 'will block it', tone: C.against, rows: list.filter(n => (Number(n.stance) || 0) <= -0.3) },
    { key: 'undecided', label: 'undecided', tone: C.hold, rows: list.filter(n => (Number(n.stance) || 0) > -0.3 && (Number(n.stance) || 0) < 0.3) },
    { key: 'for', label: 'behind it', tone: C.for, rows: list.filter(n => (Number(n.stance) || 0) >= 0.3) },
  ]
  return jsxs('div', { className: 'flex flex-col', children: [
    // three named groups, counted — the scale answers "what does this mean"
    jsx(ZoneStrip, { list }),
    ...zones.filter(z => z.rows.length).map(z => jsxs('div', { className: 'flex flex-col', children: [
      jsx('div', { className: `flex items-baseline gap-2 pt-2 pb-1 ${T.label} uppercase tracking-[0.1em]`,
        style: { color: z.tone }, children: z.label }),
      ...z.rows.map((n, i) => {
        const tone = stanceTone(n.stance)
        const isBlocker = blocker && (n.name === blocker)
        const d = deltas && deltas[n.name] != null ? Number(deltas[n.name]) : null
        const why = (n.reasons && n.reasons[0]) || ''
        return jsxs('div', {
          key: n.id || n.name || `r${i}`,
          className: 'flex flex-col border-t border-(--ui-stroke-tertiary)',
          children: [
            jsxs('div', {
              className: 'flex items-center gap-2 py-1',
              title: why ? `${n.name} — ${why}` : n.name,
              children: [
                jsx('span', { className: 'inline-block size-1.5 shrink-0 rounded-full',
                  style: { backgroundColor: tone.color } }),
                jsx('span', { className: `min-w-0 flex-1 truncate text-[0.75rem] font-medium`,
                  children: n.name }),
                isBlocker ? jsx('span', { className: `${T.micro} shrink-0 font-semibold`,
                  style: { color: C.against }, children: 'can stop it' })
                  : own.has(n.name) ? jsx('span', { className: `${T.micro} shrink-0`,
                    style: { color: C.for }, children: 'your side' })
                  : jsx('span', { className: `${T.micro} shrink-0`, style: { color: tone.color },
                    children: tone.word }),
                jsx('div', { className: 'w-[6rem] shrink-0', children: jsx(StanceMeter, { value: n.stance }) }),
                jsx('span', { className: `w-[5.5rem] shrink-0 text-right ${T.micro} text-(--ui-text-quaternary)`,
                  children: jsx(PowerWord, { cap: n.capacity }) }),
                jsx('span', { className: `w-[3.6rem] shrink-0 text-right ${T.micro} ${NUM}`,
                  style: { color: d != null && Math.abs(d) >= 0.05 ? (d > 0 ? C.for : C.against) : undefined },
                  children: d != null && Math.abs(d) >= 0.05
                    ? `${d > 0 ? '▲' : '▼'} ${Math.abs(d).toFixed(1)}` : '' }),
              ],
            }),
            showWhy && why
              ? jsx('div', { className: `pb-1 pl-3 ${T.micro} leading-snug text-(--ui-text-tertiary)`,
                  children: why })
              : null,
          ],
        })
      }),
    ]})),
    jsxs('div', { className: `flex flex-wrap items-center gap-x-2 gap-y-1 pt-2 ${T.micro} text-(--ui-text-quaternary)`, children: [
      jsx('span', { children: 'Bar length = how strongly they back or oppose it, from the centre. Power = how much they can stop you outright.' }),
      jsx(Button, { size: 'xs', variant: 'ghost', onClick: () => setShowWhy(v => !v),
        children: showWhy ? 'hide the reasons' : 'why each one is here' }),
    ]}),
  ]})
}

// ── how positions moved (the time dimension) ──────────────────────────
// OASIS's point made visible: this is a run over time, not a snapshot. One line
// per party, labelled at the right edge where the line ends.

function MovementChart({ snapshots, height = 190 }) {
  const rows = (snapshots || []).filter(s => s && s.stances && Object.keys(s.stances).length)
  if (rows.length < 2) return null
  const w = 780
  const padL = 12, padR = 156, padT = 16, padB = 26
  const names = Object.keys(rows[rows.length - 1].stances)
  const xs = (i) => padL + (rows.length === 1 ? 0 : (i / (rows.length - 1)) * (w - padL - padR))
  const ys = (v) => padT + ((1 - Math.max(-1, Math.min(1, Number(v) || 0))) / 2) * (height - padT - padB)
  // walk the labels top-to-bottom; walking bottom-up cascades every label into
  // the lower half of the chart
  const ends = names.map(n => ({ name: n, v: Number(rows[rows.length - 1].stances[n]) || 0 }))
    .sort((a, b) => b.v - a.v)
  // spread the end labels so they never overlap
  const gap = 14
  ends.forEach((e, i) => { e.y = Math.max(padT, Math.min(height - padB, ys(e.v))) })
  for (let i = 1; i < ends.length; i++) {
    if (ends[i].y - ends[i - 1].y < gap) ends[i].y = ends[i - 1].y + gap
  }
  const overflow = ends.length ? ends[ends.length - 1].y - (height - padB) : 0
  if (overflow > 0) ends.forEach(e => { e.y -= overflow })
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsx('div', { className: `${T.small} font-medium`, children: 'How positions moved' }),
    jsxs('svg', {
      viewBox: `0 0 ${w} ${height}`, className: 'w-full',
      style: { fontFamily: 'inherit' },
      children: [
        jsx('rect', { x: 0, y: 0, width: w, height: height, fill: 'transparent' }),
        // neutral midline
        jsx('line', { x1: padL, y1: ys(0), x2: w - padR, y2: ys(0),
          style: { stroke: 'var(--ui-stroke-tertiary)', strokeDasharray: '3 4' } }),
        jsx('text', { x: padL, y: ys(0) - 5, fontSize: '11', fontWeight: 500,
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' }, children: 'neutral' }),
        jsx('text', { x: padL, y: ys(1) + 12, fontSize: '10', fontWeight: 500,
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' }, children: 'for it' }),
        jsx('text', { x: padL, y: ys(-1) - 5, fontSize: '10', fontWeight: 500,
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' }, children: 'against' }),
        ...rows.map((r, i) => jsx('line', {
          x1: xs(i), y1: height - padB + 3, x2: xs(i), y2: height - padB,
          style: { stroke: 'var(--ui-stroke-tertiary)' },
        })),
        jsx('text', { x: xs(0), y: height - 6, fontSize: '10.5', textAnchor: 'start',
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' }, children: 'round 1' }),
        jsx('text', { x: xs(rows.length - 1), y: height - 6, fontSize: '10.5', textAnchor: 'end',
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' }, children: `round ${rows[rows.length - 1].round || rows.length}` }),
        ...names.map((n) => {
          const tone = stanceTone(rows[rows.length - 1].stances[n]).color
          const d = rows.map((r, i) => (r.stances[n] == null ? null : `${xs(i)},${ys(r.stances[n])}`))
            .filter(Boolean).join(' ')
          const end = ends.find(e => e.name === n)
          return jsxs('g', { children: [
            jsx('polyline', { points: d, fill: 'none',
              style: { stroke: tone, strokeWidth: 1.6, strokeLinejoin: 'round', opacity: 0.85 } }),
            jsx('circle', { cx: xs(rows.length - 1), cy: ys(rows[rows.length - 1].stances[n]), r: 2.6, fill: tone }),
            jsx('circle', { cx: w - padR + 3, cy: (end ? end.y : ys(0)), r: 2.4, fill: tone }),
            jsx('text', { x: w - padR + 10, y: (end ? end.y : ys(0)) + 4, fontSize: '11.5', fontWeight: 600,
              style: { fill: 'var(--ui-text-secondary)', fontFamily: 'inherit',
                       paintOrder: 'stroke', stroke: 'var(--ui-bg-elevated)', strokeWidth: 4 },
              children: n.length > 24 ? n.slice(0, 23) + '…' : n }),
          ]})
        }),
      ],
    }),
  ]})
}




// ── the paper lens, explained where it is chosen ───────────────────────
// A research paper is the one artifact read twice: as a product (what could be
// built, and how long the advantage survives being published) and as a market
// (who would fight it). That is unusual enough that it has to be said on the
// form. Someone who expected a peer review would otherwise read the answer as a
// bug, and someone who expected a forecast would read it as a failure.
// Every other lens answers one question: will this land, who reacts, who can stop it,
// what each concession buys. A paper gets a different question with a different
// answer — not whether it lands, but whether it is worth building at all, and for
// how long. That is a different outcome, and the form says so next to the chooser.
const PAPER_DIFF = [
  ['the question',
   'will this land, and who can stop it',
   'what could be built from this, and how long is it safe'],
  ['the room',
   'the people who react to what you are about to do',
   "the market that would receive the product — including the authors, who are usually the first competitor"],
  ['you get back',
   'friction, the veto player, what each concession buys',
   'the product and the buyer, what it gives away vs holds back, and the replication clock'],
]
const PAPER_IS_NOT = 'Not a peer review, and not a forecast: no revenue, no market share. It reads '
  + 'what the paper GIVES AWAY, because publishing is the moment a technique becomes copyable.'

function PaperLensNote() {
  return jsxs(Card, { tone: C.hold, children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: 'Why a paper is a different question' }),
      jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'same engine, different answer' }),
    ]}),
    jsx('div', { className: `${T.body} text-(--ui-text-secondary)`,
      children: 'The other lenses tell you what happens when you do something. This one tells you '
        + 'what the paper itself is worth building into — before you build it.' }),
    jsxs('div', { className: 'grid grid-cols-[minmax(0,5.5rem)_minmax(0,1fr)_minmax(0,1fr)] gap-x-2 gap-y-1.5', children: [
      jsx('div', {}),
      jsx('div', { className: `${T.micro} ${NUM} text-(--ui-text-quaternary)`, children: 'THE OTHER LENSES' }),
      jsx('div', { className: `${T.micro} ${NUM} text-(--ui-text-secondary)`, children: 'A RESEARCH PAPER' }),
      ...PAPER_DIFF.map(([k, other, paper]) => [
        jsx('div', { className: `${T.label} text-(--ui-text-quaternary)`, children: k }),
        jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: other }),
        jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: paper }),
      ]).flat(),
    ]}),
    jsx('div', { className: `${T.small} border-t border-(--ui-stroke-tertiary) pt-1.5 text-(--ui-text-quaternary)`,
      children: PAPER_IS_NOT }),
  ]})
}

// ── what the paper gives away, on the result page ──────────────────────
// The clock is the answer, so it leads. Gives-away / holds-back sit side by side
// because the whole judgement is the difference between them: everything in the
// left column can be rebuilt by anyone who reads the same PDF.
const CLOCK_TONE = { commodity: C.against, contested: C.hold, protected: C.for, unknown: C.grey }
const CLOCK_WORD = {
  commodity: 'a feature, not a company',
  contested: 'a head start — if you spend it',
  protected: 'something the paper withholds',
  unknown: 'no basis for a number',
}

function PaperRead({ moat }) {
  // Collapsed by default. The answer card above already states the product, the
  // buyer and the clock; this is the *evidence* for the clock, and evidence is
  // something a reader chooses to open. The old version printed two bullet lists
  // and three paragraphs unconditionally, which is most of why the page read as
  // a wall.
  const [open, setOpen] = React.useState(false)
  if (!moat || (!moat.product && !moat.error)) return null
  if (moat.error && !moat.product) {
    return jsx(Callout, { icon: 'warning', tone: C.hold, title: 'The paper decode did not complete',
      children: jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children:
        `${moat.error}. The market read below is still valid — it just has no replication clock, `
        + 'so treat the timing as unknown rather than safe. Re-run to decode it.' }) })
  }
  const tone = CLOCK_TONE[moat.clock] || C.grey
  const months = typeof moat.replication_months === 'number' ? moat.replication_months : null
  const clockBig = months == null ? 'unknown' : `~${Math.round(months)} ${Math.round(months) === 1 ? 'month' : 'months'}`
  const nDis = (moat.disclosed || []).length
  const nTac = (moat.tacit || []).length
  return jsxs(Card, { tone, children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsxs('div', { className: 'flex items-baseline gap-2', children: [
        jsx('div', { className: T.h2, children: 'How long the lead lasts' }),
        jsx('span', { className: `${NUM} text-[0.9375rem] font-semibold leading-none`,
          style: { color: textTone(tone) }, children: clockBig }),
        jsx('span', { className: `${T.small}`, style: { color: textTone(tone) }, children: CLOCK_WORD[moat.clock] || '' }),
      ]}),
      jsx(Button, { size: 'xs', variant: 'ghost', onClick: () => setOpen(v => !v),
        children: open ? 'hide the evidence' : 'show the evidence' }),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
      children: moat.clock_why || '' }),
    jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
      children: `${nDis} things a rebuilder gets free from the PDF · ${nTac} it holds back`
        + (moat.replication_basis ? ` · basis: ${moat.replication_basis}` : '') }),

    open && jsxs('div', { className: 'flex flex-col gap-2' , children: [
      nDis || nTac ? jsx('div', { className: 'grid gap-3 border-t border-(--ui-stroke-tertiary) pt-2 sm:grid-cols-2', children: [
        jsxs('div', { className: 'flex flex-col gap-1', children: [
          jsx('div', { className: `${T.label}`, style: { color: textTone(C.against) }, children: 'gives away' }),
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'anyone with the PDF can rebuild this' }),
          ...(moat.disclosed || []).map(d => jsxs('div', { className: `${T.small} text-(--ui-text-secondary)`, children: ['· ', d] })),
        ]}),
        jsxs('div', { className: 'flex flex-col gap-1', children: [
          jsx('div', { className: `${T.label}`, style: { color: textTone(C.for) }, children: 'holds back' }),
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'the only thing a rebuilder has to guess' }),
          nTac
            ? (moat.tacit || []).map(d => jsxs('div', { className: `${T.small} text-(--ui-text-secondary)`, children: ['· ', d] }))
            : jsx('div', { className: `${T.small} text-(--ui-text-quaternary)`, children: 'nothing — the paper is complete, so nothing here slows a copy' }),
        ]}),
      ]}) : null,
      (moat.scale_dependence || moat.nearest_prior_art || moat.authors_position) ? jsxs('div', { className: 'flex flex-col gap-1 border-t border-(--ui-stroke-tertiary) pt-2', children: [
        moat.scale_dependence ? jsxs('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: ['Scale dependence: ', jsx('span', { className: 'text-(--ui-text-secondary)', children: moat.scale_dependence })] }) : null,
        moat.nearest_prior_art ? jsxs('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: ['Nearest prior art: ', jsx('span', { className: 'text-(--ui-text-secondary)', children: moat.nearest_prior_art })] }) : null,
        moat.authors_position ? jsxs('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: ['The authors: ', jsx('span', { className: 'text-(--ui-text-secondary)', children: moat.authors_position })] }) : null,
      ]}) : null,
    ]}),
  ]})
}

// ── what it means ──────────────────────────────────────────────────────
// The first thing a reader wants is not "who objects" — it is "what does this
// actually say, and what does that open for me". Three lines, written by the
// reader of the text during extraction, quoted rather than templated here.
const KIND_LABEL = {
  repo: 'a repository README', post: 'a blog post', whitepaper: 'a whitepaper or spec',
  paper: 'a research paper',
  case_study: 'a case study', press: 'a press release', tweet: 'a social post',
  decision: 'an internal decision',
}

// ── the answer, in five lines ─────────────────────────────────────────
// Everything below this card is evidence. The card is the decision: what could
// you build, who pays, who else can build it and how long you have, what the
// market looks like, and the one next move. Two lines per row, hard cap — a
// reader should be able to stop after this card and still act.

function firstSentence(text, cap = 200) {
  const s = String(text || '').replace(/\s+/g, ' ').trim()
  if (!s) return ''
  const m = s.match(/^.{20,}?[.!?](\s|$)/)
  const cut = m ? m[0] : s
  return cut.length > cap ? cut.slice(0, cap - 1).trimEnd() + '…' : cut
}

function AnswerRow({ label, value, title, tone }) {
  if (!value) return null
  return jsxs('div', {
    className: 'grid grid-cols-[7.5rem_minmax(0,1fr)] items-baseline gap-3 border-t border-(--ui-stroke-tertiary) py-1.5 first:border-t-0 first:pt-0',
    children: [
      jsx('div', { className: `${T.label} uppercase tracking-[0.1em]`, style: tone ? { color: tone } : undefined,
        children: label }),
      jsx('div', {
        className: `${T.small} leading-snug text-(--ui-text-secondary)`,
        title: title || value,
        // two lines, then stop: the long form is one click away, in the audit
        style: { display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' },
        children: value,
      }),
    ],
  })
}

function AnswerCard({ result }) {
  if (!result) return null
  const m = result.moat || {}
  const read = result.read || {}
  const sea = result.sea || {}
  const isPaper = result.kind === 'paper'
  const clock = m.clock && m.clock !== 'unknown'
    ? `${m.clock}${m.replication_months != null ? ` · ~${Math.round(m.replication_months)} months to rebuild` : ''}`
    : 'unknown — the paper states no basis for a number'
  // One idea per row: the prior art, on its own. Who the authors are is the
  // evidence for the clock, and it stays in the expander — a card that tries to
  // say both at once gets clipped at two lines and says neither.
  const competitors = isPaper
    ? firstSentence(m.nearest_prior_art || 'no prior art named', 160)
    : (result.blocker ? `${result.blocker} can stop it outright` : 'nobody with power has engaged')
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2 pb-2', children: [
      jsx('div', { className: T.h2, children: isPaper ? 'What this paper is worth building' : 'What this means for you' }),
      jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
        children: isPaper ? 'read as an entrepreneur deciding whether to build it — not a review of the method'
                          : 'read as the person who has to decide whether to do it' }),
    ]}),

    jsx(AnswerRow, { label: 'you could build', value: m.product || read.opening || read.claim }),
    jsx(AnswerRow, { label: isPaper ? 'who pays' : 'who decides',
      value: m.buyer || (result.blocker ? `${result.blocker} — the one who can stop it` : 'nobody with power has engaged') }),
    isPaper && jsx(AnswerRow, { label: 'lead time', value: clock, tone: m.clock === 'commodity' ? C.against : undefined }),
    jsx(AnswerRow, { label: isPaper ? 'who else can build it' : 'who else could', value: competitors }),
    jsx(AnswerRow, { label: 'the market', value: sea.label ? `${sea.label} — ${firstSentence(sea.why, 150)}` : read.displaces }),
    jsx(AnswerRow, { label: 'what to do', value: firstSentence(result.recommendation, 220), tone: C.ink }),
  ]})
}

function WhatItMeans({ read, kind }) {
  if (!read || !read.claim) return null
  const lines = [
    ['the claim', read.claim],
    ['what it displaces', read.displaces],
    ['the opening', read.opening],
  ].filter(l => l[1])
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: 'What it means' }),
      kind && KIND_LABEL[kind]
        ? jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: `read as ${KIND_LABEL[kind]}` })
        : null,
    ]}),
    jsx('div', { className: 'mt-1.5 grid gap-2 md:grid-cols-3', children: lines.map(([label, text]) =>
      jsxs('div', { className: 'flex flex-col gap-0.5', children: [
        jsx('div', { className: `${T.label} text-(--ui-text-quaternary)`, children: label }),
        jsx('div', { className: `${T.body} text-(--ui-text-secondary)`, children: text }),
      ]})) }),
  ]})
}

// ── what's already on your side ────────────────────────────────────────
// An objection is only half the room. The parties who are for you are cooling it
// — and their reasons are the arguments you are allowed to make, in their words.
function OnYourSide({ personas, lev }) {
  const priced = new Map(((lev && lev.parties) || []).map(p => [p.name, p]))
  const forUs = (personas || [])
    .filter(p => Number(p.stance) >= 0.3)
    .sort((a, b) => Number(b.stance) - Number(a.stance))
  if (!forUs.length) return null
  const cooling = forUs.reduce((a, p) => {
    const row = priced.get(p.name)
    return a + (row && row.cools ? row.value : 0)
  }, 0)
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: "What's already on your side" }),
      cooling < 0
        ? jsx('span', { className: `${T.small} ${NUM}`, style: { color: textTone(C.for) },
            children: `takes ${Math.abs(cooling).toFixed(1)} points of heat out of the room` })
        : null,
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
      children: 'These parties pull friction out of the room. Their reason is the argument you are allowed to make — in their words, not yours.' }),
    jsx('div', { className: 'mt-1.5 grid gap-0 sm:grid-cols-2', children: forUs.map(p => {
      const row = priced.get(p.name)
      const said = (p.reasons || [])[0] || ''
      return jsxs('div', { className: 'flex flex-col gap-0.5 border-t border-(--ui-stroke-tertiary) py-1.5 first:border-t-0 first:pt-0', children: [
        jsxs('div', { className: 'flex flex-wrap items-baseline gap-1.5', children: [
          jsx('span', { className: 'inline-block size-1.5 rounded-full', style: { backgroundColor: C.for } }),
          jsx('span', { className: `${T.small} font-medium`, children: p.name }),
          jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'behind it' }),
          row && row.cools
            ? jsx('span', { className: `${T.micro} ${NUM}`, style: { color: textTone(C.for) },
                children: `${row.value.toFixed(1)} heat` })
            : null,
        ]}),
        said ? jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: said }) : null,
      ]})
    }) }),
  ]})
}

// ── who's making it hot right now ─────────────────────────────────────
// The ledger on a live room: the same arithmetic, run on the stances as they
// stand this round. Capacity is not assessed until the room closes, so the page
// says so instead of letting the number look more final than it is.
function LiveWorth({ lev }) {
  if (!lev || !lev.available) return null
  const parties = (lev.parties || []).filter(p => Math.abs(p.value) >= 0.5)
  if (!parties.length) return null
  const top = [...parties].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 3)
  const largest = Math.max(...top.map(p => Math.abs(p.value)), 1)
  const hot = parties.filter(p => !p.cools && p.value > 0)
  const heat = hot.reduce((a, p) => a + p.value, 0)
  const cools = parties.filter(p => p.cools).reduce((a, p) => a + p.value, 0)
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: "Who's making it hot right now" }),
      jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`,
        children: lev.live ? 'live estimate · capacity assumed until the room closes' : lev.method }),
    ]}),
    jsx('div', { className: 'mt-1.5 flex flex-col', children: top.map(pp => {
      const tone = pp.cools ? C.for : stanceTone(pp.stance).color
      return jsxs('div', { className: 'grid grid-cols-[minmax(0,1fr)_54px] items-center gap-2 border-b border-(--ui-stroke-tertiary) py-1 last:border-b-0', children: [
        jsxs('div', { className: 'flex min-w-0 items-center gap-1.5', children: [
          jsx('span', { className: 'inline-block size-1.5 shrink-0 rounded-full', style: { backgroundColor: tone } }),
          jsx('span', { className: `truncate ${T.small}`, children: pp.name }),
          jsx('div', {
            className: 'h-1 min-w-0 flex-1 overflow-hidden rounded-full bg-(--ui-bg-quaternary)',
            children: jsx('div', {
              className: 'h-full rounded-full',
              style: {
                width: `${Math.abs(pp.value) / largest * 100}%`,
                background: pp.cools
                  ? `repeating-linear-gradient(45deg, ${C.for}66, ${C.for}66 3px, transparent 3px, transparent 6px)`
                  : tone,
              },
            }),
          }),
        ]}),
        jsx('span', { className: `text-right ${T.small} ${NUM}`, style: { color: textTone(tone) },
          children: (pp.value > 0 ? '+' : '−') + Math.abs(pp.value).toFixed(1) }),
      ]})
    })}),
    hot.length > 0 && jsxs('div', { className: `${T.micro} leading-relaxed text-(--ui-text-tertiary) mt-1.5`, children: [
      hot.map(p => p.name).join(' and '),
      ` carry${hot.length > 1 ? '' : 's'} ${heat.toFixed(1)} of the ${lev.attributable.toFixed(1)} points above a neutral room`,
      cools ? ` — and ${Math.abs(cools).toFixed(1)} of that comes back out on the supporters' side` : '',
      '. Nothing moves until one of them does.',
    ]}),
  ]})
}

// ── when to run longer, and the standard that does the job ─────────────
// The timeline is not a "more is better" knob. Rounds confirm positions; they
// rarely create them. So the guidance names what longer actually buys and when
// it is wasted, and marks the one choice that covers most decisions.
const TIMELINE_GUIDE = {
  '30m':  { kind: 'short', best: 'an internal commit, one decision-maker, a quick "does anyone care?"' },
  '1h':   { kind: 'short', best: 'a fast no — you only want the veto read.' },
  '4h':   { kind: 'short', best: 'positions form; catches the obvious blocker.' },
  '6h':   { kind: 'short', best: 'coalitions start to show.' },
  '12h':  { kind: 'long',  best: 'counter-moves get tested across a working day.' },
  '24h':  { kind: 'standard', best: 'a full reaction cycle — first reaction, coalition forming, counter-moves tested.' },
  '48h':  { kind: 'long',  best: 'a dug-in veto player you need to watch for movement.' },
}

function TimelineHint({ window, est, suggested }) {
  const g = TIMELINE_GUIDE[window] || TIMELINE_GUIDE['24h']
  const tl = TIMELINES.find(t => t.v === window) || TIMELINES[5]
  const s = TIMELINES.find(t => t.v === (suggested && suggested.v)) || null
  const isSuggested = s && s.v === tl.v
  return jsxs('div', { className: 'flex flex-col gap-1 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-2.5 py-2', children: [
    jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: [
      `${tl.label} · ${tl.rounds} rounds · ${tl.eta} · ≈${est.calls} calls`,
    ]}),
    jsxs('div', { className: `${T.micro} ${NUM} text-(--ui-text-tertiary)`, children: [
      `≈${kTokens(est.tin)} tokens in / ≈${kTokens(est.tout)} tokens out, at about ${est.parties} parties`,
    ]}),
    isSuggested
      ? jsxs('div', { className: `${T.micro} leading-relaxed`, style: { color: BRAND.blue }, children: [
          'Suggested for this input — ', suggested.why, '.',
        ]})
      : jsxs('div', { className: `${T.micro} leading-relaxed text-(--ui-text-quaternary)`, children: [
          'Suggested for this input: ', s ? s.label : '6 hours', ' — ',
          (suggested && suggested.why) || '', '.',
        ]}),
    jsx('div', { className: `${T.micro} leading-relaxed text-(--ui-text-tertiary)`,
      children: `Best for ${g.best}.` }),
    jsx('div', { className: `${T.micro} leading-relaxed text-(--ui-text-quaternary)`,
      children: 'Go longer only when the parties are external (regulators, partners, press, competitors), the move is public, or a veto player is dug in — longer buys movement, not more objections. The room stops moving after 8–10 rounds, so past that the extra rounds mostly repeat positions.' }),
    tl.v === '48h' && jsx('div', { className: `${T.micro} leading-relaxed text-(--ui-text-quaternary)`,
      children: 'Rarely needed: 20 rounds is twice the useful depth, so the last ten rounds re-argue settled ground at double the cost.' }),
  ]})
}

// ── what each party is worth (the leverage ledger) ─────────────────────
// A party's price is a counterfactual, so it is computed from the room's own
// friction function (exact Shapley, server-side) and drawn — never asked of a
// model. The waterfall is the decomposition: it starts at the floor a room of
// undecided parties scores, adds what each hostile party costs, subtracts what
// each supporter takes back, and lands on the number the run already printed.

function waterfallRows(lev) {
  const rows = [{ key: 'base', label: 'nobody objects (the floor)', from: 0,
                  to: lev.baseline, kind: 'base' }]
  let cursor = lev.baseline
  const parties = lev.parties || []
  for (const p of parties.filter(x => !x.cools)) {
    rows.push({ key: `u${p.name}`, label: p.name, from: cursor, to: cursor + p.value,
                tone: stanceTone(p.stance).color, kind: 'up', value: p.value })
    cursor += p.value
  }
  for (const p of parties.filter(x => x.cools)) {
    rows.push({ key: `d${p.name}`, label: p.name, from: cursor, to: cursor + p.value,
                tone: C.for, kind: 'down', value: p.value })
    cursor += p.value
  }
  rows.push({ key: 'total', label: 'the room ends here', from: 0, to: lev.total, kind: 'total' })
  return rows
}

function HeatWaterfall({ lev }) {
  const rows = waterfallRows(lev)
  const W = 980
  const rowH = 30
  const top = 10
  const labelW = 320          // party names are long; 250 cut them mid-word
  const valueW = 64
  const plotW = W - labelW - valueW - 10
  const max = Math.max(...rows.map(r => Math.max(r.from, r.to))) * 1.02 || 1
  const H = top * 2 + rows.length * rowH
  const x = v => labelW + (v / max) * plotW
  const toneOf = r => r.kind === 'total' ? C.ink
    : r.kind === 'base' ? C.grey
    : r.kind === 'down' ? C.for : r.tone
  return jsxs('svg', { viewBox: `0 0 ${W} ${H}`, className: 'w-full', style: { fontFamily: 'inherit' },
    children: [
      // the line the room actually lands on
      jsx('line', { x1: x(lev.total), y1: 2, x2: x(lev.total), y2: H - 2,
        style: { stroke: C.ink, strokeWidth: 0.7, opacity: 0.28, strokeDasharray: '3 3' } }),
      ...rows.map((r, i) => {
        const cy = top + i * rowH + rowH / 2
        const x0 = x(Math.min(r.from, r.to)), x1 = x(Math.max(r.from, r.to))
        const tone = toneOf(r)
        const prev = rows[i - 1]
        const isTotal = r.kind === 'total', isBase = r.kind === 'base'
        return jsxs('g', { children: [
          // step connector: the eye has to be able to follow the running total
          i > 0 && jsx('path', {
            d: `M ${x(prev.to)} ${top + (i - 1) * rowH + rowH / 2 + 7} L ${x(prev.to)} ${cy} L ${x(r.from)} ${cy}`,
            fill: 'none', style: { stroke: '#4a5462', strokeWidth: 1.2, opacity: 0.95 },
          }),
          jsx('text', { x: labelW - 12, y: cy + 4, textAnchor: 'end', fontSize: '11.5',
            style: { fill: isTotal ? 'var(--ui-text-primary)' : 'var(--ui-text-secondary)',
                     fontFamily: 'inherit', fontWeight: isTotal ? 650 : 400 },
            children: r.label.length > 40 ? r.label.slice(0, 39) + '…' : r.label }),
          jsx('rect', { x: x0, y: cy - 8, width: Math.max(2, x1 - x0), height: 16, rx: 3,
            style: { fill: isTotal ? 'none' : tone,
                     fillOpacity: r.kind === 'down' ? 0.62 : isBase ? 0.55 : 0.92,
                     stroke: isTotal ? 'var(--ui-text-tertiary)' : 'none',
                     strokeWidth: isTotal ? 1 : 0, strokeDasharray: isTotal ? '3 2' : 'none' } }),
          r.kind === 'down' && jsx('rect', { x: x0, y: cy - 8, width: Math.max(2, x1 - x0), height: 16, rx: 3,
            style: { fill: 'none', stroke: C.for, strokeWidth: 1, strokeDasharray: '2 2', opacity: 0.75 } }),
          jsx('text', { x: W - 4, y: cy + 4, textAnchor: 'end', fontSize: '11.5',
            style: { fill: isBase ? 'var(--ui-text-quaternary)' : textTone(tone),
                     fontFamily: 'inherit', fontWeight: 650 },
            children: isBase ? r.to.toFixed(0)
              : isTotal ? (isTotal ? r.to.toFixed(1) : r.to.toFixed(1))
              : (r.value > 0 ? '+' : '−') + Math.abs(r.value).toFixed(1) }),
        ]})
      }),
    ]})
}

function HeatLedger({ lev }) {
  if (!lev || !lev.available || !(lev.parties || []).length) return null
  const ups = lev.parties.filter(p => !p.cools)
  const largest = Math.max(...ups.map(p => p.value), 1)
  const blocker = ups.filter(p => p.veto)[0]
  const cooling = lev.parties.filter(p => p.cools)
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsxs('div', { children: [
        jsx('div', { className: T.h2, children: 'What each party is worth' }),
        jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
          children: 'Computed by neutralising each party in turn and re-reading the room — not an opinion.' }),
      ]}),
      jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-tertiary)`, children: lev.method }),
    ]}),

    jsx('div', { className: 'mt-2', children: jsx(HeatWaterfall, { lev }) }),

    // the ledger proper
    jsxs('div', { className: 'mt-2 flex flex-col', children: [
      jsxs('div', { className: `grid grid-cols-[minmax(9.5rem,1.5fr)_minmax(0,1fr)_54px_74px] gap-2 border-b border-(--ui-stroke-tertiary) pb-1 ${T.label} text-(--ui-text-quaternary)`, children: [
        jsx('span', { children: 'party' }),
        jsx('span', { children: 'share of the heat' }),
        jsx('span', { className: 'text-right', children: 'points' }),
        jsx('span', { className: 'text-right', children: 'veto' }),
      ]}),
      ...lev.parties.map(pp => {
        const tone = pp.cools ? C.for : stanceTone(pp.stance).color
        const pct = Math.max(0, pp.value) / largest * 100
        return jsxs('div', { className: 'grid grid-cols-[minmax(9.5rem,1.5fr)_minmax(0,1fr)_54px_74px] items-center gap-2 border-b border-(--ui-stroke-tertiary) py-1', children: [
          jsxs('div', { className: 'flex min-w-0 items-center gap-1.5', children: [
            jsx('span', { className: 'inline-block size-1.5 shrink-0 rounded-full', style: { backgroundColor: tone } }),
            jsx('span', { className: `${T.small} leading-tight`, title: pp.name, children: pp.name }),
          ]}),
          jsx('div', { className: 'h-1.5 overflow-hidden rounded-full bg-(--ui-bg-quaternary)', children:
            jsx('div', { className: 'h-full rounded-full', style: {
              width: `${pct}%`, background: pp.cools
                ? `repeating-linear-gradient(45deg, ${C.for}66, ${C.for}66 3px, transparent 3px, transparent 6px)`
                : tone } }) }),
          jsx('div', { className: `text-right ${T.small} ${NUM}`, style: { color: textTone(tone) },
            children: (pp.value > 0 ? '+' : '−') + Math.abs(pp.value).toFixed(1) }),
          jsxs('div', { className: `text-right ${T.micro} text-(--ui-text-quaternary)`, children: [
            pp.cools ? 'cools' : pp.veto ? (pp.capacity >= 0.8 ? 'outright' : 'can slow') : '—',
          ]}),
        ]})
      }),
    ]}),

    // the read: one sentence, from the arithmetic
    blocker && jsxs('div', { className: 'mt-2 flex flex-col gap-1 rounded-lg px-3 py-2', style: {
      backgroundColor: `color-mix(in srgb, ${stanceTone(blocker.stance).color} 8%, transparent)`,
      borderLeft: `2px solid ${stanceTone(blocker.stance).color}` }, children: [
      jsx(Label, { children: 'the read' }),
      jsxs('div', { className: `${T.small} leading-relaxed`, children: [
        jsx('span', { className: 'font-semibold', children: blocker.name }),
        ` carries ${blocker.value.toFixed(0)} of the ${lev.attributable.toFixed(0)} points above a neutral room`,
        blocker.share >= 50 ? ' — more than half of everything anyone adds. ' : '. ',
        cooling.length
          ? `${cooling.map(c => c.name).join(' and ')} take${cooling.length > 1 ? '' : 's'} ${Math.abs(cooling.reduce((a, c) => a + c.value, 0)).toFixed(1)} back out.`
          : '',
      ]}),
    ]}),

    // coalitions, by what they actually do
    (lev.pairs || []).length > 0 && jsxs('div', { className: 'mt-2 flex flex-col gap-1', children: [
      jsx(Label, { children: 'together, they are one negotiation' }),
      ...lev.pairs.slice(0, 2).map(pr => jsxs('div', { className: 'flex flex-col gap-0.5', children: [
        jsxs('div', { className: `${T.small} font-medium`, children: [
          pr.a, jsx('span', { className: 'text-(--ui-text-quaternary)', children: ' + ' }), pr.b,
          jsx('span', { className: `${T.micro} text-(--ui-text-tertiary)`, children: pr.kind === 'heat'
            ? `  costs ${pr.interaction.toFixed(1)} more together`
            : '  neither one alone clears the veto' }),
        ]}),
        jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: pr.line }),
      ]})),
    ]}),

    // what each concession buys
    (lev.counterfactuals || []).length > 0 && jsxs('div', { className: 'mt-3 flex flex-col gap-1.5', children: [
      jsx(Label, { children: 'what each concession buys' }),
      jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
        children: 'The room re-read with that party’s condition met. Same parties, same claims, one thing changed.' }),
      jsx('div', { className: 'grid gap-1.5 sm:grid-cols-2 xl:grid-cols-3', children:
        lev.counterfactuals.map(cf => {
          const better = cf.friction < lev.total - 0.05
          const clears = !cf.veto_left
          const tone = clears ? C.for : better ? C.hold : 'var(--ui-text-quaternary)'
          return jsxs('div', { className: 'flex flex-col gap-1 rounded-lg border px-3 py-2.5', style: {
            borderColor: clears ? `color-mix(in srgb, ${C.for} 45%, transparent)` : 'var(--ui-stroke-tertiary)',
            backgroundColor: clears ? `color-mix(in srgb, ${C.for} 9%, transparent)` : 'var(--ui-bg-elevated)' }, children: [
            jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: ['clear ', cf.label] }),
            jsxs('div', { className: 'flex items-baseline gap-2', children: [
              jsx('span', { className: `${T.body} ${NUM} font-semibold leading-none`,
                style: { color: textTone(tone) }, children: cf.friction.toFixed(0) }),
              jsx('span', { className: `${T.small}`, style: { color: 'var(--ui-text-tertiary)' },
                children: cf.band.label }),
            ]}),
            jsx('div', { className: `${T.small}`, style: { color: clears ? textTone(C.for) : 'var(--ui-text-secondary)' },
              children: clears ? 'nobody left can stop it'
                : cf.veto_left ? `${cf.veto_left} can still stop it` : 'no veto left' }),
          ]})
        }) }),
    ]}),

    jsx('div', { className: `${T.micro} text-(--ui-text-quaternary) mt-2`,
      children: 'Points are heat, not power: a loud party with no lever costs heat and cannot stop you. The veto column is the lever.' }),
  ]})
}

// ── what each party is standing on (the provenance graph) ──────────────
// GraphRAG's actual claim, drawn: a party's position is only as good as the
// span it cites. One column of source spans, one column of parties, an edge for
// every citation — so a reader can see who is standing on the same sentence.

function citationsIn(text) {
  const out = []
  const re = /\[(decision|evidence|context)\s*¶?\s*(\d+)?\]/gi
  let m
  while ((m = re.exec(String(text)))) {
    out.push(`${m[1].toLowerCase()} ¶${m[2] || '?'}`)
  }
  return out
}

function provenance(personas) {
  const spans = []
  const parties = []
  for (const p of personas || []) {
    const reasons = p.reasons || []
    const cited = []
    for (const r of reasons) {
      for (const c of citationsIn(r)) {
        let span = spans.find(s => s.id === c)
        if (!span) {
          span = { id: c, text: String(r).replace(/\[[^\]]*\]/g, '').trim(), cites: [] }
          spans.push(span)
        }
        span.cites.push(p.name)
        cited.push(c)
      }
    }
    parties.push({ name: p.name, stance: p.stance, capacity: p.capacity, cited })
  }
  return { spans, parties: parties.filter(p => p.cited.length) }
}

function EvidenceGraph({ personas }) {
  const { spans, parties } = provenance(personas)
  if (!parties.length || !spans.length) return null
  const w = 740
  const rowH = 34
  const h = Math.max(spans.length, parties.length) * rowH + 26
  const leftX = 236, partyX = 452
  const spanY = (i) => 20 + ((i + 0.5) / spans.length) * (h - 30)
  const partyY = (i) => 20 + ((i + 0.5) / parties.length) * (h - 30)
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsx('div', { className: T.h2, children: 'What each party is standing on' }),
    jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
      children: 'Left: the lines of your own document. Right: the parties. A line means that party cites that span — two parties on one line are arguing from the same text.' }),
    jsx('svg', {
      viewBox: `0 0 ${w} ${h}`, className: 'w-full', style: { fontFamily: 'inherit' },
      children: [
        // edges first, so nodes sit on top
        ...parties.flatMap((p, pi) => p.cited.map((c, ci) => {
          const si = spans.findIndex(s => s.id === c)
          if (si < 0) return null
          const tone = stanceTone(p.stance).color
          const y1 = spanY(si), y2 = partyY(pi)
          return jsx('path', {
            key: `e${pi}-${ci}`,
            d: `M ${leftX + 8} ${y1} C ${leftX + 90} ${y1}, ${partyX - 90} ${y2}, ${partyX - 6} ${y2}`,
            fill: 'none',
            style: { stroke: tone, strokeWidth: 1.4, opacity: 0.45 },
          })
        })),
        // source spans
        ...spans.map((s, i) => {
          const tone = stanceTone((parties.find(p => s.cites.includes(p.name)) || {}).stance || 0).color
          return jsxs('g', { children: [
            jsx('text', { x: leftX, y: spanY(i) + 3.5, textAnchor: 'end', fontSize: '10.5',
              style: { fill: 'var(--ui-text-tertiary)', fontFamily: 'inherit' },
              children: s.text.length > 38 ? s.text.slice(0, 37) + '…' : s.text }),
            jsx('rect', { x: leftX + 2, y: spanY(i) - 4, width: 8, height: 8, rx: 1.5, fill: tone, opacity: 0.85 }),
          ]})
        }),
        // parties
        ...parties.map((p, i) => {
          const tone = stanceTone(p.stance).color
          const r = 3 + Math.max(0, Math.min(1, Number(p.capacity) || 0)) * 3.4
          return jsxs('g', { children: [
            jsx('circle', { cx: partyX, cy: partyY(i), r, fill: tone }),
            jsx('text', { x: partyX + 10, y: partyY(i) + 4, fontSize: '11.5', fontWeight: 600,
              style: { fill: 'var(--ui-text-secondary)', fontFamily: 'inherit' },
              children: p.name.length > 24 ? p.name.slice(0, 23) + '…' : p.name }),
            jsx('text', { x: w - 4, y: partyY(i) + 4, fontSize: '10', textAnchor: 'end',
              style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' },
              children: stanceTone(p.stance).word }),
          ]})
        }),
        jsx('text', { x: leftX + 2, y: 10, fontSize: '9.5',
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' },
          children: 'cited spans' }),
        jsx('text', { x: partyX, y: 10, fontSize: '9.5',
          style: { fill: 'var(--ui-text-quaternary)', fontFamily: 'inherit' },
          children: 'parties' }),
      ],
    }),
  ]})
}

// ── the transcript ────────────────────────────────────────────────────
// CAMEL's actual lesson: the conversation is the artifact. A stakeholder who
// speaks in their own voice is a person you can plan against; a status line is
// not. These are the run's own frozen statements, grouped by round.

function QuoteLine({ e, tone }) {
  const isGod = e.actor === '<god>'
  const verbTone = ACTION_TONE[e.action]
  return jsxs('div', { className: 'flex gap-2.5 py-1.5', children: [
    jsxs('div', { className: 'flex w-[8.5rem] shrink-0 flex-col', children: [
      jsx('span', { className: `truncate ${T.micro} font-semibold`, title: e.actor,
        style: isGod ? { color: C.for } : undefined,
        children: isGod ? 'You' : e.actor }),
      jsx('span', { className: `${T.micro}`, style: { color: verbTone || 'var(--ui-text-quaternary)' },
        children: ACTION_WORD[e.action] || e.action }),
    ]}),
    jsxs('div', { className: 'flex flex-1 flex-col gap-0.5', children: [
      jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: e.text || '—' }),
    ]}),
  ]})
}

function Transcript({ events, rounds, openRound }) {
  const list = (events || []).filter(e => e && (e.text || '').trim())
  const byRound = {}
  list.forEach(e => { const r = e.round || 0; (byRound[r] = byRound[r] || []).push(e) })
  const roundKeys = Object.keys(byRound).map(Number).sort((a, b) => b - a)
  const [sel, setSel] = React.useState(openRound != null ? openRound : (roundKeys[0] || 0))
  if (!list.length) return null
  const shown = byRound[sel] || byRound[roundKeys[0]] || []
  const tone = {}
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex items-baseline justify-between gap-3', children: [
      jsx('div', { className: T.h2, children: 'What they actually said' }),
      jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
        children: `${list.length} statements across ${roundKeys.length} rounds` }),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
      children: 'Every line below was written during the run and frozen with the claims. Pick a round to see the room at that point.' }),
    jsxs('div', { className: 'flex flex-wrap gap-1.5', children: roundKeys.slice().sort((a, b) => a - b).map(r =>
      jsx(Button, {
        key: `tr${r}`, size: 'xs', variant: r === sel ? 'secondary' : 'outline',
        onClick: () => { haptic('tap'); setSel(r) },
        children: `Round ${r}`,
      })
    )}),
    jsxs('div', { className: 'flex flex-col divide-y divide-(--ui-stroke-tertiary)' , children:
      shown.map((e, i) => jsx(QuoteLine, { key: `q${i}`, e, tone })) }),
  ]})
}

const ACTION_TONE = {
  blocks: C.against, supports: C.for, shares: C.hold,
  waits: C.hold, intervention: C.for,
}

// The two voices that decide the room, quoted. A stance word without the
// sentence behind it is back to being a number nobody can argue with.
function LoudestLine({ who, kind }) {
  if (!who) return null
  const tone = kind === 'for' ? C.for : C.against
  return jsxs('div', {
    className: 'flex flex-col gap-0.5 rounded-md px-2 py-1.5',
    style: { backgroundColor: `color-mix(in srgb, ${tone} 7%, transparent)`, borderLeft: `2px solid ${tone}` },
    children: [
      jsxs('div', { className: 'flex items-baseline gap-1.5', children: [
        jsx('span', { className: `${T.label}`, style: { color: tone },
          children: kind === 'for' ? 'loudest for it' : 'loudest against it' }),
        jsx('span', { className: `${T.micro} font-semibold`, children: who.name }),
        jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-quaternary)`, children: signed(who.stance) }),
      ]}),
      jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: who.said || '—' }),
    ],
  })
}

// ── live: the floor ───────────────────────────────────────────────────

// The first round takes real time — one model call to read the input and one per
// party. Sitting on "Round 0 of 5" for a minute reads as a hang, so the screen
// says what the machine is actually doing and moves while it does it. The shimmer
// is SMIL inside the SVG the plugin already draws: no injected stylesheet, no
// animation framework, and it stops when the element unmounts.
const STAGES = [
  [0,   'Reading what you gave it'],
  [8,   'Naming the parties who will react'],
  [20,  'Working out who can stop it'],
  [35,  'Opening the arena — round 1'],
  [60,  'Still going — a long input takes longer to read'],
]

function WorkingBar({ startedAt, round, label }) {
  const [now, setNow] = React.useState(Date.now())
  React.useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(t)
  }, [])
  const secs = startedAt ? Math.max(0, Math.round((now - startedAt) / 1000)) : 0
  const stage = [...STAGES].reverse().find(([at]) => secs >= at) || STAGES[0]
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsxs('svg', { viewBox: '0 0 600 8', className: 'w-full', preserveAspectRatio: 'none',
      style: { height: 8 }, children: [
      jsx('rect', { x: 0, y: 0, width: 600, height: 8, rx: 4,
        style: { fill: 'var(--ui-bg-quaternary)' } }),
      jsx('rect', { y: 0, width: 90, height: 8, rx: 4,
        style: { fill: C.for, opacity: 0.85 }, children:
        jsx('animate', { attributeName: 'x', values: '-90;600', dur: '1.7s',
          repeatCount: 'indefinite' }) }),
    ]}),
    jsxs('div', { className: `flex flex-wrap items-baseline justify-between gap-2 ${T.micro}`, children: [
      jsx('span', { style: { color: textTone(C.for) },
        children: label || `${stage[1]}…` }),
      jsx('span', { className: `${NUM} text-(--ui-text-quaternary)`,
        children: `${secs}s · round ${round || 0} is the slow one` }),
    ]}),
  ]})
}

function LiveFloor({ events }) {
  const list = (events || []).filter(e => e && (e.text || '').trim())
  if (!list.length) {
    return jsxs('div', { className: 'flex flex-col gap-1.5', children: [
      jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
        children: 'The first statements land as soon as the room has read everything. Nothing is invented while you wait — the parties are being named from your text.' }),
    ]})
  }
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsx(Label, { children: 'on the floor' }),
    jsxs('div', { className: 'flex flex-col gap-2', children: list.map((e, i) => {
      const isGod = e.actor === '<god>'
      return jsxs('div', { className: 'flex gap-2.5', children: [
        jsx('span', { className: 'mt-1.5 inline-block size-1.5 shrink-0 rounded-full',
          style: { backgroundColor: isGod ? C.for : 'var(--ui-accent)' } }),
        jsxs('div', { className: 'flex flex-1 flex-col', children: [
          jsxs('div', { className: 'flex items-baseline gap-1.5', children: [
            jsx('span', { className: `${T.micro} font-semibold`, style: isGod ? { color: C.for } : undefined,
              children: isGod ? 'You' : e.actor }),
            jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: ACTION_WORD[e.action] || e.action }),
          ]}),
          jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: e.text || '—' }),
        ]}),
      ]})
    }) }),
  ]})
}

function RoundTrack({ round, total }) {
  const n = Math.max(1, Number(total) || 1)
  const r = Math.max(0, Number(round) || 0)
  return jsxs('div', { className: 'flex items-center gap-2', children: [
    jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-quaternary)`, children: 'round 1' }),
    jsx('div', { className: 'flex flex-1 items-center gap-[3px]', children: [
      ...Array.from({ length: n }).map((_, i) => jsx('div', {
        key: `rt${i}`,
        className: 'h-2 flex-1 rounded-full',
        style: {
          backgroundColor: i < r ? 'var(--ui-accent)' : 'var(--ui-bg-quaternary)',
          opacity: i < r ? (i === r - 1 ? 1 : 0.55) : 1,
        },
      })),
    ]}),
    jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-quaternary)`, children: `round ${n}` }),
  ]})
}

// ── scorecard ─────────────────────────────────────────────────────────
// The claims are the product's honesty: written down before the outcome is known,
// scored afterwards. The record is the reason to come back.

function ClaimRow({ c, hit, onHit, disabled }) {
  return jsxs('div', { className: 'flex items-start gap-2 border-t border-(--ui-stroke-tertiary) py-2 first:border-t-0', children: [
    jsxs('div', { className: 'flex flex-1 flex-col gap-0.5', children: [
      jsx('div', { className: `${T.small}`, children: c.claim }),
      c.source ? jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: `from: ${c.source}` }) : null,
    ]}),
    jsxs('div', { className: 'flex shrink-0 items-center gap-1', children: [
      jsx(Button, {
        size: 'xs', variant: hit === true ? 'secondary' : 'outline', disabled,
        className: 'w-7', onClick: () => onHit(c.id, true), title: 'This call held',
        children: '✓',
      }),
      jsx(Button, {
        size: 'xs', variant: hit === false ? 'destructive' : 'outline', disabled,
        className: 'w-7', onClick: () => onHit(c.id, false), title: 'This call was wrong',
        children: '✗',
      }),
    ]}),
  ]})
}

function Scorecard({ result, claimHits, setClaimHits, onVerify, record, due }) {
  const claims = result.claims || []
  const dueDate = result.createdAt ? dueAt({ created_at: result.createdAt, window: result.window }) : ''
  const isDue = dueDate ? Date.parse(dueDate) <= Date.now() : false
  const scored = result.verified && result.verified.verdict
  return jsxs(Card, { tone: C.for, children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: 'The call, frozen' }),
      jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
        dueDate ? (isDue ? 'window closed — score it now' : `score it in ${until(dueDate)}`) : '',
      ]}),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-secondary)`,
      children: scored
        ? `You scored this run "${scored}". That is the whole point: a call you can audit, not a horoscope.`
        : 'These were written at the moment the run finished, before anyone knew the answer. When the window closes, mark each one. That is how this becomes a track record instead of an opinion.' }),

    jsxs('div', { className: 'flex flex-col', children: claims.map(c =>
      jsx(ClaimRow, { key: c.id, c, hit: claimHits[c.id], disabled: !!scored,
        onHit: (id, v) => { haptic('tap'); setClaimHits({ ...claimHits, [id]: v }) } })
    )}),

    scored ? null : jsxs('div', { className: 'flex flex-wrap items-center gap-2 pt-0.5', children: [
      jsx('span', { className: `${T.micro} text-(--ui-text-tertiary)`, children: 'overall:' }),
      ...['right', 'partial', 'wrong'].map(v => jsx(Button, {
        key: v, size: 'xs', variant: 'outline', onClick: () => onVerify(v),
        children: v === 'right' ? 'it held' : v === 'partial' ? 'partly' : 'it broke',
      })),
    ]}),

    record && record.verified > 0 ? jsxs('div', {
      className: 'mt-1 grid grid-cols-3 gap-3 border-t border-(--ui-stroke-tertiary) pt-2.5',
      children: [
        jsxs('div', { children: [
          jsx('div', { className: `${T.display} ${NUM}`, children: String(record.runs) }),
          jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: 'reviews run' }),
        ]}),
        jsxs('div', { children: [
          jsx('div', { className: `${T.display} ${NUM}`, children: String(record.verified) }),
          jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: 'scored' }),
        ]}),
        jsxs('div', { children: [
          jsx('div', { className: `${T.display} ${NUM}`,
            children: record.claim_hit_rate == null ? '—' : `${Math.round(record.claim_hit_rate * 100)}%` }),
          jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`,
            children: record.verified < 10 ? 'hit rate (n<10 — thin)' : 'hit rate' }),
        ]}),
      ],
    }) : null,

    due && due.length
      ? jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
          children: `${due.length} other ${due.length === 1 ? 'review is' : 'reviews are'} past their window and unscored — they are waiting at the bottom of this page.` })
      : null,
  ]})
}

// ── the verdict ───────────────────────────────────────────────────────

// "Go talk to Legal" is not an instruction. Their condition names the artifact
// that ends the objection; this maps the words they used onto what to carry into
// the room. Derived, never invented — the condition itself is shown verbatim.
function unblockArtifact(condition) {
  const t = String(condition || '').toLowerCase()
  if (!t) return ''
  if (/licen[cs]e|licen[cs]ing|\bip\b|compliance|regulat|gdpr|data protection/.test(t))
    return 'the signed paper: the licence or clearance they named, in writing — not a promise to obtain it'
  if (/budget|cost|spend|margin|revenue|cannibal/.test(t))
    return 'a capped number, agreed in writing, with whoever owns the budget'
  if (/clause|terms|contract|protection|indemn/.test(t))
    return 'the drafted clause itself — a term they can redline, not a description of one'
  if (/survey|evidence|eval|benchmark|data/.test(t))
    return 'the underlying data behind the claim, so they can check it themselves'
  if (/support|migration|reseller/.test(t))
    return 'a named owner and a date for the gap they described'
  return 'the specific thing their condition names, in writing, before you ask again'
}

// The blocker's own condition, in their words — the same sentence the verdict
// panel prints, so the condensed view cannot tell a different story.
function conditionLine(result) {
  const blocker = (result.personas || []).find(p => p.name === result.blocker)
  return blocker && blocker.reasons && blocker.reasons[0] ? blocker.reasons[0] : ''
}

function verdictHeadline(result) {
  const blocker = result.blocker
  const band = frictionBand(result.friction)
  if (!blocker) {
    return 'Nothing in this room can stop it — so the real risk is that nobody cares.'
  }
  if (band.name === 'A brawl') return `${blocker} can stop this, and they are dug in. Do not launch on this read.`
  if (band.name === 'A fight') return `This lands only after ${blocker} moves — they can stop it and they are not convinced.`
  if (band.name === 'Winnable ground') return `This is winnable: ${blocker} objects, but one good move turns them.`
  return `${blocker} is the one to watch — everyone else is already with you.`
}

function VerdictPanel({ result }) {
  const blocker = result.personas?.find(p => p.name === result.blocker) || null
  const band = frictionBand(result.friction)
  const sea = result.sea
  const seaDef = sea && sea.state ? SEA[sea.state] : null
  const condition = blocker && blocker.reasons && blocker.reasons[0]
  const move = (result.counterMoves && result.counterMoves[0]) || result.recommendation || ''

  return jsxs('div', {
    className: 'flex flex-col gap-3 rounded-xl border border-(--ui-stroke-tertiary) p-5',
    style: {
      background: `linear-gradient(160deg, color-mix(in srgb, ${band.color} 9%, var(--ui-bg-elevated)) 0%, var(--ui-bg-elevated) 62%)`,
    },
    children: [
      jsxs('div', { className: 'flex flex-wrap items-center gap-2', children: [
        jsx(Label, { children: 'the call' }),
        jsx('span', { className: `rounded-full px-2 py-0.5 ${T.micro} font-medium`,
          style: { backgroundColor: `color-mix(in srgb, ${band.color} 16%, transparent)`, color: band.color },
          children: band.name }),
        seaDef ? jsxs('span', { className: `flex items-center gap-1.5 ${T.micro} text-(--ui-text-tertiary)`, children: [
          jsx('span', { className: 'inline-block size-1.5 rounded-full', style: { backgroundColor: seaDef.color } }),
          seaDef.label + ' · ' + seaDef.meaning,
        ]}) : null,
        // an off-axis read is the absence of a read, not an unlit axis — say why
        sea && !seaDef && jsxs('span', { className: `flex items-center gap-1.5 ${T.micro} text-(--ui-text-tertiary)`, children: [
          jsx('span', { className: 'inline-block size-1.5 rounded-full border border-dashed border-(--ui-text-tertiary)' }),
          `competition read: ${sea.label || 'insufficient input'}${sea.why ? ' — ' + sea.why : ''}`,
        ]}),
      ]}),

      jsx('h2', { className: `${T.display} max-w-[46rem]`, children: verdictHeadline(result) }),

      jsxs('div', { className: 'grid gap-4 md:grid-cols-3', children: [
        jsxs('div', { className: 'flex flex-col gap-1', children: [
          jsx(Label, { children: 'who can stop it' }),
          jsx('div', { className: `${T.h1}`, children: blocker ? blocker.name : 'nobody found' }),
          jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`,
            children: blocker ? powerWord(blocker.capacity) : (sea && sea.why) || 'no party with blocking power was found' }),
        ]}),
        jsxs('div', { className: 'flex flex-col gap-1', children: [
          jsx(Label, { children: 'what they need' }),
          jsx('div', { className: `${T.body} text-(--ui-text-secondary)`,
            children: condition || 'No specific condition was grounded in your documents.' }),
        ]}),
        jsxs('div', { className: 'flex flex-col gap-1', children: [
          jsx(Label, { children: 'your best move' }),
          jsx('div', { className: `${T.body} text-(--ui-text-secondary)`,
            children: move || 'No counter-move survived this run.' }),
        ]}),
      ]}),

      // the two voices that decided it, and what ends the objection
      blocker && condition ? jsxs('div', {
        className: 'flex flex-col gap-1 rounded-lg px-3 py-2.5',
        style: { backgroundColor: `color-mix(in srgb, ${C.against} 6%, transparent)`,
                 borderLeft: `2px solid ${C.against}` },
        children: [
          jsx(Label, { children: 'what ends this objection' }),
          jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: condition }),
          jsxs('div', { className: `${T.small}`, children: [
            jsx('span', { className: 'font-semibold', children: 'Bring: ' }),
            jsx('span', { className: 'text-(--ui-text-secondary)', children: unblockArtifact(condition) }),
          ]}),
          move ? jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
            jsx('span', { className: 'font-semibold', children: 'Then: ' }), move,
          ]}) : null,
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
            children: 'Read off the words in their condition — the run does not add facts you did not give it.' }),
        ],
      }) : null,

      jsxs('div', { className: 'flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-(--ui-stroke-tertiary) pt-3', children: [
        jsx(FrictionGauge, { friction: result.friction }),
        jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`,
          children: 'how hard the room pushes back · 0 quiet · 50 contested · 100 open war' }),
      ]}),
      jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: band.why }),
    ],
  })
}

// ── home ──────────────────────────────────────────────────────────────

function Step({ n, title, body }) {
  return jsxs('div', { className: 'flex gap-2.5', children: [
    jsx('div', {
      className: 'flex size-5 shrink-0 items-center justify-center rounded-full text-[0.625rem] font-semibold',
      style: { backgroundColor: 'color-mix(in srgb, var(--ui-accent) 16%, transparent)', color: 'var(--ui-accent)' },
      children: String(n),
    }),
    jsxs('div', { className: 'flex flex-col gap-0.5', children: [
      jsx('div', { className: `${T.small} font-medium`, children: title }),
      jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: body }),
    ]}),
  ]})
}

function GetTile({ title, body }) {
  return jsxs('div', {
    className: 'flex flex-col gap-1 rounded-lg border border-(--ui-stroke-tertiary) p-3',
    style: { backgroundColor: 'color-mix(in srgb, var(--ui-bg-elevated) 60%, transparent)' },
    children: [
      jsx('div', { className: `${T.small} font-semibold`, children: title }),
      jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: body }),
    ],
  })
}

function Hero({ onStart }) {
  return jsxs('div', {
    className: 'flex flex-col gap-4 rounded-xl border border-(--ui-stroke-tertiary) px-5 py-5',
    style: {
      background: `radial-gradient(120% 140% at 0% 0%, color-mix(in srgb, var(--ui-accent) 12%, transparent) 0%, transparent 58%), var(--ui-bg-elevated)`,
    },
    children: [
      jsxs('div', { className: 'flex flex-col gap-1.5', children: [
        jsx('h1', { className: T.display, children: TAGLINE }),
        jsx('p', { className: `${T.body} text-(--ui-text-secondary)`,
          children: `Add what you want evaluated — a repo README, a paper, a blog link, a launch post, a case study, an announcement. ${PRODUCT_NAME} opens a stage: the parties who will actually react, drawn from the text and links you give it, arguing for as few as three rounds or as many as you ask. Yours or someone else's — what comes back is what it means, who is for it and who can stop it, how contested the ground already is, and what each concession buys.` }),
        jsx('p', { className: `${T.small} text-(--ui-text-tertiary)`,
          children: 'Every party, every condition and every quote comes from what you gave it — nothing is invented. It is a test, not a forecast: the claims are frozen with dates and scored later, so the record argues for itself.' }),
      ]}),
      jsxs('div', { className: 'flex flex-wrap items-center gap-2', children: [
        jsx(PrimaryAction, { onClick: onStart, className: 'h-9 px-3.5 text-[0.875rem]', children: 'Start arena session' }),
        jsx('span', { className: `${T.micro} text-(--ui-text-tertiary)`,
          children: 'Three rounds takes about two minutes on a free model — a cheap way to find out whether anyone cares.' }),
      ]}),
      jsxs('div', { className: 'grid gap-4 border-t border-(--ui-stroke-tertiary) pt-4 md:grid-cols-3', children: [
        jsx(Step, { n: 1, title: 'Add the details',
          body: 'A repo README, a blog link, a launch post, a whitepaper, a case study, a press release, a tweet. One link is enough; more gives the room more to stand on.' }),
        jsx(Step, { n: 2, title: 'The arena opens',
          body: 'The parties who will actually react take their seats and argue — three rounds, or as many as you ask. You can inject a counter-move mid-run and watch the board bend.' }),
        jsx(Step, { n: 3, title: 'Read the result',
          body: 'What it means, who is for it, who can stop it, what each concession buys — and the claims frozen so you can score them.' }),
      ]}),
    ],
  })
}

function WhatYouGet() {
  return jsxs('div', { className: 'flex flex-col gap-2', children: [
    jsx(Label, { children: 'what comes back' }),
    jsxs('div', { className: 'grid gap-2 sm:grid-cols-2 lg:grid-cols-3', children: [
      jsx(GetTile, { title: 'What it means', body: 'The request read plainly: what is actually being claimed, who it displaces, and the opening it creates for you.' }),
      jsx(GetTile, { title: 'The room', body: 'Who actually reacts: customers, competitors, partners, and the marketplace that would list you — named, drawing on your own text.' }),
      jsx(GetTile, { title: 'Who decides', body: 'The parties with real power over the outcome — the ones who can veto it, the ones who can amplify it, and the ones who can only complain.' }),
      jsx(GetTile, { title: 'The field', body: 'How contested the ground already is, and whether you will be read as a new category, another entrant, or noise.' }),
      jsx(GetTile, { title: 'The price', body: 'What each concession buys, computed from the room: settle Finance and Legal and the call goes from a fight to quiet ground.' }),
      jsx(GetTile, { title: 'The record', body: 'Claims frozen at run time, scored when the window closes. That is our record, not our opinion.' }),
    ]}),
    jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
      children: 'Not a forecast and not a guarantee. A dry run finds the fight before you are in it, and writes down its calls so you can grade them.' }),
  ]})
}

// A run is one line. The room is drawn small — position as a dot on a line,
// power as the dot's size — so the row carries a picture without a second row
// of chrome. Twelve runs then take a third of the space three cards used to.
function MiniRoom({ personas, width = 78, height = 16 }) {
  const list = (personas || []).filter(p => p && p.stance != null)
  if (!list.length) return jsx('span', { className: 'inline-block', style: { width: `${width}px` } })
  const x = (s) => 4 + ((Math.max(-1, Math.min(1, Number(s) || 0)) + 1) / 2) * (width - 8)
  return jsxs('svg', {
    width, height, viewBox: `0 0 ${width} ${height}`, 'aria-hidden': 'true',
    className: 'shrink-0',
    children: [
      jsx('line', { x1: 4, y1: height / 2, x2: width - 4, y2: height / 2,
        style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1 } }),
      jsx('line', { x1: width / 2, y1: 3, x2: width / 2, y2: height - 3,
        style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1, strokeDasharray: '1.5 2' } }),
      ...list.map((p, i) => jsx('circle', {
        key: `m${i}`,
        cx: x(p.stance), cy: height / 2,
        r: 1.8 + Math.max(0, Math.min(1, Number(p.capacity) || 0)) * 2.2,
        fill: stanceTone(p.stance).color, opacity: 0.95,
      })),
    ],
  })
}

function RunLine({ h, onOpen }) {
  const band = frictionBand(h.friction)
  const due = h.window && h.created_at ? Date.parse(dueAt(h)) <= Date.now() && !(h.verified && h.verified.verdict) : false
  return jsxs('button', {
    type: 'button',
    className: 'flex w-full items-center gap-2.5 border-t border-(--ui-stroke-tertiary) px-1.5 py-2 text-left transition-colors first:border-t-0 hover:bg-(--ui-bg-elevated)',
    onClick: () => onOpen(h.run_id, h.title),
    children: [
      jsx('span', { className: 'inline-block size-1.5 shrink-0 rounded-full',
        style: { backgroundColor: band.color } }),
      jsx('span', { className: `min-w-0 flex-1 truncate ${T.small} font-medium`, children: h.title }),
      jsx(MiniRoom, { personas: h.personas }),
      jsx('span', { className: `hidden w-[5.5rem] shrink-0 md:inline ${T.micro}`, style: { color: band.color },
        children: band.name }),
      jsx('span', { className: `hidden w-[9rem] shrink-0 truncate md:inline ${T.micro} text-(--ui-text-tertiary)`, title: h.blocker || '',
        children: h.blocker ? `${h.blocker} can stop it` : 'no single blocker' }),
      jsx('span', { className: `w-[3.5rem] shrink-0 text-right ${T.micro} ${NUM} text-(--ui-text-quaternary)`,
        children: h.friction != null ? `${Number(h.friction).toFixed(0)}` : '—' }),
      jsx('span', { className: `w-[4.5rem] shrink-0 text-right ${T.micro}`,
        style: due ? { color: C.for } : undefined,
        children: h.verified && h.verified.verdict ? h.verified.verdict : (due ? 'to score' : '') }),
      jsx('span', { className: `w-[3.5rem] shrink-0 text-right ${T.micro} text-(--ui-text-quaternary)`, children: ago(h.created_at) }),
      jsx(Codicon, { name: 'chevron-right', size: '0.75rem', className: 'shrink-0 text-(--ui-text-quaternary)' }),
    ],
  })
}

function RunTableHead() {
  return jsxs('div', { className: `flex items-center gap-2.5 px-1.5 pb-1 ${T.label} text-(--ui-text-quaternary)`, children: [
    jsx('span', { className: 'size-1.5 shrink-0' }),
    jsx('span', { className: 'min-w-0 flex-1', children: 'review' }),
    jsx('span', { className: 'w-[78px] shrink-0', children: 'room' }),
    jsx('span', { className: 'hidden w-[5.5rem] shrink-0 md:inline', children: 'verdict' }),
    jsx('span', { className: 'hidden w-[9rem] shrink-0 md:inline', children: 'blocker' }),
    jsx('span', { className: 'w-[3.5rem] shrink-0 text-right', children: 'heat' }),
    jsx('span', { className: 'w-[4.5rem] shrink-0 text-right', children: 'scored' }),
    jsx('span', { className: 'w-[3.5rem] shrink-0 text-right', children: 'when' }),
    jsx('span', { className: 'w-3 shrink-0' }),
  ]})
}

// ── "this window is behind" ───────────────────────────────────────────
// A page reload cannot fix a stale window: the app reads its UI file from the
// machine the window runs on, and this process is not that machine. So the card
// offers the two things that do work, and says plainly that neither restarts
// the app.

function UpdateCard({ uiBuild, onOpenPlugins }) {
  return jsxs(Card, { tone: C.hold, children: [
    jsxs('div', { className: 'flex flex-wrap items-center gap-2', children: [
      jsx(Label, { children: 'this window is behind' }),
      jsx(Badge, { variant: 'outline',
        children: `window ${uiBuild.running || 'unknown'} → installed ${uiBuild.installed || 'unknown'}` }),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-secondary)`,
      children: 'The app reads its UI file from the machine it runs on, so reloading this page cannot pick up a new build — and you do not need to restart the app.' }),
    jsxs('div', { className: 'flex flex-wrap items-center gap-2', children: [
      jsx(Button, { onClick: onOpenPlugins, children: 'Open plugin settings' }),
    ]}),
    // This plugin does not update itself: the trust model is the pinned commit,
    // so the update has to be the app's or the user's, never ours.
    jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
      jsx('strong', { children: 'In the app: ' }),
      'Capabilities → Plugins → Install from Git → trillionverselabs-boop/strategic-arena → tick Desktop → Install. The app copies the file and reloads it.',
    ]}),
    jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
      jsx('strong', { children: 'Or drop the file in yourself: ' }),
      'replace `%USERPROFILE%\\.hermes\\desktop-plugins\\strategic-arena\\plugin.js`. The app watches that file and reloads the page in place.',
    ]}),
  ]})
}


// ── the demo path ─────────────────────────────────────────────────────
// A judge has about sixty seconds. The first thing they should be able to do is
// read a finished, scored session — not fill in a form. One click from cold start
// to: what it meant, the call, who paid for it, and the claim that was graded.
// Everything here is real run data; nothing is staged for the demo.

function demoPick(history) {
  const done = (history || []).filter(h => h && h.friction != null)
  if (!done.length) return null
  // a scored session first — the whole point is that this thing can be wrong
  return done.find(h => h.verified && h.verified.verdict) || done[0]
}

function DemoCard({ best, onOpen }) {
  if (!best) return null
  const scored = best.verified && best.verified.verdict
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex flex-wrap items-center justify-between gap-3', children: [
      jsxs('div', { className: 'flex flex-col gap-1', children: [
        jsx(Label, { children: 'start here — a finished session' }),
        jsx('div', { className: T.h2, children: best.title }),
        jsxs('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: [
          `${best.personas ? best.personas.length : 0} parties`,
          ` · heat ${Number(best.friction).toFixed(0)}`,
          best.blocker ? ` · ${best.blocker} can stop it` : ' · no single blocker',
          scored ? ` · scored “${scored}”` : ' · awaiting its window',
        ]}),
      ]}),
      jsx(PrimaryAction, { onClick: () => { haptic('tap'); onOpen(best.run_id, best.title) },
        children: 'See the finished review' }),
    ]}),
    jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children:
      'The real thing, on real text: what it means, the call, what each party is worth, and the claims frozen before anyone knew the answer. Esc to come back.' }),
  ]})
}

// The condensed read: one screen, no scrolling required. The full session is one
// click away for anyone who wants the waterfall and the transcript.
function DemoReview({ result, onFull, onStart, onBack, record }) {
  const claims = (result.claims || []).slice(0, 4)
  const lev = result.leverage && result.leverage.available ? result.leverage : null
  const top = lev ? lev.parties.filter(p => p.value > 0.5).slice(0, 3) : []
  const band = frictionBand(result.friction)
  const scored = result.verified && result.verified.verdict
  return jsxs('div', { className: 'flex flex-col gap-3', children: [
    jsxs('div', { className: 'flex flex-wrap items-center justify-between gap-2', children: [
      jsxs('div', { className: 'flex flex-col gap-0.5', children: [
        jsx(Label, { children: 'a finished session' }),
        jsx('div', { className: T.h1, children: result.title }),
      ]}),
      jsxs('div', { className: 'flex items-center gap-1.5', children: [
        jsx(Button, { variant: 'ghost', size: 'xs', onClick: onBack, children: '← back' }),
        jsx(Button, { variant: 'ghost', size: 'xs', onClick: onFull, children: 'the full session' }),
        jsx(PrimaryAction, { onClick: onStart, children: 'Start arena session' }),
      ]}),
    ]}),

    // 1. what it means
    result.read && result.read.claim && jsxs('div', { className: 'rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-4 py-3', children: [
      jsx(Label, { children: 'what it means' }),
      jsx('div', { className: `${T.body} mt-1`, children: result.read.claim }),
      result.read.opening ? jsxs('div', { className: `${T.small} text-(--ui-text-tertiary) mt-1`, children: [
        jsx('span', { className: 'font-semibold', children: 'The opening: ' }), result.read.opening,
      ]}) : null,
    ]}),

    // 2. the call
    jsxs('div', { className: 'rounded-xl border border-(--ui-stroke-tertiary) px-4 py-3', style: {
      borderLeft: `3px solid ${band.color}` }, children: [
      jsxs('div', { className: 'flex flex-wrap items-baseline gap-2', children: [
        jsx('span', { className: `${T.micro} font-semibold`, style: { color: textTone(band.color) },
          children: `${band.name} · ${Number(result.friction).toFixed(0)}/100` }),
        result.sea ? jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: result.sea.label }) : null,
      ]}),
      jsx('div', { className: `${T.h1} mt-1`, style: { fontSize: '1.125rem' }, children: verdictHeadline(result) }),
      jsxs('div', { className: 'mt-2 grid gap-2 md:grid-cols-3', children: [
        jsxs('div', { children: [
          jsx('div', { className: T.label + ' text-(--ui-text-quaternary)', children: 'who can stop it' }),
          jsx('div', { className: T.small, children: result.blocker || 'nobody with standing' }),
        ]}),
        jsxs('div', { children: [
          jsx('div', { className: T.label + ' text-(--ui-text-quaternary)', children: 'what they need' }),
          jsx('div', { className: T.small, children: conditionLine(result) || '—' }),
        ]}),
        jsxs('div', { children: [
          jsx('div', { className: T.label + ' text-(--ui-text-quaternary)', children: 'your best move' }),
          jsx('div', { className: T.small, children: (result.counterMoves || [])[0] || '—' }),
        ]}),
      ]}),
    ]}),

    // 3. who paid for it
    top.length > 0 && jsxs('div', { className: 'rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-4 py-3', children: [
      jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
        jsx(Label, { children: 'what each party is worth' }),
        jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-quaternary)`, children: lev.method }),
      ]}),
      jsx('div', { className: 'mt-1 grid gap-1 sm:grid-cols-3', children: top.map(pp => jsxs('div', {
        className: 'flex items-baseline gap-1.5', children: [
          jsx('span', { className: 'inline-block size-1.5 rounded-full', style: { backgroundColor: stanceTone(pp.stance).color } }),
          jsx('span', { className: `${T.small} truncate`, children: pp.name }),
          jsx('span', { className: `${T.small} ${NUM} font-semibold`, style: { color: textTone(stanceTone(pp.stance).color) },
            children: `+${pp.value.toFixed(1)}` }),
          pp.veto ? jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'veto' }) : null,
        ]}) ) }),
    ]}),

    // 4. the graded claim — the part nobody else ships
    claims.length > 0 && jsxs('div', { className: 'rounded-xl border px-4 py-3', style: {
      borderColor: scored ? `color-mix(in srgb, ${C.for} 40%, transparent)` : 'var(--ui-stroke-tertiary)',
      background: scored ? `color-mix(in srgb, ${C.for} 7%, transparent)` : 'transparent' }, children: [
      jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
        jsx(Label, { children: 'frozen before the answer was known' }),
        scored
          ? jsx('span', { className: `${T.small} font-semibold`, style: { color: textTone(C.for) },
              children: `graded “${scored}”` })
          : jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: dueAt({ created_at: result.createdAt, window: result.window }) ? `scored ${until(dueAt({ created_at: result.createdAt, window: result.window }))}` : 'opens later' }),
      ]}),
      jsx('div', { className: 'mt-1 flex flex-col', children: claims.map(c => jsxs('div', {
        className: 'flex items-baseline gap-2 border-t border-(--ui-stroke-tertiary) py-1 first:border-t-0 first:pt-0',
        children: [
          jsx('span', { className: `${T.small} flex-1`, children: c.claim }),
          c.probability != null ? jsx('span', { className: `${T.micro} ${NUM} text-(--ui-text-tertiary)`, children: `${Math.round(c.probability * 100)}%` }) : null,
        ]}) ) }),
      jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary) mt-1`, children: [
        'That is the claim we were willing to be marked on. A session you can grade beats a report you have to trust.',
        record && record.hit_rate != null ? ` Track record: ${record.hit_rate}% on ${record.scored || 0} scored sessions.` : '',
      ]}),
    ]}),
  ]})
}

// ── new review dialog ─────────────────────────────────────────────────

function NewReviewModal({ ctx, onClose, onStarted }) {
  const [title, setTitle] = React.useState('')
  const [decision, setDecision] = React.useState('')
  const [evidence, setEvidence] = React.useState('')
  const [urls, setUrls] = React.useState('')
  const [window, setWindow] = React.useState('24h')
  const [kind, setKind] = React.useState('auto')
  const [goal, setGoal] = React.useState('adoption')
  const [showGuide, setShowGuide] = React.useState(false)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState('')

  // The model is the session's, read from the app's own state. Not a copy, not a
  // catalogue we fetch over the network, not a host permission we ask for — a
  // picker here could only ever be wrong about a decision Hermes already made.
  const sessionModel = useValue(host.state.model) || ''
  const modelLabel = sessionModel || 'this session\u2019s model'
  const modelIsFree = /:free$/i.test(sessionModel)

  const tl = TIMELINES.find(t => t.v === window) || TIMELINES[5]
  const shape = {
    decision, evidence, kind,
    urls: urls.split('\n').map(u => u.trim()).filter(Boolean),
  }
  const est = runEstimate(tl, shape)
  const suggested = suggestWindow(shape)
  const hasInput = decision.trim().length > 0 || urls.trim().length > 0

  // What those tokens would cost, if the catalogue publishes a price for exactly
  // this model. Read-only: this cannot pick a model or fail a run, and when the
  // price is unknown the form shows tokens and says nothing about money.
  const [price, setPrice] = React.useState(null)
  React.useEffect(() => {
    if (!sessionModel) { setPrice(null); return }
    let live = true
    ctx.rest(`/price?model=${encodeURIComponent(sessionModel)}&tin=${est.tin}&tout=${est.tout}`)
      .then(r => { if (live) setPrice(r) })
      .catch(() => { if (live) setPrice(null) })
    return () => { live = false }
  }, [sessionModel, est.tin, est.tout])

  // a run that will occupy the screen for minutes must announce itself: the
  // difference between "working" and "broken" is a sentence and a colour
  const longWait = tl.rounds >= 12 || kind === 'paper'

  // Three states, because "unknown" is not "free" and not "paid":
  //   loading  — the price request has not answered yet (first paint)
  //   free     — the catalogue says this exact id is free, or the slug says :free
  //   paid     — the catalogue prices this exact id
  //   unknown  — the catalogue has no entry and the slug says nothing
  // A two-way boolean flashed the free-tier warning on a paid model for as long
  // as the price request took, which is exactly what made the note look wrong.
  const priceState = price === null ? 'loading'
    : price.found ? (price.free ? 'free' : 'paid')
    : (modelIsFree ? 'free' : 'unknown')

  const costLine = !price || !price.found ? ''
    : price.free ? 'free'
    : price.cost_usd != null ? `≈$${Number(price.cost_usd).toFixed(3)} at the published price`
    : ''


  function applyRecipe(r) {
    setGoal(r.goal)
    setTitle(r.title)
    setDecision(r.decision)
    setEvidence(r.evidence)
    setUrls('')
    setShowGuide(true)
  }

  function useSample() {
    setTitle(SAMPLE.title); setDecision(SAMPLE.decision); setEvidence(SAMPLE.evidence)
  }

  async function submit() {
    if (!title.trim()) { setError('Give it a title — something you would recognise in a list.'); return }
    if (!hasInput) { setError('Add a decision document OR at least one URL — one of the two is required.'); return }
    haptic('tap')
    setBusy(true); setError('')
    try {
      const docs = []
      if (decision.trim()) docs.push({ type: 'decision', content: decision })
      if (evidence.trim()) docs.push({ type: 'evidence', content: evidence })
      const urlList = urls.split('\n').map(u => u.trim()).filter(Boolean)
      const res = await ctx.rest('/run', {
        method: 'POST',
        // no `model`: the backend runs on the host's active model. Sending one
        // would be a request the host is entitled to refuse, which is how a run
        // ends up on a model nobody chose.
        body: { title, goal, documents: docs, urls: urlList, window, kind },
      })
      onStarted(res.run_id, title)
    } catch (e) {
      setError('Could not start the review: ' + (e && e.message ? e.message : 'unknown error'))
    } finally { setBusy(false) }
  }

  return jsx(Dialog, {
    open: true,
    onOpenChange: open => { if (!open) onClose() },
    children: jsx(DialogContent, {
      // ONE scroll container, and it is the dialog itself. Two earlier shapes
      // failed the same way: a tall box with a scroller inside (header and footer
      // sat outside the height budget, so the Run button went off-screen), then a
      // flex column (correct in theory, but it depends on the shell having a
      // resolved height — and when it does not, flex-1 collapses to nothing and
      // the footer is still unreachable). Scrolling the whole content and pinning
      // the footer to the bottom of that scroll is the shape that holds whatever
      // the app's dialog does with height.
      // 84vh, not 90: the app draws its own banner above a plugin page (the
      // "unreviewed local source" notice), and a taller dialog lets that banner
      // land on this header — visible in a screen grab as a clipped, overlapping
      // title. Eight per cent of the viewport is cheaper than fighting the z-order.
      className: 'max-h-[84vh] w-[min(42rem,94vw)] max-w-none overflow-y-auto',
      children: [
        // The title block is PINNED, not scrolled. The dialog is the one scroll
        // container (see above), which means anything above the fold scrolls away
        // — and with a tall form that reads as "the top of this thing is broken".
        // A sticky header with the dialog's own background keeps "New arena
        // session" and the close affordance on screen at any scroll position.
        jsxs(DialogHeader, {
          className: 'sticky top-0 z-20 -mx-1 border-b border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-1 pb-2 pt-1',
          children: [
            jsx(DialogTitle, { children: `New ${ARENA} session` }),
            jsx(DialogDescription, { children: 'Add a link or the text — a README, a post, a whitepaper, an announcement. It opens the arena the room will answer in.' }),
          ],
        }),

        jsxs('div', { className: 'flex flex-col gap-3 pr-0.5', children: [
          jsx(Field, {
            label: 'Title',
            hint: 'Short and specific, the way you would say it out loud — it is what you will see in the run list.',
            children: jsx(Input, {
              autoFocus: true,
              placeholder: 'Name this decision…',
              value: title, onChange: e => setTitle(e.target.value),
            }),
          }),

          jsxs(Section, {
            label: 'Start from a recipe (optional)',
            action: jsx(Button, {
              size: 'xs', variant: 'ghost',
              onClick: () => setShowGuide(v => !v),
              children: showGuide ? 'hide what to paste' : 'what should I paste?',
            }),
            children: [
              jsx('div', { className: 'flex flex-wrap gap-1.5', children: RECIPES.map(r => jsx(Button, {
                key: r.id, size: 'xs', variant: 'chip',
                onClick: () => applyRecipe(r),
                children: r.label,
              })) }),
              showGuide && jsxs('div', { className: 'flex flex-col gap-1 rounded-md border border-(--ui-stroke-tertiary) p-2', children: [
                jsx('div', { className: FIELD_LABEL, children: 'source → what it buys the review' }),
                ...SOURCE_GUIDE.map(([k, v]) => jsxs('div', { className: 'grid grid-cols-2 gap-2 text-[0.6875rem]', children: [
                  jsx('span', { children: k }),
                  jsx('span', { className: 'text-(--ui-text-tertiary)', children: v }),
                ]})),
                jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: 'Two sources that disagree beat five that agree. A decision plus one piece of real evidence is the best cheap run.' }),
              ]}),
            ],
          }),

          jsx(Field, {
            label: 'Decision document — or URLs below',
            hint: 'Paste the plan, launch note or proposal being reacted to. Vague input produces vague stakeholders.',
            right: jsx(Button, { size: 'xs', variant: 'outline', onClick: useSample, children: 'Use a sample' }),
            children: jsx(Textarea, {
              className: 'min-h-20',
              placeholder: 'The decision — what you are launching, changing or removing, and who is affected…',
              value: decision, onChange: e => setDecision(e.target.value),
            }),
          }),

          jsx(Field, {
            label: 'Evidence (optional, biggest quality lever)',
            hint: 'Real numbers, quotes, survey results, competitor facts — anything factual a stakeholder would react to.',
            children: jsx(Textarea, {
              className: 'min-h-12',
              placeholder: 'e.g. "Q2 survey of 400 CIOs: 61% cannot route inference through an external API…"',
              value: evidence, onChange: e => setEvidence(e.target.value),
            }),
          }),

          jsx(Field, {
            label: 'Links (one per line — README, post, whitepaper, announcement)',
            hint: `Each line is fetched as a real document, with the URL kept as provenance. Good sources: ${URL_TYPES.join(' · ')}. Reading the links is the longest single step of a run — it happens once, before the room opens, so a big page can sit there a while before the first round lands.`,
            children: jsx(Textarea, {
              className: 'min-h-10',
              placeholder: 'https://github.com/owner/repo\nhttps://example.com/blog-post',
              value: urls, onChange: e => setUrls(e.target.value),
            }),
          }),
          jsx(Field, {
            label: 'What are you adding?',
            hint: kind === 'auto'
              ? 'Read off the link. A repo link brings maintainers and security reviewers; a post brings the people who quote it.'
              : kind === 'paper'
                ? 'Not the peer-review room: the market room. What this lens answers, and what it refuses to, is spelled out below.'
                : `The room: ${KIND_ROOM[kind] || KIND_ROOM.decision}.`,
            children: jsxs(Select, { value: kind, onValueChange: setKind, children: [
              jsx(SelectTrigger, { children: jsx(SelectValue, { placeholder: 'Auto-detect from the link' }) }),
              jsx(SelectContent, { children: KINDS.map(k => jsx(SelectItem, {
                key: k.v, value: k.v, children: k.label,
                })) }),
            ]}),
          }),
          kind === 'paper' ? jsx(PaperLensNote, {}) : null,
          jsxs('div', { className: 'grid grid-cols-2 gap-3', children: [
            jsx(Field, {
              label: 'Timeline',
              hint: `${tl.note} The suggestion below is read off what you have added.`,
              children: jsxs('div', { className: 'flex flex-col gap-1.5', children: [
                jsxs(Select, { value: window, onValueChange: setWindow, children: [
                  jsx(SelectTrigger, { children: jsx(SelectValue, {}) }),
                  jsx(SelectContent, { children: TIMELINES.map(t => jsx(SelectItem, {
                    key: t.v, value: t.v,
                    children: `${t.label} — ${t.rounds} rounds${t.v === suggested.v ? ' · suggested' : ''}`,
                  })) }),
                ]}),
                jsx(TimelineHint, { window, est, suggested }),
              ]}),
            }),
            jsx(Field, {
              label: 'Model',
              hint: 'A run uses whatever model this session is on — that is your default model setting. Change it in the app, not here.',
              children: jsxs('div', { className: 'flex flex-col gap-1 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-2.5 py-2', children: [
                jsx('div', { className: `truncate text-[0.75rem] font-medium text-(--ui-text-secondary)`, children: modelLabel }),
                jsxs('div', { className: `${T.micro} ${NUM} text-(--ui-text-tertiary)`, children: [
                  `${est.calls} calls · ≈${kTokens(est.tin)} tokens in / ≈${kTokens(est.tout)} tokens out`,
                  costLine ? ` · ${costLine}` : '',
                ]}),
                jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'Tokens are the run\u2019s own arithmetic — rounds × parties × the prompt window. Money appears only when the catalogue publishes a price for this exact model; the finished run prints what it actually cost.' }),
              ]}),
            }),

          // Which model runs, and what a free one costs in wall-clock. This is the
          // disclosure the review asked for, put where the decision is actually
          // made — and it says what this form can actually prove, nothing more.
          // The caveat is conditional on what we KNOW, not on a guess. On a model
          // the catalogue prices as paid, a "free tier, rate limits and all" banner
          // is noise that makes the form look like it is not reading its own state
          // — the reviewer's own screenshot showed a $0.017 run being warned about
          // free tiers. Unknown ids keep the caveat: one unnecessary paragraph is
          // cheaper than a degraded run nobody warned about.
          priceState === 'paid'
            ? jsx(Callout, { icon: 'info',
              title: 'Paid model — the free-tier caveat does not apply',
              children: jsxs('div', { className: 'flex flex-col gap-1 text-[0.75rem] leading-relaxed text-(--ui-text-tertiary)', children: [
                jsx('span', { children: `This run uses the model the app has bound to this session${sessionModel ? ` — ${sessionModel}` : ''}, billed at the published rate above. No model setting in this form: change it in the app, and the finished run prints the model that actually served it. A free model works too — it is only rate-limited on large inputs.` }),
              ]}),
            })
            : priceState === 'free'
            ? jsx(Callout, { icon: 'warning', tone: C.hold,
              title: 'This runs on your Hermes model — free tier included, rate limits and all',
              children: jsxs('div', { className: 'flex flex-col gap-1 text-[0.75rem] leading-relaxed text-(--ui-text-tertiary)', children: [
                jsx('span', { children: `This run uses the model the app has bound to this session${sessionModel ? ` — ${sessionModel}` : ''}. No model setting here: change it in the app, and if this line still shows the old one, reload the plugin page. The finished run prints the model that actually served it.` }),
                jsx('span', { children: 'A free tier is rate-limited and a large input feels it — a paper or a long post runs slower and can stop partway. For those, a paid model is the recommendation. If a run fails on a rate limit, nothing about your input is wrong: change the session to another model and run it again.' }),
              ]}),
            })
            : jsx(Callout, { icon: 'info',
              title: 'This run uses the model the app has bound to this session',
              children: jsxs('div', { className: 'flex flex-col gap-1 text-[0.75rem] leading-relaxed text-(--ui-text-tertiary)', children: [
                jsx('span', { children: `No model setting in this form: change it in the app${sessionModel ? ` (${sessionModel} right now)` : ''}, and the finished run prints the model that actually served it. Whether that model is free or paid decides whether you get a rate-limit note here.` }),
              ]}),
            }),
          ]}),

          // Anything that will visibly take minutes says so, in the accent
          // colour, before the user presses Run — otherwise a reviewer watches a
          // spinner and assumes the plugin is broken.
          longWait && jsx(Callout, { icon: 'info', tone: C.hold,
            title: `This will take about ${tl.eta} — that is normal, not a hang`,
            children: `${tl.rounds} rounds at about ${est.parties} parties${kind === 'paper' ? ', plus one call to read the paper\'s clock' : ''}. `
              + 'The page stays live while it runs: you will see each round land, and you can stop it between rounds.'
              + ' Most of that wait is ingestion: the links are fetched and read once, before any round appears — a long paper is the slowest step in the product.'
              + (modelIsFree ? ' On a free model expect the longer end of that range, and a large input can push past it.' : '') }),

          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: `${est.calls} model calls · ≈${kTokens(est.tin)} tokens in / ≈${kTokens(est.tout)} tokens out${costLine ? ' · ' + costLine : ''} · ${modelLabel}` }),
          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: 'For a first pass: whatever model the session is on, at 4–6 hours.' }),
          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: 'Go to 24h only when the parties are external and the decision is expensive.' }),

          error && jsx('span', { className: 'text-[0.75rem] text-destructive', children: error }),
        ]}),

        jsxs(DialogFooter, {
          // Pinned to the bottom of the scrolling dialog: a long form must never
          // be able to hide the button that starts it.
          className: 'sticky bottom-0 z-10 -mx-1 border-t border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) px-1 pt-3',
          children: [
          jsx('div', { className: 'mr-auto text-[0.75rem] text-(--ui-text-tertiary)', children: hasInput ? 'Ready — one input is enough.' : 'Add a decision document or a URL to run.' }),
          jsx(Button, { variant: 'text', onClick: onClose, children: 'Cancel' }),
          jsx(PrimaryAction, { disabled: busy || !hasInput || !title.trim(), onClick: submit, children: busy ? 'Starting…' : 'Run review' }),
        ]}),
      ],
    }),
  })
}

// ── comparison across timelines ──────────────────────────────────────

function ComparePanel({ cmp }) {
  if (!cmp || !cmp.rows || !cmp.rows.length) return null
  return jsxs(Card, { children: [
    jsxs('div', { className: 'flex items-center justify-between', children: [
      jsx('div', { className: T.h2, children: `Same decision across timelines — ${cmp.runs} run(s)` }),
      jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
        children: cmp.friction_spread != null ? `spread ${cmp.friction_spread} · blocker ${cmp.blocker_stable ? 'stable' : 'changed'}` : '' }),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: cmp.reading }),
    jsxs('div', { className: 'flex flex-col gap-1', children: [
      jsxs('div', { className: `grid grid-cols-5 gap-2 ${T.label} text-(--ui-text-quaternary)`, children: [
        jsx('span', { children: 'timeline' }), jsx('span', { children: 'heat' }),
        jsx('span', { children: 'market' }), jsx('span', { children: 'blocker' }), jsx('span', { children: 'scored' }),
      ]}),
      ...cmp.rows.map(r => jsxs('div', {
        key: r.run_id,
        className: `grid grid-cols-5 items-center gap-2 ${T.micro}`,
        children: [
          jsx('span', { children: `${r.rounds ?? '?'} rounds` }),
          jsx(FrictionGauge, { friction: r.friction, width: 90, height: 6 }),
          jsx('span', { children: r.sea_label || '—' }),
          jsx('span', { children: r.blocker || 'none' }),
          jsx('span', { children: r.verified && r.verified.verdict ? r.verified.verdict : '—' }),
        ],
      })),
    ]}),
  ]})
}

// ── page ──────────────────────────────────────────────────────────────

function UpfrontPage({ ctx }) {
  const [modal, setModal] = React.useState(false)
  const [showExplainer, setShowExplainer] = React.useState(true)
  const [running, setRunning] = React.useState(null)
  const [result, setResult] = React.useState(null)
  const [demo, setDemo] = React.useState(false)   // condensed finished-review view
  const [reloadNonce, setReloadNonce] = React.useState(0)  // remount key for "Reload page"
  const [history, setHistory] = React.useState([])
  const [compare, setCompare] = React.useState(null)
  const [showCompare, setShowCompare] = React.useState(true)
  const [claimHits, setClaimHits] = React.useState({})
  const [injectText, setInjectText] = React.useState('')
  const [showAudit, setShowAudit] = React.useState(false)
  // three views of the same evidence: what moved, what each party is worth, what
  // was actually said. Stacked they were most of the page; as tabs, one screen.
  const [evidenceTab, setEvidenceTab] = React.useState('moves')
  const [showAllPast, setShowAllPast] = React.useState(false)
  const [injectHint, setInjectHint] = React.useState('')
  const [injectImpact, setInjectImpact] = React.useState('')
  const [startedAt, setStartedAt] = React.useState(null)
  const [uiBuild, setUiBuild] = React.useState(null)
  const [reloading, setReloading] = React.useState(false)
  const [record, setRecord] = React.useState(null)
  const [due, setDue] = React.useState([])
  const gateway = useValue(host.state.gateway)

  // which build this window actually runs, vs the one installed — the app loads
  // its own copy of this file, so "I updated the plugin" and "this window shows
  // the new build" are two different things and the user should not have to guess
  React.useEffect(() => {
    ctx.rest(`/ui?build=${encodeURIComponent(BUILD)}`).then(setUiBuild).catch(() => setUiBuild(null))
  }, [])

  function reloadUi() {
    haptic('tap')
    setReloading(true)
    // Re-render THIS view and re-read its data. A window reload tears down the
    // webview — and with it the run you are watching — to achieve nothing: the UI
    // file is already in memory, and a reload cannot fetch a newer one anyway
    // (see UpdateCard). Remounting the page body is what "reload" should mean here.
    refreshHistory()
    ctx.rest(`/ui?build=${encodeURIComponent(BUILD)}`).then(setUiBuild).catch(() => setUiBuild(null))
    setReloadNonce(n => n + 1)
    window.setTimeout(() => setReloading(false), 400)
  }

  function openPluginSettings() {
    haptic('tap')
    try { host.navigate('/capabilities?tab=plugins') } catch (_) {}
  }

  function refreshHistory() {
    ctx.rest('/history').then(setHistory).catch(() => {})
    ctx.rest('/calibration').then(setRecord).catch(() => {})
    ctx.rest('/due').then(d => setDue(Array.isArray(d) ? d : (d && d.due) || [])).catch(() => {})
  }
  React.useEffect(() => { refreshHistory() }, [])

  async function openRun(runId, titleHint) {
    const [rep, g, cl, ev, meta, lev] = await Promise.all([
      ctx.rest(`/report/${runId}`).catch(() => ({ report: '' })),
      ctx.rest(`/graph/${runId}`).catch(() => ({ nodes: [], edges: [] })),
      ctx.rest(`/claims/${runId}`).catch(() => ({ claims: [] })),
      ctx.rest(`/events/${runId}`).catch(() => ({ events: [], snapshots: [] })),
      ctx.rest('/history').then(rows => (rows || []).find(h => h.run_id === runId) || {}).catch(() => ({})),
      ctx.rest(`/leverage/${runId}`).catch(() => ({ available: false })),
    ])
    setResult({
      runId, report: rep.report, graph: g, claims: cl.claims || [], leverage: lev,
      read: rep.read || {}, kind: rep.kind || '', moat: rep.moat || {},
      events: ev.events || [], snapshots: ev.snapshots || [],
      sea: meta.sea_state ? { state: meta.sea_state,
                             label: (SEA[meta.sea_state] && SEA[meta.sea_state].label) || meta.sea_label,
                             color: meta.sea_color,
                             why: meta.sea_why, meaning: SEA[meta.sea_state] ? SEA[meta.sea_state].meaning : '' } : null,
      friction: meta.friction, blocker: meta.blocker, blockerStance: meta.blocker_stance,
      recommendation: rep.recommendation, summary: rep.summary,
      counterMoves: rep.counter_moves, personas: rep.personas,
      interventions: rep.interventions, verified: meta.verified,
      camps: rep.camps || meta.camps || [],
      window: meta.window, createdAt: meta.created_at, title: meta.title || titleHint,
      modelNote: rep.model_note || '',
      modelRequested: rep.model_requested || '',
      modelServed: rep.model_served || '',
      modelFallback: rep.model_fallback_note || '',
      cost: rep.usage || null,
      // "your side": parties grounded in the decision document itself
      ownSide: (rep.personas || []).filter(p => (p.reasons?.[0] || '').includes('[decision')).map(p => p.name),
    })
    setClaimHits({})
    setShowAudit(false)
    setInjectImpact('')
    const t = titleHint || meta.title
    if (t) ctx.rest(`/compare?title=${encodeURIComponent(t)}`).then(setCompare).catch(() => {})
    // bring the answer into view — the page is long and the click was at the bottom
    try { window.scrollTo({ top: 0, behavior: 'smooth' }) } catch (_) {}
  }

  function started(runId) {
    setModal(false)
    setResult(null)
    setRunning({ runId, progress: 0, round: 0, total: 0, stances: {}, events: [] })
    setStartedAt(Date.now())
    setInjectImpact('')
    setInjectHint('')
    const iv = setInterval(async () => {
      const st = await ctx.rest(`/status/${runId}`).catch(() => null)
      if (!st) return
      setRunning({ runId, progress: st.progress || 0, round: st.round || 0,
        total: st.total || 0, stances: st.stances || {}, events: st.events || [],
        movers: st.movers || [] })
      if (st.status === 'done') {
        clearInterval(iv)
        setRunning(null)
        setStartedAt(null)
        refreshHistory()
        await openRun(runId)
      } else if (st.status === 'cancelled') {
        clearInterval(iv)
        setRunning({ runId, progress: 0, cancelled: true })
        setStartedAt(null)
      } else if (st.status === 'failed') {
        clearInterval(iv)
        setRunning({ runId, progress: 0, error: st.error || 'failed' })
      }
    }, 900)
  }

  async function cancelRun() {
    if (!running) return
    haptic('tap')
    await ctx.rest(`/cancel/${running.runId}`, { method: 'POST' }).catch(() => {})
  }

  async function inject() {
    if (!running) return
    if (!injectText.trim()) {
      setInjectHint('Describe the counter-move first — e.g. "Publish the eval suite first"')
      return
    }
    haptic('tap')
    setInjectHint('')
    setInjectImpact(`Injected ✓ — "${injectText.trim()}" lands at the start of the next round. Watch the board.`)
    await ctx.rest(`/inject/${running.runId}`, {
      method: 'POST', body: { name: 'Counter-move', description: injectText },
    }).catch(() => {})
    setInjectText('')
  }

  async function verify(verdict) {
    if (!result) return
    haptic('tap')
    await ctx.rest(`/verify/${result.runId}`, { method: 'POST', body: { verdict, hits: claimHits } }).catch(() => {})
    refreshHistory()
    setResult({ ...result, verified: { verdict } })
  }

  function loudest(kind) {
    const entries = Object.entries(running?.stances || {})
    if (!entries.length) return null
    const pick = kind === 'for'
      ? entries.reduce((a, b) => (b[1] > a[1] ? b : a), entries[0])
      : entries.reduce((a, b) => (b[1] < a[1] ? b : a), entries[0])
    const [name, stance] = pick
    const said = [...(running.events || [])].reverse()
      .find(e => e.actor === name && (e.text || '').trim())
    return { name, stance, said: said ? said.text : '' }
  }

  // remaining time from the pace so far — a 48h run needs an end time, not a spinner
  function etaLine() {
    if (!running || !startedAt || !running.round || !running.total) return ''
    const elapsed = (Date.now() - startedAt) / 60000
    const per = elapsed / running.round
    const left = Math.max(0, Math.round(per * (running.total - running.round)))
    return left <= 0 ? 'almost done' : `≈ ${left} min left`
  }

  // one list, newest first; collapsed to a third of the screen until asked
  const shown = showAllPast ? history : history.slice(0, 6)

  return jsxs('div', {
    // `key` remounts the body when "Reload page" is pressed: fresh state, fresh
    // data, no webview teardown, and a run in progress is undisturbed.
    key: `page-${reloadNonce}`,
    // scope the accent to this page only: every SDK control inside inherits it,
    // so the primary button is the product's blue without touching core UI
    style: { '--ui-accent': BRAND.blue },
    className: 'flex h-full flex-col gap-3 overflow-auto p-4', children: [
    // header — one line of identity, one line of state, one primary action
    jsxs('div', { className: 'flex flex-wrap items-center justify-between gap-3', children: [
      jsxs('div', { className: 'flex flex-col gap-1', children: [
        jsx(Wordmark, { size: 34 }),
        jsxs('div', { className: `flex flex-wrap items-center gap-2 ${T.micro} text-(--ui-text-quaternary)`, children: [
          jsx('span', { children: `gateway ${gateway}` }),
          jsx('span', { className: 'opacity-50', children: '·' }),
          jsx(Badge, { variant: 'outline', title: 'This window reads the UI file from the machine the app runs on. A new build has to be put there — see the banner when this one is behind.',
            children: uiBuild && uiBuild.installed && uiBuild.installed !== BUILD
              ? `build ${BUILD} → ${uiBuild.installed} installed`
              : `build ${BUILD}` }),
          jsx(Button, {
            variant: 'ghost', size: 'xs', disabled: reloading, onClick: reloadUi,
            title: 'Reloads this page. The app re-reads the UI file from this machine; this button never fetches a new one.',
            children: reloading ? 'Reloading…' : 'Reload page',
          }),
        ]}),
      ]}),
      jsxs('div', { className: 'flex items-center gap-2', children: [
        jsx(Button, {
          variant: 'ghost', size: 'xs', onClick: () => setShowExplainer(v => !v),
          children: showExplainer ? 'hide what you get' : 'what you get',
        }),
        jsx(LightAction, {
          onClick: () => { haptic('tap'); setModal(true) },
          children: '+ Start arena session',
        }),
      ]}),
    ]}),

    uiBuild && !uiBuild.up_to_date && jsx(UpdateCard, {
      uiBuild, onOpenPlugins: openPluginSettings }),

    modal && jsx(NewReviewModal, { ctx, onClose: () => setModal(false), onStarted: started }),

    // ── idle home ────────────────────────────────────────────────────
    !running && !result && jsx(Hero, { onStart: () => { haptic('tap'); setModal(true) } }),
    !running && !result && jsx(DemoCard, { best: demoPick(history),
      onOpen: (id, title) => { setDemo(true); openRun(id, title) } }),
    !running && !result && showExplainer && jsx(WhatYouGet, {}),

    // ── live run ─────────────────────────────────────────────────────
    running && !running.cancelled && !running.error && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsxs('div', { className: 'flex flex-col gap-2.5 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) p-4', children: [
        jsxs('div', { className: 'flex flex-wrap items-end justify-between gap-2', children: [
          jsxs('div', { className: 'flex min-w-0 flex-col gap-1', children: [
            jsxs('div', { className: 'flex items-center gap-2', children: [
              // A pill, not a button: there is already one control on this card
              // (Cancel run), and a second blue thing beside it would read as an
              // action. The dot dims when the room is closing, so the state is
              // carried by the pill itself.
              jsx('span', {
                className: 'inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-[3px] text-[0.5625rem] font-bold uppercase tracking-[0.12em]',
                style: { backgroundColor: BRAND.blue, color: '#04121f' },
                children: [
                  jsx('span', {
                    className: 'h-1.5 w-1.5 rounded-full',
                    style: { backgroundColor: '#04121f',
                      opacity: (running.progress || 0) >= 100 ? 0.35 : 1 },
                  }),
                  'live',
                ],
              }),
              // not <Label>: that uppercases, and this line is the name the user
              // asked to see, exactly as written.
              jsx('div', { className: 'text-[0.625rem] font-semibold tracking-[0.08em] text-(--ui-text-quaternary)',
                children: `${ARENA} - LIVE` }),
            ]}),
            jsx('div', { className: T.h1,
              children: running.progress >= 100
                ? `Closing the ${ARENA} — writing the call`
                : `The ${ARENA} is in session` }),
          ]}),
          jsxs('div', { className: 'flex flex-col items-end gap-0.5', children: [
            jsx('div', { className: `${T.small} font-medium ${NUM}`,
              children: running.total ? `Round ${running.round} of ${running.total}` : 'starting' }),
            jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: [
              startedAt ? `started ${Math.max(1, Math.round((Date.now() - startedAt) / 60000))} min ago` : '',
              etaLine() ? ` · ${etaLine()}` : '',
            ]}),
          ]}),
        ]}),
        jsx(RoundTrack, { round: running.round, total: running.total }),
        (running.round || 0) === 0 && jsx(WorkingBar, {
          startedAt, round: running.round,
          label: (running.events || []).length ? 'Opening the arena' : undefined }),
        jsxs('div', { className: 'grid gap-2 md:grid-cols-2', children: [
          LoudestLine({ who: loudest('against'), kind: 'against' }),
          LoudestLine({ who: loudest('for'), kind: 'for' }),
        ]}),
        jsx(LiveFloor, { events: running.events }),
      ]}),

      jsx(LiveWorth, { lev: running.leverage }),

      jsxs('div', { className: 'grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]', children: [
      Object.keys(running.stances || {}).length > 0 && jsxs(Card, { children: [
        jsx('div', { className: T.h2, children: 'The board, live' }),
        jsx(RoomBoard, { nodes: Object.entries(running.stances || {}).map(([name, stance]) => ({ id: name, name, stance })) }),
      ]}),

      jsxs(Card, { children: [
        jsx(Label, { children: 'counter-moves' }),
        jsx('div', { className: `${T.small} text-(--ui-text-secondary)`,
          children: 'Change the room, not the record. Announce a concession, publish something first, bring a champion forward — everyone hears it before they speak next round, and the board bends where you can see it.' }),
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx(Input, {
            className: 'flex-1',
            placeholder: 'Your counter-move…',
            value: injectText, onChange: e => setInjectText(e.target.value),
            onKeyDown: e => { if (e.key === 'Enter') inject() },
          }),
          jsx(PrimaryAction, { onClick: inject, children: 'Inject ⚡' }),
        ]}),
        jsx('div', { className: 'flex flex-wrap gap-1.5', children: [
          'Publish the eval suite first',
          'Cap the free window at a fixed budget',
          'Bring a named enterprise champion forward',
          'Offer the two resellers a protection clause',
        ].map(s => jsx(Button, {
          key: s, size: 'xs', variant: 'outline',
          onClick: () => setInjectText(s),
          children: s,
        })) }),
        injectHint && jsx('div', { className: `${T.small}`, style: { color: C.hold }, children: injectHint }),
        injectImpact && jsx('div', { className: `${T.small} text-(--ui-text-secondary)`, children: injectImpact }),
        jsx('div', { className: 'flex items-center justify-between pt-0.5', children: [
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
            children: 'Nothing is saved until the run finishes — a cancelled run leaves no history.' }),
          jsx(Button, { size: 'xs', variant: 'ghost', onClick: cancelRun, children: 'Cancel run' }),
        ]}),
      ]}),
      ]}),
    ]}),

    running && running.cancelled && jsx(Callout, { icon: 'info', tone: 'var(--ui-accent)',
      title: 'Run cancelled',
      children: 'Stopped before it finished — nothing was written to your Past reviews, so your history only ever holds complete runs.' }),

    running && running.error && jsx(Callout, { icon: 'error', tone: 'var(--destructive)', title: 'Run failed', children: running.error }),

    // ── finished result ──────────────────────────────────────────────
    demo && result && jsx(DemoReview, {
      result, record,
      onBack: () => { setDemo(false); setResult(null) },
      onFull: () => setDemo(false),
      onStart: () => { haptic('tap'); setDemo(false); setResult(null); setModal(true) },
    }),
    result && !demo && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
        jsxs('div', { className: 'flex flex-col', children: [
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
            children: result.kind === 'paper' ? 'paper read' : 'review' }),
          jsx('div', { className: T.h1, children: result.title || 'This review' }),
        ]}),
        jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: [
          result.createdAt ? ago(result.createdAt) : '',
          result.window ? ` · ${result.window} window` : '',
          result.personas?.length ? ` · ${result.personas.length} parties` : '',
          result.claims?.length ? ` · ${result.claims.length} claims frozen` : '',
          result.cost && result.cost.calls
            ? ` · ${result.cost.calls} calls, ${kTokens(result.cost.tokens_total || 0)} tokens`
            : '',
          result.cost && result.cost.cost_known
            ? ` · $${Number(result.cost.cost_usd).toFixed(3)} spent`
            : '',
        ]}),
      ]}),

      jsx(AnswerCard, { result }),

      jsx(PaperRead, { moat: result.moat }),

      // the three-line read is folded into the answer card for a paper — the
      // claim is already line one, and repeating it is the "ton of text" the
      // reader complained about
      result.kind === 'paper' ? null : jsx(WhatItMeans, { read: result.read, kind: result.kind }),

      jsx(VerdictPanel, { result }),

      jsx(OnYourSide, { personas: result.personas, lev: result.leverage }),

      result.modelFallback && jsx(Callout, { icon: 'warning', tone: C.hold,
        title: 'The model you picked was not used', children: result.modelFallback }),

      // the room: board first (who stands where), then the words (why)
      jsxs('div', { className: 'grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]', children: [
        jsxs(Card, { children: [
          jsx('div', { className: T.h2, children: 'The room, in order' }),
          jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
            children: 'Sorted from the people most against you to the people most behind you.' }),
          jsx(RoomBoard, {
            nodes: (result.personas || []).map((p, i) => ({ id: `p${i}`, name: p.name, stance: p.stance,
              capacity: p.capacity, reasons: p.reasons })),
            ownSide: result.ownSide, blocker: result.blocker,
          }),
        ]}),
        jsxs('div', { className: 'flex flex-col gap-3', children: [
          (result.camps || []).filter(c => (c.members || []).length >= 2).length > 0 && jsxs(Card, { children: [
            jsx('div', { className: T.h2, children: 'Coalitions that formed' }),
            jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
              children: 'Parties that moved together. A camp is only a camp when two or more of them agree.' }),
            ...result.camps.filter(c => (c.members || []).length >= 2).map((c, i) => {
              const lean = c.lean === 'against' ? C.against : c.lean === 'for' ? C.for : C.hold
              return jsxs('div', { className: 'flex flex-col gap-0.5 border-t border-(--ui-stroke-tertiary) pt-1.5 first:border-t-0 first:pt-0', children: [
                jsxs('div', { className: 'flex items-center gap-1.5', children: [
                  jsx('span', { className: 'inline-block size-1.5 rounded-full', style: { backgroundColor: lean } }),
                  jsx('span', { className: `${T.small} font-medium`, children: c.name }),
                  jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: c.lean }),
                ]}),
                jsx('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: (c.members || []).join(' · ') }),
              ]})
            }),
          ]}),
        ]}),
      ]}),
      (result.personas || []).length > 0 && jsx(Card, { children: jsx(EvidenceGraph, { personas: result.personas }) }),

      // ── the evidence, one screen at a time ───────────────────────────
      jsxs('div', { className: 'flex flex-col gap-2', children: [
        jsx(Tabs, { value: evidenceTab, onValueChange: setEvidenceTab, children: [
          jsx(TabsList, { className: 'self-start', children: [
            jsx(TabsTrigger, { value: 'moves',
              children: `over time${result.rounds ? ` · ${result.rounds} rounds` : ''}` }),
            jsx(TabsTrigger, { value: 'ledger',
              children: `the ledger${(result.personas || []).length ? ` · ${result.personas.length} parties` : ''}` }),
            jsx(TabsTrigger, { value: 'words',
              children: `what they said${(result.events || []).length ? ` · ${result.events.length}` : ''}` }),
          ]}),
        ]}),
        evidenceTab === 'moves' && jsx(MovementChartCard, { snapshots: result.snapshots }),
        evidenceTab === 'ledger' && jsx(HeatLedger, { lev: result.leverage }),
        evidenceTab === 'words' && jsx(Transcript, { events: result.events, rounds: result.rounds }),
      ]}),

      jsx(Scorecard, { result, claimHits, setClaimHits, onVerify: verify, record, due }),

      // the receipt: what was actually done, in one line
      jsxs('div', { className: `flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg border border-dashed border-(--ui-stroke-tertiary) px-3 py-2 ${T.small} text-(--ui-text-tertiary)`, children: [
        jsx('span', { children: `${result.personas?.length || 0} parties` }),
        jsx('span', { children: '·' }),
        jsx('span', { children: `${result.events?.length || 0} statements` }),
        jsx('span', { children: '·' }),
        jsx('span', { children: `${result.claims?.length || 0} claims` }),
        jsx('span', { children: '·' }),
        jsx('span', { children: `served by ${result.modelServed || result.modelRequested || 'the active model'}` }),
        result.modelNote ? jsx('span', { children: `· ${result.modelNote}` }) : null,
      ]}),

      // the audit is for the people who want it, not for the reader who wants the answer
      result.report && jsxs('div', { className: 'flex flex-col gap-1', children: [
        jsx(Button, {
          size: 'xs', variant: 'ghost', className: 'self-start',
          onClick: () => setShowAudit(!showAudit),
          children: showAudit ? 'hide the full audit (provenance, round log, failure modes)'
                             : 'show the full audit (provenance, round log, failure modes)',
        }),
        showAudit && jsx(Card, { className: 'max-h-[480px] overflow-auto',
          children: jsx(Markdown, { text: result.report }) }),
      ]}),
    ]}),

    !running && result && compare && showCompare && jsxs('div', { className: 'flex flex-col gap-1', children: [
      jsx(ComparePanel, { cmp: compare }),
      jsx(Button, { size: 'xs', variant: 'ghost', className: 'self-start',
        onClick: () => setShowCompare(false), children: 'hide comparison' }),
    ]}),

    // ── every run, one line each, in the lower third ─────────────────
    history.length > 0 && jsxs('div', { className: 'flex flex-col gap-1.5 pt-2', children: [
      jsxs('div', { className: 'flex items-end justify-between gap-3', children: [
        jsxs('div', { className: 'flex flex-col gap-0.5', children: [
          jsx(Label, { children: 'your reviews' }),
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
            children: `${history.length} ${history.length === 1 ? 'run' : 'runs'}${due.length ? ` · ${due.length} ready to score` : ''} · click a row to read it` }),
        ]}),
        history.length > 6
          ? jsx(Button, { size: 'xs', variant: 'ghost', onClick: () => setShowAllPast(v => !v),
              children: showAllPast ? 'show fewer' : `show all ${history.length}` })
          : null,
      ]}),
      jsx(RunTableHead, {}),
      jsxs('div', {
        className: 'flex flex-col rounded-lg border border-(--ui-stroke-tertiary) px-1.5',
        style: { backgroundColor: 'var(--ui-bg-elevated)' },
        children: shown.map(h => jsx(RunLine, { key: h.run_id, h, onOpen: openRun })),
      }),
    ]}),
  ]})
}

function MovementChartCard({ snapshots }) {
  const rows = (snapshots || []).filter(s => s && s.stances && Object.keys(s.stances).length)
  if (rows.length < 2) return null
  return jsx(Card, { children: jsx(MovementChart, { snapshots }) })
}

// ── report markdown ───────────────────────────────────────────────────

function inline(text) {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => (part.startsWith('**') && part.endsWith('**') && part.length > 4
    ? jsx('strong', { key: i, children: part.slice(2, -2) })
    : part))
}

function Markdown({ text }) {
  const lines = String(text || '').split('\n')
  return jsx('div', { className: 'flex flex-col gap-1 text-xs', children: lines.map((ln, i) => {
    const key = `md${i}`
    if (ln.startsWith('### ')) return jsx('div', { key, className: 'text-sm font-semibold', children: inline(ln.slice(4)) })
    if (ln.startsWith('## ')) return jsx('div', { key, className: 'mt-2 text-sm font-semibold', children: inline(ln.slice(3)) })
    if (ln.startsWith('# ')) return jsx('div', { key, className: 'text-base font-semibold', children: inline(ln.slice(2)) })
    if (ln.startsWith('> ')) return jsx('div', { key, className: 'border-l-2 border-(--ui-stroke-tertiary) pl-2 text-(--ui-text-tertiary)', children: inline(ln.slice(2)) })
    if (ln.startsWith('- ')) return jsx('div', { key, className: 'pl-3', children: inline(`• ${ln.slice(2)}`) })
    if (!ln.trim()) return jsx('div', { key, className: 'h-1' })
    return jsx('div', { key, children: inline(ln) })
  }) })
}

export default {
  id: 'strategic-arena',
  name: PRODUCT_NAME,
  defaultEnabled: false,
  register(ctx) {
    ctx.registerMany([
      { id: 'page', area: ROUTES_AREA, data: { path: '/strategic-arena' }, render: () => jsx(UpfrontPage, { ctx }) },
      { id: 'nav', area: SIDEBAR_NAV_AREA, data: { path: '/strategic-arena', label: PRODUCT_NAME, codicon: 'graph' } },
    ])
  },
}
