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
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
  Textarea,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
} from '@hermes/plugin-sdk'
import React from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const BUILD = '0.5.2 · ui14'          // bump on every UI change — how you know the app reloaded
const PRODUCT_NAME = 'Upfront Prediction'   // display only — one line to rename the product
const TAGLINE = 'Rehearse the reaction before you commit.'

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

// One meaning per colour. Nothing decorative is coloured.
const C = {
  against: '#e5484d',   // will block
  hold: '#f5a524',      // undecided / conditional
  for: '#46a758',       // behind it
  own: '#8b5cf6',       // the parties your own document names
  ink: '#e8ecf2',       // label text on a canvas
  halo: 'rgba(6,8,12,.86)',
}
const SEA = {
  red: { label: 'Red ocean', color: '#e5484d', meaning: 'everyone is fighting for the same fish — you will be read as another entrant' },
  purple: { label: 'Purple ocean', color: '#8b5cf6', meaning: 'contested middle — winnable ground, but not free' },
  blue: { label: 'Blue ocean', color: '#3b82f6', meaning: 'open water — nobody is contesting this yet' },
}
const SEA_ORDER = ['red', 'purple', 'blue']

const ACTION_WORD = {
  blocks: 'against it', supports: 'behind it', shares: 'conditional',
  waits: 'holding back', intervention: 'you changed the situation',
}

// eta = realistic wall-clock on a free, rate-limited model — the number that
// decides whether a 24h review is a 5-minute check or a 30-minute wait.
const TIMELINES = [
  { v: '30m', label: '30 minutes', rounds: 3, note: 'Sanity check — does anyone care at all? Cheapest.', eta: '2–5 min' },
  { v: '1h', label: '1 hour', rounds: 5, note: 'First reactions only. Good for a fast no.', eta: '4–8 min' },
  { v: '4h', label: '4 hours', rounds: 8, note: 'Positions form. Catches the obvious blocker.', eta: '6–12 min' },
  { v: '6h', label: '6 hours', rounds: 10, note: 'Coalitions start to show.', eta: '8–15 min' },
  { v: '12h', label: '12 hours', rounds: 12, note: 'Counter-moves get tested.', eta: '10–20 min' },
  { v: '24h', label: '24 hours', rounds: 16, note: 'Recommended. Full reaction cycle.', eta: '15–30 min' },
  { v: '48h', label: '48 hours', rounds: 20, note: 'Deepest read — hard to move a veto player. ~2x cost.', eta: '25–45 min' },
]
const WINDOW_HOURS = { '30m': 0.5, '1h': 1, '4h': 4, '6h': 6, '12h': 12, '24h': 24, '48h': 48 }

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
// people who gain. That is what "rehearsal" means on screen.
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
    jsxs('div', { className: 'flex flex-col', children: [
      jsx('div', { className: 'text-[0.9375rem] font-semibold leading-none tracking-[-0.01em]', children: PRODUCT_NAME }),
      jsx('div', { className: cn(T.label, 'mt-1 text-(--ui-text-quaternary)'), children: 'strategic rehearsal' }),
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
  if (n < 20) return { name: 'A quiet room', color: '#6b7280',
    why: 'Most of the people who matter are behind this — or nobody with power has engaged. That is good, and it is also why the frozen claims matter more than the score: quiet rooms can hide indifference.' }
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
        background: 'linear-gradient(90deg, #46a758 0%, #46a758 20%, #f5a524 45%, #f5a524 64%, #e5484d 82%, #e5484d 100%)',
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
  if (!list.length) {
    return jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`, children: 'No parties yet.' })
  }
  const own = new Set(ownSide || [])
  return jsxs('div', { className: 'flex flex-col', children: [
    // three named groups, counted — the scale answers "what does this mean"
    jsx(ZoneStrip, { list }),
    ...list.map((n, i) => {
      const tone = stanceTone(n.stance)
      const isBlocker = blocker && (n.name === blocker)
      const d = deltas && deltas[n.name] != null ? Number(deltas[n.name]) : null
      return jsxs('div', {
        key: n.id || n.name || `r${i}`,
        className: 'flex items-start gap-3 border-t border-(--ui-stroke-tertiary) py-3 first:border-t-0',
        children: [
          jsxs('div', { className: 'flex w-[10rem] shrink-0 flex-col gap-1', children: [
            jsxs('div', { className: 'flex items-center gap-1.5', children: [
              jsx('span', {
                className: 'inline-block size-1.5 shrink-0 rounded-full',
                style: { backgroundColor: tone.color },
              }),
              jsx('span', { className: `truncate ${T.small} font-medium`, title: n.name, children: n.name }),
            ]}),
            jsxs('div', { className: `flex items-center gap-1 ${T.micro}`, children: [
              jsx('span', { style: { color: tone.color }, children: tone.word }),
              isBlocker ? jsx('span', { className: 'font-semibold', style: { color: C.against }, children: '· can stop it' }) : null,
              own.has(n.name) ? jsx('span', { style: { color: C.own }, children: '· your side' }) : null,
            ]}),
          ]}),
          jsxs('div', { className: 'flex flex-1 flex-col gap-1.5 pt-1.5', children: [
            jsx(StanceMeter, { value: n.stance }),
            n.reasons && n.reasons[0]
              ? jsx('div', { className: `${T.small} leading-snug text-(--ui-text-secondary)`, children: n.reasons[0] })
              : null,
          ]}),
          jsxs('div', { className: 'flex w-[6.5rem] shrink-0 flex-col items-end gap-1 pt-1', children: [
            jsx(PowerPips, { cap: n.capacity, color: tone.color }),
            jsx(PowerWord, { cap: n.capacity }),
            d != null && Math.abs(d) >= 0.05
              ? jsx('span', { className: `${T.micro} ${NUM} font-medium`,
                  style: { color: d > 0 ? C.for : C.against },
                  children: `${d > 0 ? '▲' : '▼'} ${Math.abs(d).toFixed(1)}` })
              : jsx('span', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'steady' }),
          ]}),
        ],
      })
    }),
    jsxs('div', { className: `pt-2 ${T.micro} text-(--ui-text-quaternary)`, children: [
      'Bar length = how strongly they back or oppose it, from the centre. Power = how much they can stop you outright.',
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
        style: isGod ? { color: C.own } : undefined,
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
  waits: C.hold, intervention: C.own,
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

function LiveFloor({ events }) {
  const list = (events || []).filter(e => e && (e.text || '').trim())
  if (!list.length) {
    return jsx('div', { className: `${T.small} text-(--ui-text-tertiary)`,
      children: 'The room is reading your documents — the first statements land in a moment.' })
  }
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsx(Label, { children: 'on the floor' }),
    jsxs('div', { className: 'flex flex-col gap-2', children: list.map((e, i) => {
      const isGod = e.actor === '<god>'
      return jsxs('div', { className: 'flex gap-2.5', children: [
        jsx('span', { className: 'mt-1.5 inline-block size-1.5 shrink-0 rounded-full',
          style: { backgroundColor: isGod ? C.own : 'var(--ui-accent)' } }),
        jsxs('div', { className: 'flex flex-1 flex-col', children: [
          jsxs('div', { className: 'flex items-baseline gap-1.5', children: [
            jsx('span', { className: `${T.micro} font-semibold`, style: isGod ? { color: C.own } : undefined,
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
  return jsxs(Card, { tone: C.own, children: [
    jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
      jsx('div', { className: T.h2, children: 'The call, frozen' }),
      jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
        dueDate ? (isDue ? 'window closed — score it now' : `score it in ${until(dueDate)}`) : '',
      ]}),
    ]}),
    jsx('div', { className: `${T.small} text-(--ui-text-secondary)`,
      children: scored
        ? `You scored this run "${scored}". That is the whole point: a rehearsal you can audit, not a horoscope.`
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

// "Go talk to Legal" is not an instruction. Their condition names the artefact
// that ends the objection; this maps the words they used onto what to carry into
// the room. Derived, never invented — the condition itself is shown verbatim.
function unblockArtefact(condition) {
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
            jsx('span', { className: 'text-(--ui-text-secondary)', children: unblockArtefact(condition) }),
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
        jsx('h1', { className: `${T.display} max-w-[40rem]`, children: TAGLINE }),
        jsx('p', { className: `max-w-[44rem] ${T.body} text-(--ui-text-secondary)`,
          children: 'Paste a decision — a launch note, a price change, a memo, or a URL. Upfront gathers the people who will react to it into one room, lets them argue for as many rounds as you ask for, and hands back the call: who can stop you, what they need, and the move that gets you past them.' }),
        jsx('p', { className: `max-w-[44rem] ${T.small} text-(--ui-text-tertiary)`,
          children: 'Every party and every condition comes from the text you paste — nothing is invented. It is a rehearsal, not a forecast.' }),
      ]}),
      jsxs('div', { className: 'flex flex-wrap items-center gap-2', children: [
        jsx(Button, { onClick: onStart, className: 'h-9 px-3.5 text-[0.875rem]', children: 'Rehearse a decision' }),
        jsx('span', { className: `${T.micro} text-(--ui-text-tertiary)`,
          children: 'Three rounds takes about two minutes on a free model — a cheap way to find out whether anyone cares.' }),
      ]}),
      jsxs('div', { className: 'grid gap-4 border-t border-(--ui-stroke-tertiary) pt-4 md:grid-cols-3', children: [
        jsx(Step, { n: 1, title: 'Paste the move',
          body: 'The decision plus one or two real facts. Vague input produces vague stakeholders — that is the only rule.' }),
        jsx(Step, { n: 2, title: 'The room reacts',
          body: 'Each party remembers, argues and shifts round by round. You can change the situation mid-run and watch it bend.' }),
        jsx(Step, { n: 3, title: 'Read the call',
          body: 'Blocker, condition, best move — plus claims frozen at run time, so you can check us later.' }),
      ]}),
    ],
  })
}

function WhatYouGet() {
  return jsxs('div', { className: 'flex flex-col gap-2', children: [
    jsx(Label, { children: 'what comes back' }),
    jsxs('div', { className: 'grid gap-2 md:grid-cols-4', children: [
      jsx(GetTile, { title: 'Who can stop you', body: 'The one party with the power to block it — and how much power that is.' }),
      jsx(GetTile, { title: 'What they need', body: 'The condition each objector would accept, quoted from your own document.' }),
      jsx(GetTile, { title: 'Your best move', body: 'The counter-move that converts the blocker instead of fighting them.' }),
      jsx(GetTile, { title: 'A scorecard', body: 'Claims frozen at run time. Score them when the window closes — that is our record, not our opinion.' }),
    ]}),
    jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`,
      children: 'Not a forecast and not a guarantee. A rehearsal finds the fight before you are in it, and writes down its calls so you can grade them.' }),
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
        style: due ? { color: C.own } : undefined,
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
      'Capabilities → Plugins → Install from Git → trillionverselabs-boop/upfront-test → tick Desktop → Install. The app copies the file and reloads it.',
    ]}),
    jsxs('div', { className: `${T.micro} text-(--ui-text-tertiary)`, children: [
      jsx('strong', { children: 'Or drop the file in yourself: ' }),
      'replace `%USERPROFILE%\\.hermes\\desktop-plugins\\upfront\\plugin.js`. The app watches that file and reloads the page in place.',
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
  const [goal, setGoal] = React.useState('adoption')
  const [showGuide, setShowGuide] = React.useState(false)
  const [models, setModels] = React.useState([])
  const [modelId, setModelId] = React.useState('')
  const [freeOnly, setFreeOnly] = React.useState(false)
  const [modelAccess, setModelAccess] = React.useState(null)
  const [note, setNote] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState('')

  React.useEffect(() => {
    ctx.rest('/model-access').then(setModelAccess).catch(() => setModelAccess(null))
  }, [])

  React.useEffect(() => {
    ctx.rest('/models').then(r => {
      setModels(r.models || [])
      setNote(r.error ? r.error : r.count ? `${r.count} models · ${r.free_count} free · fetched ${r.fetched_at}` : '')
    }).catch(() => setNote('model catalogue unavailable'))
  }, [])

  const tl = TIMELINES.find(t => t.v === window) || TIMELINES[5]
  const calls = tl.rounds * 8 + 16
  const visibleModels = freeOnly ? models.filter(m => m.free) : models
  const chosen = models.find(m => m.id === modelId)
  const perCall = chosen ? (700 / 1e6) * chosen.prompt_per_m + (120 / 1e6) * chosen.completion_per_m : 0
  const cost = !chosen ? 'your active model'
    : modelAccess && !modelAccess.allowed ? 'FREE (active model — choice not granted)'
    : chosen.free ? 'FREE' : `~$${(calls * perCall).toFixed(3)} at list price`
  const hasInput = decision.trim().length > 0 || urls.trim().length > 0

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
        body: { title, goal, documents: docs, urls: urlList, window, model: modelId || undefined },
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
      className: 'w-[min(42rem,94vw)] max-w-none overflow-visible',
      children: [
        jsxs(DialogHeader, { children: [
          jsx(DialogTitle, { children: 'New review' }),
          jsx(DialogDescription, { children: 'Describe the move; Upfront rehearses the response to it.' }),
        ]}),

        jsxs('div', { className: 'flex max-h-[min(72vh,44rem)] flex-col gap-3 overflow-y-auto pr-0.5', children: [
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
            label: 'URLs (optional — one per line)',
            hint: `Each line is fetched as a real document, with the URL kept as provenance. Good sources: ${URL_TYPES.join(' · ')}.`,
            children: jsx(Textarea, {
              className: 'min-h-10',
              placeholder: 'https://github.com/owner/repo\nhttps://example.com/blog-post',
              value: urls, onChange: e => setUrls(e.target.value),
            }),
          }),

          jsxs('div', { className: 'grid grid-cols-2 gap-3', children: [
            jsx(Field, {
              label: 'Timeline',
              hint: `${tl.note} About ${tl.eta} on a free model.`,
              children: jsxs(Select, { value: window, onValueChange: setWindow, children: [
                jsx(SelectTrigger, { children: jsx(SelectValue, {}) }),
                jsx(SelectContent, { children: TIMELINES.map(t => jsx(SelectItem, {
                  key: t.v, value: t.v, children: `${t.label} — ${t.rounds} rounds`,
                })) }),
              ]}),
            }),
            jsx(Field, {
              label: 'Model',
              hint: 'Leave on active model to use whatever Hermes already runs. Choosing a specific model is a host permission — without it the run uses your active model.',
              children: jsxs('div', { className: 'flex flex-col gap-1', children: [
                jsxs(Select, { value: modelId || 'active', onValueChange: v => setModelId(v === 'active' ? '' : v), children: [
                  jsx(SelectTrigger, { children: jsx(SelectValue, {}) }),
                  jsx(SelectContent, { children: [
                    jsx(SelectItem, { value: 'active', children: 'active model (default)' }),
                    ...visibleModels.map(m => jsx(SelectItem, {
                      key: m.id, value: m.id,
                      children: `${m.free ? 'FREE · ' : ''}${m.name} — $${m.prompt_per_m}/M in`,
                    })),
                  ]}),
                ]}),
                jsxs('label', { className: 'flex cursor-pointer items-center gap-2 text-[0.75rem] text-(--ui-text-secondary)', children: [
                  jsx(Switch, { 'aria-label': 'free models only', checked: freeOnly, onCheckedChange: setFreeOnly, size: 'xs' }),
                  'free models only',
                ]}),
              ]}),
            }),
          ]}),

          // the host gates model choice — warn BEFORE the run, not after it fails
          chosen && modelAccess && !modelAccess.allowed && jsx(Callout, { icon: 'info',
            tone: 'var(--ui-accent)',
            title: 'The host has not granted model choice',
            children: `This run will use your active model instead of ${chosen.name}. To let the picker choose, add "${modelAccess.config_key}: true" to config.yaml (a host permission, not a plugin setting).` }),

          // free models are the default here and they are SLOW — say so before
          // the user commits 30 minutes to a 24h review with no explanation
          chosen?.free && jsx(Callout, { icon: 'info', tone: 'var(--ui-accent)',
            title: 'Free models are rate-limited and slow',
            children: `Expect roughly ${tl.eta} for this timeline, sometimes more. A 30-minute run is a fast sanity check; 24 hours is the full reaction cycle.` }),

          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: `${calls} model calls · ${cost}${note ? ' · ' + note : ''}` }),
          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: 'For a first pass: a flash-class model at 24h.' }),
          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: 'Spend on 48h and a bigger model only when the decision is expensive.' }),

          error && jsx('span', { className: 'text-[0.75rem] text-destructive', children: error }),
        ]}),

        jsxs(DialogFooter, { children: [
          jsx('div', { className: 'mr-auto text-[0.75rem] text-(--ui-text-tertiary)', children: hasInput ? 'Ready — one input is enough.' : 'Add a decision document or a URL to run.' }),
          jsx(Button, { variant: 'text', onClick: onClose, children: 'Cancel' }),
          jsx(Button, { disabled: busy || !hasInput || !title.trim(), onClick: submit, children: busy ? 'Starting…' : 'Run review' }),
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
  const [showExplainer, setShowExplainer] = React.useState(false)
  const [running, setRunning] = React.useState(null)
  const [result, setResult] = React.useState(null)
  const [history, setHistory] = React.useState([])
  const [compare, setCompare] = React.useState(null)
  const [showCompare, setShowCompare] = React.useState(true)
  const [claimHits, setClaimHits] = React.useState({})
  const [injectText, setInjectText] = React.useState('')
  const [showAudit, setShowAudit] = React.useState(false)
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
    // A page reload re-runs the app's plugin scan, which re-reads the UI file
    // from this machine. It cannot fetch a new one — see UpdateCard.
    window.location.reload()
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
    const [rep, g, cl, ev, meta] = await Promise.all([
      ctx.rest(`/report/${runId}`).catch(() => ({ report: '' })),
      ctx.rest(`/graph/${runId}`).catch(() => ({ nodes: [], edges: [] })),
      ctx.rest(`/claims/${runId}`).catch(() => ({ claims: [] })),
      ctx.rest(`/events/${runId}`).catch(() => ({ events: [], snapshots: [] })),
      ctx.rest('/history').then(rows => (rows || []).find(h => h.run_id === runId) || {}).catch(() => ({})),
    ])
    setResult({
      runId, report: rep.report, graph: g, claims: cl.claims || [],
      events: ev.events || [], snapshots: ev.snapshots || [],
      sea: meta.sea_state ? { state: meta.sea_state, label: meta.sea_label, color: meta.sea_color,
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

  return jsxs('div', { className: 'flex h-full flex-col gap-3 overflow-auto p-4', children: [
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
          children: showExplainer ? 'hide overview' : 'what is this?',
        }),
        jsx(Button, {
          onClick: () => { haptic('tap'); setModal(true) },
          children: '+ New review',
        }),
      ]}),
    ]}),

    uiBuild && !uiBuild.up_to_date && jsx(UpdateCard, {
      uiBuild, onOpenPlugins: openPluginSettings }),

    modal && jsx(NewReviewModal, { ctx, onClose: () => setModal(false), onStarted: started }),

    // ── idle home ────────────────────────────────────────────────────
    !running && !result && jsx(Hero, { onStart: () => { haptic('tap'); setModal(true) } }),
    !running && !result && showExplainer && jsx(WhatYouGet, {}),

    // ── live run ─────────────────────────────────────────────────────
    running && !running.cancelled && !running.error && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsxs('div', { className: 'flex flex-col gap-2.5 rounded-xl border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) p-4', children: [
        jsxs('div', { className: 'flex flex-wrap items-end justify-between gap-2', children: [
          jsxs('div', { className: 'flex flex-col gap-0.5', children: [
            jsx(Label, { children: 'roundtable in session' }),
            jsx('div', { className: T.h1,
              children: running.progress >= 100 ? 'Closing the roundtable — writing the call' : 'The roundtable is arguing' }),
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
        jsxs('div', { className: 'grid gap-2 md:grid-cols-2', children: [
          LoudestLine({ who: loudest('against'), kind: 'against' }),
          LoudestLine({ who: loudest('for'), kind: 'for' }),
        ]}),
        jsx(LiveFloor, { events: running.events }),
      ]}),

      jsxs('div', { className: 'grid gap-3 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]', children: [
      Object.keys(running.stances || {}).length > 0 && jsxs(Card, { children: [
        jsx('div', { className: T.h2, children: 'The board, live' }),
        jsx(RoomBoard, { nodes: Object.entries(running.stances || {}).map(([name, stance]) => ({ id: name, name, stance })) }),
      ]}),

      jsxs(Card, { children: [
        jsx(Label, { children: 'change the situation' }),
        jsx('div', { className: `${T.small} text-(--ui-text-secondary)`,
          children: 'Announce a concession, publish something first, bring a champion forward. Everyone hears it before they speak next round — and the board bends where you can see it.' }),
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx(Input, {
            className: 'flex-1',
            placeholder: 'Your counter-move…',
            value: injectText, onChange: e => setInjectText(e.target.value),
            onKeyDown: e => { if (e.key === 'Enter') inject() },
          }),
          jsx(Button, { onClick: inject, children: 'Inject ⚡' }),
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
    result && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsxs('div', { className: 'flex flex-wrap items-baseline justify-between gap-2', children: [
        jsxs('div', { className: 'flex flex-col', children: [
          jsx('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: 'review' }),
          jsx('div', { className: T.h1, children: result.title || 'This review' }),
        ]}),
        jsxs('div', { className: `${T.micro} text-(--ui-text-quaternary)`, children: [
          result.createdAt ? ago(result.createdAt) : '',
          result.window ? ` · ${result.window} window` : '',
          result.personas?.length ? ` · ${result.personas.length} parties` : '',
          result.claims?.length ? ` · ${result.claims.length} claims frozen` : '',
        ]}),
      ]}),

      jsx(VerdictPanel, { result }),

      result.modelFallback && jsx(Callout, { icon: 'warning', tone: '#f5a524',
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
      jsx(MovementChartCard, { snapshots: result.snapshots }),

      jsx(Transcript, { events: result.events, rounds: result.rounds }),

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
  id: 'upfront',
  name: PRODUCT_NAME,
  defaultEnabled: false,
  register(ctx) {
    ctx.registerMany([
      { id: 'page', area: ROUTES_AREA, data: { path: '/upfront' }, render: () => jsx(UpfrontPage, { ctx }) },
      { id: 'nav', area: SIDEBAR_NAV_AREA, data: { path: '/upfront', label: PRODUCT_NAME, codicon: 'graph' } },
    ])
  },
}
