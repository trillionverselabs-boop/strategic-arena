// Upfront — desktop plugin (unified package, desktop half).
//
// Loads UNCOMPILED: no JSX. Only imports @hermes/plugin-sdk, react, react/jsx-runtime.
// Surfaces: LEFT sidebar nav row + full center page (ROUTES_AREA).
//
// Look: the app's own design language — the same atoms the Kanban board uses
// (SDK components, theme tokens, FIELD_LABEL / Section / Callout / card chrome).
// No custom colours, no hand-rolled form controls: native is the look.
//
// Flow: "+ New review" opens a dialog (title, decision or URL, evidence, timeline,
// model+cost). The run streams progress, can be injected mid-flight, and finishes
// as: competition read -> graph -> report -> frozen claims you score.

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

const BUILD = '0.4.1 · ui7'          // bump on every UI change — how you know the app reloaded
const PRODUCT_NAME = 'Upfront Prediction'   // display only — one line to rename the product

const SEA = {
  red: { label: 'Red ocean', color: '#e5484d', level: 'high', meaning: 'everyone fighting for the same fish' },
  purple: { label: 'Purple ocean', color: '#8b5cf6', level: 'medium', meaning: 'contested middle — winnable ground' },
  blue: { label: 'Blue ocean', color: '#3b82f6', level: 'low', meaning: 'open water — nobody contesting' },
}
const SEA_ORDER = ['red', 'purple', 'blue']

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

// What each kind of source actually buys you.
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

// ── atoms (the Kanban board's shared chrome) ──────────────────────────

const FIELD_LABEL = 'text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-(--ui-text-quaternary)'

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
    className: 'flex flex-col gap-2 rounded-md p-2.5',
    style: { backgroundColor: `color-mix(in srgb, ${tone} 7%, transparent)`, borderLeft: `2px solid ${tone}` },
    children: [
      jsxs('div', { className: 'flex items-start gap-1.5 text-[0.75rem] font-medium', style: { color: tone }, children: [
        jsx(Codicon, { className: 'mt-px shrink-0', name: icon, size: '0.8rem' }),
        jsx('span', { children: title }),
      ]}),
      children,
    ],
  })
}

// The board's card: elevated fill, hairline border, optional coloured left rule.
function Card({ children, className, tone }) {
  return jsx('div', {
    className: cn('flex flex-col gap-2 rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg-elevated) p-3', className),
    style: tone ? { borderLeftWidth: 2, borderLeftColor: tone } : undefined,
    children,
  })
}

function stanceColor(s) {
  if (s < -0.3) return '#e5484d'
  if (s > 0.3) return '#46a758'
  return '#f5a524'
}

// The graph is a reading aid, not decoration. Left = against the move, right =
// behind it, size = how much power that party has to stop it. Without the axis
// and the size cue the picture is just coloured dots — the number one complaint
// from the first real user.
function layoutGraph(nodes, w, h) {
  const left = 56, right = 28, top = 34, bottom = 62
  const usableW = w - left - right
  const usableH = h - top - bottom
  const sorted = [...nodes].sort((a, b) => (a.stance || 0) - (b.stance || 0))
  return sorted.map((n, i) => {
    const s = Math.max(-1, Math.min(1, Number(n.stance) || 0))
    const x = left + ((s + 1) / 2) * usableW
    const y = sorted.length === 1 ? top + usableH / 2 : top + (i / (sorted.length - 1)) * usableH
    const cap = n.capacity == null ? 0.5 : Math.max(0, Math.min(1, Number(n.capacity)))
    return { ...n, x, y, r: 10 + cap * 11, cap }
  })
}

function GraphLegend() {
  return jsxs('div', { className: 'flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.75rem] text-(#c7cdd6)', children: [
    jsxs('span', { className: 'flex items-center gap-1', children: [
      jsx('span', { className: 'inline-block h-2 w-2 rounded-full', style: { backgroundColor: '#e5484d' } }),
      'against it',
    ]}),
    jsxs('span', { className: 'flex items-center gap-1', children: [
      jsx('span', { className: 'inline-block h-2 w-2 rounded-full', style: { backgroundColor: '#f5a524' } }),
      'undecided',
    ]}),
    jsxs('span', { className: 'flex items-center gap-1', children: [
      jsx('span', { className: 'inline-block h-2 w-2 rounded-full', style: { backgroundColor: '#46a758' } }),
      'behind it',
    ]}),
    jsxs('span', { className: 'flex items-center gap-1', children: [
      jsx('span', { className: 'inline-block h-2.5 w-2.5 rounded-full border border-dashed border-(--ui-text-secondary)' }),
      'bigger = more power to stop it',
    ]}),
    jsxs('span', { className: 'flex items-center gap-1', children: [
      jsx('span', { className: 'inline-block h-2.5 w-2.5 rounded-full border-2 border-(--ui-accent)' }),
      'your side',
    ]}),
  ]})
}

function GraphCaption({ text }) {
  return jsx('div', { className: 'mb-1 text-[0.75rem] font-medium leading-snug text-(#c7cdd6)', children: text })
}

function GraphSvg({ graph, height = 340, ownSide = [] }) {
  const w = 560
  const nodes = graph?.nodes || []
  const edges = graph?.edges || []
  const placed = layoutGraph(nodes, w, height)
  const byId = Object.fromEntries(placed.map(n => [n.id, n]))
  // "your side" = the parties your own decision document names (grounded in
  // [decision ¶]), so the reader can tell who is them from who is the room.
  const own = new Set(ownSide || [])
  const labelBelow = new Set(placed.filter((n, i) => i % 2 === 0).map(n => n.id))
  // coalitions (GraphRAG-style communities) drawn as hulls, so the reader sees
  // the shape of the room rather than a bag of dots
  const hulls = (graph?.camps || [])
    .filter(c => (c.members || []).length >= 2)
    .map(c => {
      const members = placed.filter(n => (c.members || []).includes(n.name))
      if (members.length < 2) return null
      const xs = members.map(m => m.x), ys = members.map(m => m.y)
      const pad = 26
      const lean = c.lean || 'undecided'
      const color = lean === 'against' ? '#e5484d' : lean === 'for' ? '#46a758' : '#f5a524'
      return {
        key: c.name, color, lean,
        x: Math.min(...xs) - pad, y: Math.min(...ys) - pad - 12,
        w: Math.max(...xs) - Math.min(...xs) + pad * 2,
        h: Math.max(...ys) - Math.min(...ys) + pad * 2 + 12,
        label: `${c.name} — ${lean}`,
      }
    })
    .filter(Boolean)
  return jsxs('div', { className: 'flex flex-col gap-1', children: [
    jsx(GraphCaption, { text: 'Position: how much each party backs your move. Size: how much power they have to stop it. Outlined groups: coalitions that formed.' }),
    jsxs('svg', {
      viewBox: `0 0 ${w} ${height}`,
      className: 'w-full rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg)',
      children: [
        // axis
        jsx('line', { x1: 40, y1: height - 28, x2: w - 16, y2: height - 28,
          style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1.5 } }),
        jsx('line', { x1: 40, y1: height - 33, x2: 40, y2: height - 23,
          style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1.5 } }),
        jsx('line', { x1: w / 2, y1: height - 33, x2: w / 2, y2: height - 23,
          style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1.5 } }),
        jsx('line', { x1: w - 16, y1: height - 33, x2: w - 16, y2: height - 23,
          style: { stroke: 'var(--ui-stroke-tertiary)', strokeWidth: 1.5 } }),
        jsx('text', { x: 40, y: height - 10, textAnchor: 'start', fontSize: '12', fontWeight: 600,
          style: { fill: '#c7cdd6' }, children: 'against' }),
        jsx('text', { x: w / 2, y: height - 10, textAnchor: 'middle', fontSize: '12', fontWeight: 600,
          style: { fill: '#c7cdd6' }, children: 'neutral' }),
        jsx('text', { x: w - 16, y: height - 10, textAnchor: 'end', fontSize: '12', fontWeight: 600,
          style: { fill: '#c7cdd6' }, children: 'behind it' }),
        ...hulls.map(hl => jsxs('g', { key: `hull-${hl.key}`, children: [
          jsx('rect', { x: hl.x, y: hl.y, width: hl.w, height: hl.h, rx: 12,
            style: { fill: hl.color, opacity: 0.07, stroke: hl.color, strokeWidth: 1.2, strokeDasharray: '3 3' } }),
          jsx('text', { x: hl.x + 8, y: hl.y + 12, fontSize: '9',
            style: { fill: hl.color } }, hl.label),
        ]})),
        ...edges.map((e, i) => {
          const a = byId[e.from], b = byId[e.to]
          if (!a || !b) return null
          return jsx('line', {
            key: `e${i}`, x1: a.x, y1: a.y, x2: b.x, y2: b.y,
            style: {
              stroke: 'var(--ui-border)', strokeWidth: 1.5,
              strokeDasharray: e.label === 'opposes' ? '4 3' : undefined,
            },
          })
        }),
        ...placed.map(n => jsxs('g', {
          key: n.id,
          children: [
            own.has(n.name) && jsx('circle', { cx: n.x, cy: n.y, r: n.r + 4, fill: 'none',
              style: { stroke: 'var(--ui-accent)', strokeWidth: 2 } }),
            jsx('circle', { cx: n.x, cy: n.y, r: n.r, fill: stanceColor(n.stance), opacity: 0.92 }),
            jsx('text', { x: n.x, y: n.y + 3, textAnchor: 'middle', fontSize: '10', fill: '#fff',
              children: `${n.stance >= 0 ? '+' : ''}${(n.stance || 0).toFixed(1)}` }),
            jsx('text', {
              x: n.x, y: labelBelow.has(n.id) ? n.y + n.r + 15 : n.y - n.r - 7,
              textAnchor: 'middle', fontSize: '12.5', fontWeight: 600,
              style: { fill: '#f2f4f7', paintOrder: 'stroke',
                       stroke: 'rgba(5,7,10,.85)', strokeWidth: 3.5,
                       strokeLinejoin: 'round' }, children: n.name,
            }),
          ],
        })),
      ],
    }),
    jsx(GraphLegend, {}),
  ]})
}

function SeaAxis({ sea }) {
  if (!sea || !sea.state) return null
  // Off-axis states (currently 'insufficient') are not a point on the competition
  // scale — they are the absence of a read. Show the reason, not unlit pills.
  if (!SEA_ORDER.includes(sea.state)) {
    return jsxs('div', { className: 'flex items-center gap-2', children: [
      jsx('span', { className: FIELD_LABEL, children: 'competition' }),
      jsx(Badge, { variant: 'muted', title: sea.why || '', children: sea.label || 'insufficient input' }),
      sea.why && jsx('span', { className: 'text-[0.75rem] text-(--ui-text-secondary)', children: sea.why }),
    ]})
  }
  const idx = SEA_ORDER.indexOf(sea.state)
  return jsxs('div', { className: 'flex items-center gap-2', children: [
    jsx('span', { className: FIELD_LABEL, children: 'competition' }),
    jsxs('div', {
      className: 'relative h-2 w-36 rounded-full',
      style: { background: 'linear-gradient(90deg, #e5484d 0%, #8b5cf6 50%, #3b82f6 100%)' },
      children: [
        jsx('div', {
          className: 'absolute h-3.5 w-3.5 rounded-full border-2 border-white shadow',
          style: {
            top: '50%', transform: 'translateY(-50%)',
            left: `calc(${idx / (SEA_ORDER.length - 1) * 100}% - 7px)`,
            backgroundColor: SEA[sea.state].color,
          },
        }),
      ],
    }),
    jsx(Badge, { variant: 'outline', style: { color: SEA[sea.state].color, borderColor: 'transparent' }, children: sea.label }),
  ]})
}

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
    if (ln.startsWith('# ')) return jsx('div', { key, className: 'text-lg font-semibold', children: inline(ln.slice(2)) })
    if (ln.startsWith('> ')) return jsx('div', { key, className: 'border-l-2 border-(--ui-stroke-tertiary) pl-2 text-(--ui-text-tertiary)', children: inline(ln.slice(2)) })
    if (ln.startsWith('- ')) return jsx('div', { key, className: 'pl-3', children: inline(`• ${ln.slice(2)}`) })
    if (!ln.trim()) return jsx('div', { key, className: 'h-1' })
    return jsx('div', { key, children: inline(ln) })
  }) })
}

function FrictionBar({ friction, color }) {
  const pct = Math.max(0, Math.min(100, Number(friction) || 0))
  const c = color || 'var(--ui-accent)'
  return jsxs('div', { className: 'flex items-center gap-2', children: [
    jsxs('div', { className: 'relative h-2.5 w-44 overflow-hidden rounded-full bg-(--ui-bg-quaternary)', children: [
      jsx('div', { className: 'h-full rounded-full', style: { width: `${pct}%`, backgroundColor: c } }),
      jsx('div', { className: 'absolute inset-y-0 left-1/2 w-px bg-(--ui-stroke-secondary)' }),
    ]}),
    jsx('span', { className: 'text-xs tabular-nums text-(--ui-text-secondary)', children: `${pct.toFixed(0)}/100` }),
  ]})
}

// ── plain-language reading of the numbers ─────────────────────────────
// A number with no sentence next to it is noise. Every metric on the result
// page gets one line that says what it means and why it matters.

function frictionMeaning(f) {
  const n = Number(f) || 0
  if (n < 20) return 'A quiet room. Most parties who matter are behind this, or nobody with power has engaged. Low friction is good — it is also why you should check the claims later rather than trust it today.'
  if (n < 45) return 'A real contest with winnable ground. Somebody objects, but nobody is dug in. This is where a good counter-move changes the outcome.'
  if (n < 65) return 'A fight. At least one party is working against you with the power to make it cost. Expect a hard conversation before this lands.'
  return 'A brawl. Multiple parties are against it and at least one can stop it. Do not launch on this read — talk to the objectors first.'
}

function powerMeaning(cap) {
  if (cap == null) return 'Power to stop it: not stated in your documents'
  const n = Number(cap)
  if (n >= 0.7) return 'Power to stop it: high — they can block or materially change this'
  if (n >= 0.4) return 'Power to stop it: real — they can slow it or extract a price'
  return 'Power to stop it: low — they can complain, not stop it'
}

function VerdictCard({ result }) {
  const sea = result.sea
  const blocker = result.personas?.find(p => p.name === result.blocker) || null
  return jsxs(Card, { tone: 'var(--ui-accent)', children: [
    jsx('div', { className: FIELD_LABEL, children: 'What the rehearsal found' }),
    jsxs('div', { className: 'mt-1 flex flex-wrap items-center gap-3', children: [
      sea && jsx(SeaAxis, { sea }),
      result.friction != null && jsxs('span', { className: 'flex items-center gap-2', children: [
        jsx(FrictionBar, { friction: result.friction, color: sea ? sea.color : 'var(--ui-accent)' }),
        jsx('span', { className: 'text-sm font-semibold tabular-nums', children: `${result.friction}/100` }),
      ]}),
    ]}),
    sea && jsxs('p', { className: 'mt-1 text-[0.75rem] leading-snug text-(--ui-text-secondary)', children: [
      jsx('strong', { children: sea.label + '. ' }),
      sea.meaning + ' ',
      jsx('span', { className: 'text-(--ui-text-tertiary)', children: sea.why || '' }),
    ]}),
    result.friction != null && jsx('p', { className: 'mt-1 text-[0.75rem] leading-snug text-(#c7cdd6)',
      children: frictionMeaning(result.friction) }),

    // who can actually stop it — the sentence the reader came for
    jsxs('div', { className: 'mt-3 border-t border-(--ui-stroke-tertiary) pt-2', children: [
      jsx('div', { className: FIELD_LABEL, children: 'Who can challenge this' }),
      blocker
        ? jsxs('div', { className: 'mt-0.5', children: [
            jsxs('div', { className: 'text-sm font-semibold', children: [
              blocker.name,
              jsx('span', { className: 'ml-2 text-xs font-normal text-(--ui-text-tertiary)',
                children: `${blocker.stance >= 0 ? '+' : ''}${Number(blocker.stance).toFixed(2)}` }),
            ]}),
            jsx('div', { className: 'text-[0.75rem] text-(--ui-text-secondary)',
              children: blocker.reasons?.[0] ? `Their condition: ${blocker.reasons[0]}` : 'No reason recorded.' }),
            jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: powerMeaning(blocker.capacity) }),
          ]})
        : jsxs('div', { className: 'mt-0.5', children: [
            jsx('div', { className: 'text-sm font-semibold', children: 'Nobody in this room can stop it.' }),
            jsx('div', { className: 'text-[0.75rem] text-(--ui-text-secondary)',
              children: (sea && sea.why) || 'No party was found who could contest this move.' }),
          ]}),
    ]}),

    result.recommendation && jsxs('div', { className: 'mt-3 border-t border-(--ui-stroke-tertiary) pt-2', children: [
      jsx('div', { className: FIELD_LABEL, children: 'So what do I do' }),
      jsx('div', { className: 'mt-0.5 text-[0.8125rem] leading-snug', children: result.recommendation }),
    ]}),

    result.counter_moves?.length > 0 && jsxs('div', { className: 'mt-2 flex flex-col gap-1', children: [
      jsx('div', { className: FIELD_LABEL, children: 'Best response' }),
      ...result.counter_moves.map((m, i) => jsx('div', { key: `cm${i}`,
        className: 'pl-2 text-[0.75rem] leading-snug text-(--ui-text-secondary)', children: `• ${m}` })),
    ]}),

    result.interventions?.length > 0 && jsx('div', { className: 'mt-2 text-[0.6875rem] text-(--ui-text-tertiary)',
      children: `Mid-run moves you made: ${result.interventions.join(' · ')}` }),
  ]})
}

// ── "what you get" explainer ──────────────────────────────────────────

function WhatYouGet() {
  return jsxs(Callout, {
    icon: 'info',
    tone: 'var(--ui-accent)',
    title: 'What you get back — and what you do not',
    children: [
      jsx('div', { className: 'text-[0.75rem] leading-snug', children: 'A structured review of the response to your move: who can veto it, which coalitions form, the best response, and how contested the ground is.' }),
      jsx('div', { className: 'text-[0.75rem] leading-snug text-(--ui-text-secondary)', children: 'Not a prediction of the future and not a guarantee. It is rehearsal: it finds the fight before you are in it, and it freezes its calls so you can score them later.' }),
      jsx('div', { className: 'text-[0.6875rem] leading-snug text-(--ui-text-tertiary)', children: 'Use it to decide whether to launch, who to talk to first, which objection to answer, and whether the pushback is a real fight or just noise.' }),
    ],
  })
}

// ── new review dialog (mirrors Kanban's new-task dialog) ──────────────

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
  const [note, setNote] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState('')

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
  const cost = !chosen ? 'your active model' : chosen.free ? 'FREE' : `~$${(calls * perCall).toFixed(3)} at list price`
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
              hint: 'Leave on active model to use whatever Hermes already runs. Free models cost nothing but have rate limits.',
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

          // free models are the default here and they are SLOW — say so before
          // the user commits 30 minutes to a 24h review with no explanation
          chosen?.free && jsx(Callout, { icon: 'info', tone: 'var(--ui-accent)',
            title: 'Free models are rate-limited and slow',
            children: `Expect roughly ${tl.eta} for this timeline, sometimes more. A 30-minute run is a fast sanity check; 24 hours is the full reaction cycle.` }),

          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: `${calls} model calls · ${cost}${note ? ' · ' + note : ''}` }),
          jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: 'For a first pass: a flash-class model at 24h. Spend on 48h and a bigger model only when the decision is expensive.' }),

          jsx(WhatYouGet, {}),

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
      jsx('div', { className: 'text-sm font-medium', children: `Same decision across timelines — ${cmp.runs} run(s)` }),
      jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)',
        children: cmp.friction_spread != null ? `friction spread ${cmp.friction_spread} · veto ${cmp.blocker_stable ? 'stable' : 'changed'}` : '' }),
    ]}),
    jsx('div', { className: 'text-xs text-(--ui-text-secondary)', children: cmp.reading }),
    jsxs('div', { className: 'flex flex-col gap-1', children: [
      jsxs('div', { className: 'grid grid-cols-5 gap-2 text-[0.6875rem] uppercase tracking-wide text-(--ui-text-tertiary)', children: [
        jsx('span', { children: 'timeline' }), jsx('span', { children: 'friction' }),
        jsx('span', { children: 'competition' }), jsx('span', { children: 'veto player' }), jsx('span', { children: 'scored' }),
      ]}),
      ...cmp.rows.map(r => jsxs('div', {
        key: r.run_id,
        className: 'grid grid-cols-5 items-center gap-2 text-xs',
        children: [
          jsx('span', { children: `${r.rounds ?? '?'} rounds` }),
          jsx(FrictionBar, { friction: r.friction, color: SEA[r.sea_state] ? SEA[r.sea_state].color : 'var(--ui-accent)' }),
          jsx('span', { children: r.sea_label || '—' }),
          jsx('span', { children: r.blocker || 'none' }),
          jsx('span', { children: r.verified && r.verified.verdict ? r.verified.verdict : '—' }),
        ],
      })),
    ]}),
  ]})
}

// ── one run row (shared by Recent and Past reviews) ─────────────────

function RunRow({ h, onOpen }) {
  return jsxs(Button, {
    variant: 'ghost',
    className: 'h-auto w-full justify-start gap-3 px-2 py-1.5 text-left font-normal',
    onClick: () => onOpen(h.run_id, h.title),
    children: [
      jsx('span', { className: 'size-2 shrink-0 rounded-full', style: { backgroundColor: SEA[h.sea_state] ? SEA[h.sea_state].color : '#555' } }),
      jsx('span', { className: 'flex-1 truncate text-[0.8125rem]', children: h.title }),
      jsx('span', { className: 'text-[0.6875rem] tabular-nums text-(--ui-text-tertiary)', children: h.rounds ? `${h.rounds} rounds` : '' }),
      jsx('span', { className: 'text-[0.6875rem] tabular-nums text-(--ui-text-tertiary)', children: h.friction != null ? `friction ${h.friction}` : '' }),
      jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: h.verified && h.verified.verdict ? h.verified.verdict : '' }),
    ],
  })
}

// ── page ──────────────────────────────────────────────────────────────

function UpfrontPage({ ctx }) {
  const [modal, setModal] = React.useState(false)
  const [running, setRunning] = React.useState(null)
  const [result, setResult] = React.useState(null)
  const [history, setHistory] = React.useState([])
  const [compare, setCompare] = React.useState(null)
  const [showCompare, setShowCompare] = React.useState(true)
  const [claimHits, setClaimHits] = React.useState({})
  const [injectText, setInjectText] = React.useState('')
  const [lastEdges, setLastEdges] = React.useState([])
  const [showAudit, setShowAudit] = React.useState(false)
  const [showAllClaims, setShowAllClaims] = React.useState(false)
  const [injectHint, setInjectHint] = React.useState('')
  const [injectImpact, setInjectImpact] = React.useState('')
  const [startedAt, setStartedAt] = React.useState(null)
  const injectBaseline = React.useRef(null)
  const gateway = useValue(host.state.gateway)

  function refreshHistory() {
    ctx.rest('/history').then(setHistory).catch(() => {})
  }
  React.useEffect(() => { refreshHistory() }, [])

  async function openRun(runId, titleHint) {
    const [rep, g, cl] = await Promise.all([
      ctx.rest(`/report/${runId}`).catch(() => ({ report: '' })),
      ctx.rest(`/graph/${runId}`).catch(() => ({ nodes: [], edges: [] })),
      ctx.rest(`/claims/${runId}`).catch(() => ({ claims: [] })),
    ])
    let meta = {}
    try { meta = (await ctx.rest('/history')).find(h => h.run_id === runId) || {} } catch (_) {}
    setResult({
      runId, report: rep.report, graph: g, claims: cl.claims || [],
      sea: meta.sea_state ? { state: meta.sea_state, label: meta.sea_label, color: meta.sea_color,
                             why: meta.sea_why, meaning: SEA[meta.sea_state] ? SEA[meta.sea_state].meaning : '' } : null,
      friction: meta.friction, blocker: meta.blocker, blockerStance: meta.blocker_stance,
      recommendation: rep.recommendation, summary: rep.summary,
      counterMoves: rep.counter_moves, personas: rep.personas,
      interventions: rep.interventions, verified: meta.verified,
      // "your side": parties grounded in the decision document itself
      ownSide: (rep.personas || []).filter(p => (p.reasons?.[0] || '').includes('[decision')).map(p => p.name),
    })
    setClaimHits({})
    setShowAudit(false)
    setShowAllClaims(false)
    setInjectImpact('')
    setLastEdges(g?.edges || [])
    const t = titleHint || meta.title
    if (t) ctx.rest(`/compare?title=${encodeURIComponent(t)}`).then(setCompare).catch(() => {})
  }

  function started(runId) {
    setModal(false)
    setResult(null)
    setRunning({ runId, progress: 0, round: 0, total: 0, stances: {} })
    setStartedAt(Date.now())
    setInjectImpact('')
    setInjectHint('')
    injectBaseline.current = null
    const iv = setInterval(async () => {
      const st = await ctx.rest(`/status/${runId}`).catch(() => null)
      if (!st) return
      // what did the injection actually do? compare to the stances at that moment
      if (injectBaseline.current && st.stances) {
        const base = injectBaseline.current
        const movers = Object.keys(st.stances)
          .map(k => ({ name: k, d: (st.stances[k] || 0) - (base[k] || 0) }))
          .filter(m => Math.abs(m.d) >= 0.05)
          .sort((a, b) => Math.abs(b.d) - Math.abs(a.d))
        if (movers.length) {
          setInjectImpact(`Injected ✓ — ${movers.slice(0, 3)
            .map(m => `${m.name} ${m.d > 0 ? '+' : ''}${m.d.toFixed(1)}`).join(' · ')}`)
        }
      }
      setRunning({ runId, progress: st.progress || 0, round: st.round || 0,
        total: st.total || 0, stances: st.stances || {} })
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
    }, 800)
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
    injectBaseline.current = { ...running.stances }
    setInjectHint('')
    setInjectImpact('Injected — watch the dots move over the next round.')
    await ctx.rest(`/inject/${running.runId}`, {
      method: 'POST', body: { name: 'Counter-move', description: injectText },
    }).catch(() => {})
    setInjectText('')
  }

  async function verify(verdict) {
    if (!result) return
    await ctx.rest(`/verify/${result.runId}`, { method: 'POST', body: { verdict, hits: claimHits } }).catch(() => {})
    refreshHistory()
  }

  const liveGraph = React.useMemo(() => {
    const nodes = Object.entries(running?.stances || {}).map(([name, stance]) => ({ id: name, name, stance }))
    if (!nodes.length) return null
    return { nodes, edges: lastEdges }
  }, [running?.stances, lastEdges])

  // the party currently most against it — a running narrative beats a bare number
  function loudestObjector() {
    const entries = Object.entries(running?.stances || {})
    if (!entries.length) return null
    const [name, stance] = entries.reduce((a, b) => (b[1] < a[1] ? b : a), entries[0])
    return { name, stance }
  }

  const recent = history.slice(0, 2)

  return jsxs('div', { className: 'flex h-full flex-col gap-3 overflow-auto p-4', children: [
    // header
    jsxs('div', { className: 'flex items-center justify-between', children: [
      jsxs('div', { className: 'flex flex-col', children: [
        jsx('div', { className: 'text-lg font-semibold', children: PRODUCT_NAME }),
        jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)',
          children: `strategic-response review · gateway: ${gateway} · build ${BUILD}` }),
      ]}),
      jsx(Button, {
        onClick: () => { haptic('tap'); setModal(true) },
        children: '+ New review',
      }),
    ]}),

    modal && jsx(NewReviewModal, { ctx, onClose: () => setModal(false), onStarted: started }),

    // live run
    running && !running.error && jsxs(Card, { children: [
      jsxs('div', { className: 'flex items-center justify-between', children: [
        jsx('div', { className: 'text-sm font-medium',
          children: running.progress >= 100 ? 'Finishing — writing the report' : 'Review in progress' }),
        jsx('div', { className: 'text-xs font-medium text-(#c7cdd6)',
          children: running.total ? `Round ${running.round} of ${running.total} — ${running.progress}%` : `${running.progress}%` }),
      ]}),
      jsxs('div', { className: 'text-[0.75rem] text-(#c7cdd6)', children: [
        startedAt ? `Started ${Math.max(1, Math.round((Date.now() - startedAt) / 60000))} min ago` : '',
        loudestObjector() ? ` · loudest objector: ${loudestObjector().name} (${loudestObjector().stance >= 0 ? '+' : ''}${loudestObjector().stance.toFixed(1)})` : '',
        running.progress >= 100 ? ' · nearly there' : '',
      ]}),
      jsxs('div', { className: 'h-2 w-full overflow-hidden rounded-full bg-(--ui-bg-quaternary)', children: [
        jsx('div', { className: 'h-full rounded-full bg-primary transition-all', style: { width: `${running.progress}%` } }),
      ]}),
      liveGraph && jsx(GraphSvg, { graph: liveGraph, height: 320 }),
      jsxs('div', { className: 'flex items-center gap-2', children: [
        jsx(Input, {
          className: 'flex-1',
          placeholder: 'Inject a counter-move mid-run — e.g. "Publish the eval suite first"',
          value: injectText, onChange: e => setInjectText(e.target.value),
        }),
        jsx(Button, { onClick: inject, children: 'Inject ⚡' }),
      ]}),
      jsx('div', { className: 'flex items-center justify-between gap-2', children: [
        jsx('div', { className: 'text-[0.75rem] leading-snug text-(--ui-text-secondary)',
          children: 'Change the situation while it runs — announce a concession, publish something first, bring a champion forward. The dots move next round.' }),
        jsx(Button, { size: 'xs', variant: 'outline', onClick: cancelRun, children: 'Cancel run' }),
      ]}),
      injectHint && jsx('div', { className: 'text-[0.75rem] text-(#f5a524)', children: injectHint }),
      injectImpact && jsx('div', { className: 'text-[0.75rem] text-(--ui-text-secondary)', children: injectImpact }),
    ]}),
    running && running.cancelled && jsx(Callout, { icon: 'info', tone: 'var(--ui-accent)',
      title: 'Run cancelled',
      children: 'Stopped before it finished — nothing was written to your Past reviews, so your history only ever holds complete runs.' }),

    running && running.error && jsx(Callout, { icon: 'error', tone: 'var(--destructive)', title: 'Run failed', children: running.error }),

    // finished result — the "so what" comes first; the audit is behind a toggle
    result && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsx(VerdictCard, { result }),

      jsxs('div', { className: 'grid grid-cols-2 gap-3', children: [
        jsxs(Card, { children: [
          jsx('div', { className: 'mb-1 text-sm font-medium', children: 'The room, after the run' }),
          jsx(GraphSvg, { graph: result.graph, ownSide: result.ownSide }),
        ]}),
        jsxs(Card, { children: [
          jsx('div', { className: 'mb-1 text-sm font-medium', children: 'The parties, and why they stand where they do' }),
          jsx('div', { className: 'flex max-h-[420px] flex-col gap-2 overflow-auto pr-1', children:
            (result.personas || []).slice().sort((a, b) => a.stance - b.stance).map(p => jsxs('div', {
              className: 'border-b border-(--ui-stroke-tertiary) pb-1.5',
              children: [
                jsxs('div', { className: 'flex items-center justify-between gap-2', children: [
                  jsx('span', { className: 'text-xs font-medium', children: p.name }),
                  jsx('span', { className: 'text-[0.6875rem] tabular-nums',
                    style: { color: stanceColor(p.stance) },
                    children: `${p.stance >= 0 ? '+' : ''}${Number(p.stance).toFixed(2)}` }),
                ]}),
                p.reasons?.[0] && jsx('div', { className: 'text-[0.75rem] leading-snug text-(#c7cdd6)',
                  children: p.reasons[0] }),
              ],
            })) }),
        ]}),
      ]}),

      result.claims && result.claims.length > 0 && jsxs(Card, { children: [
        jsx('div', { className: 'text-sm font-medium', children: 'Score the claims — did the review call it?' }),
        jsx('div', { className: 'text-[0.75rem] text-(#c7cdd6)',
          children: 'These were frozen when the run finished. Mark each right or wrong when the window closes — that is how the rehearsal gets better.' }),
        ...(showAllClaims ? result.claims : result.claims.slice(0, 4)).map(c => jsxs('div', { key: c.id, className: 'mt-1 flex items-start gap-2 text-xs', children: [
          jsx('span', { className: 'flex-1 text-(--ui-text-secondary)', children: c.claim }),
          jsx(Button, {
            size: 'xs',
            variant: claimHits[c.id] === true ? 'secondary' : 'outline',
            onClick: () => setClaimHits({ ...claimHits, [c.id]: true }),
            children: '✓',
          }),
          jsx(Button, {
            size: 'xs',
            variant: claimHits[c.id] === false ? 'destructive' : 'outline',
            onClick: () => setClaimHits({ ...claimHits, [c.id]: false }),
            children: '✗',
          }),
        ]})),
        result.claims.length > 4 && jsx(Button, {
          size: 'xs', variant: 'ghost', className: 'self-start',
          onClick: () => setShowAllClaims(!showAllClaims),
          children: showAllClaims ? 'show fewer' : `show all ${result.claims.length} claims`,
        }),
        jsxs('div', { className: 'flex items-center gap-2 pt-1', children: [
          jsx('span', { className: 'text-xs text-(--ui-text-tertiary)', children: 'overall verdict:' }),
          ...['right', 'partial', 'wrong'].map(v => jsx(Button, {
            key: v, size: 'xs', variant: 'outline',
            onClick: () => verify(v), children: v,
          })),
        ]}),
      ]}),

      // the audit is for the people who want it, not for the reader who wants the answer
      result.report && jsxs('div', { className: 'flex flex-col gap-1', children: [
        jsx(Button, {
          size: 'xs', variant: 'ghost', className: 'self-start',
          onClick: () => setShowAudit(!showAudit),
          children: showAudit ? 'hide the full audit (stakeholders, provenance, round log)'
                             : 'show the full audit (stakeholders, provenance, round log)',
        }),
        showAudit && jsx(Card, { className: 'max-h-[480px] overflow-auto',
          children: jsx(Markdown, { text: result.report }) }),
      ]}),
    ]}),

    compare && showCompare && jsxs('div', { className: 'flex flex-col gap-1', children: [
      jsx(ComparePanel, { cmp: compare }),
      jsx(Button, { size: 'xs', variant: 'ghost', className: 'self-start',
        onClick: () => setShowCompare(false), children: 'hide comparison' }),
    ]}),

    // recent — the two latest runs, above the full list
    recent.length > 0 && jsxs(Card, { tone: 'var(--ui-accent)', children: [
      jsxs('div', { className: 'flex items-center justify-between', children: [
        jsx('div', { className: 'text-sm font-medium', children: 'Recent' }),
        jsx('div', { className: 'text-[0.6875rem] text-(--ui-text-tertiary)', children: 'latest 2 runs' }),
      ]}),
      ...recent.map(h => jsx(RunRow, { key: h.run_id, h, onOpen: openRun })),
    ]}),

    // history
    jsxs(Card, { children: [
      jsx('div', { className: 'text-sm font-medium', children: 'Past reviews' }),
      history.length === 0
        ? jsx('div', { className: 'py-2 text-sm text-(--ui-text-tertiary)', children: 'No runs yet — press + New review.' })
        : history.map(h => jsx(RunRow, { key: h.run_id, h, onOpen: openRun })),
    ]}),
  ]})
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
