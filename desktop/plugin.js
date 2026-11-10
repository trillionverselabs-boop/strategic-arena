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

const BUILD = '0.3.2 · ui3'          // bump on every UI change — how you know the app reloaded
const PRODUCT_NAME = 'Upfront'        // display only — one line to rename the product

const SEA = {
  red: { label: 'Red ocean', color: '#e5484d', level: 'high', meaning: 'everyone fighting for the same fish' },
  purple: { label: 'Purple ocean', color: '#8b5cf6', level: 'medium', meaning: 'contested middle — winnable ground' },
  blue: { label: 'Blue ocean', color: '#3b82f6', level: 'low', meaning: 'open water — nobody contesting' },
}
const SEA_ORDER = ['red', 'purple', 'blue']

const TIMELINES = [
  { v: '30m', label: '30 minutes', rounds: 3, note: 'Sanity check — does anyone care at all? Cheapest.' },
  { v: '1h', label: '1 hour', rounds: 5, note: 'First reactions only. Good for a fast no.' },
  { v: '4h', label: '4 hours', rounds: 8, note: 'Positions form. Catches the obvious blocker.' },
  { v: '6h', label: '6 hours', rounds: 10, note: 'Coalitions start to show.' },
  { v: '12h', label: '12 hours', rounds: 12, note: 'Counter-moves get tested.' },
  { v: '24h', label: '24 hours', rounds: 16, note: 'Recommended. Full reaction cycle.' },
  { v: '48h', label: '48 hours', rounds: 20, note: 'Deepest read — hard to move a veto player. ~2x cost.' },
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

const SAMPLE = {
  title: 'Open-weight Arete-27B',
  decision:
    'Nous is considering open-weighting Arete-27B. The weights ship under a permissive licence ' +
    'on release day, with the full training data and eval suite published alongside. The hosted ' +
    'API stays free for the first 90 days so people can try it before committing.',
  evidence:
    'Q2 survey of 400 enterprise CIOs: 61% said they cannot route inference through an external ' +
    'API for compliance reasons. Open-weight model downloads tripled quarter over quarter, and ' +
    'community fine-tunes now outnumber closed-model adaptations 3:1. Enterprises want weights ' +
    'on-prem; the community wants the training data; nobody wants a licence that forbids ' +
    'commercial use.',
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

function layoutGraph(nodes, w, h) {
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) / 2 - 50
  return nodes.map((n, i) => {
    const a = (i / Math.max(1, nodes.length)) * Math.PI * 2 - Math.PI / 2
    return { ...n, x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) }
  })
}

function GraphSvg({ graph, height = 420 }) {
  const w = 560
  const nodes = graph?.nodes || []
  const edges = graph?.edges || []
  const placed = layoutGraph(nodes, w, height)
  const byId = Object.fromEntries(placed.map(n => [n.id, n]))
  return jsxs('svg', {
    viewBox: `0 0 ${w} ${height}`,
    className: 'w-full rounded-md border border-(--ui-stroke-tertiary) bg-(--ui-bg)',
    children: [
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
          jsx('circle', { cx: n.x, cy: n.y, r: 16, fill: stanceColor(n.stance), opacity: 0.9 }),
          jsx('text', { x: n.x, y: n.y + 30, textAnchor: 'middle', fontSize: '11',
            style: { fill: 'var(--ui-text)' }, children: n.name }),
          jsx('text', { x: n.x, y: n.y + 3, textAnchor: 'middle', fontSize: '10', fill: '#fff',
            children: `${n.stance >= 0 ? '+' : ''}${(n.stance || 0).toFixed(1)}` }),
        ],
      })),
    ],
  })
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
              hint: tl.note,
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
      sea: meta.sea_state ? { state: meta.sea_state, label: meta.sea_label, color: meta.sea_color, why: meta.sea_why } : null,
      friction: meta.friction, blocker: meta.blocker, verified: meta.verified,
    })
    setClaimHits({})
    setLastEdges(g?.edges || [])
    const t = titleHint || meta.title
    if (t) ctx.rest(`/compare?title=${encodeURIComponent(t)}`).then(setCompare).catch(() => {})
  }

  function started(runId) {
    setModal(false)
    setResult(null)
    setRunning({ runId, progress: 0, round: 0, total: 0, stances: {} })
    const iv = setInterval(async () => {
      const st = await ctx.rest(`/status/${runId}`).catch(() => null)
      if (!st) return
      setRunning({ runId, progress: st.progress || 0, round: st.round || 0,
        total: st.total || 0, stances: st.stances || {} })
      if (st.status === 'done') {
        clearInterval(iv)
        setRunning(null)
        refreshHistory()
        await openRun(runId)
      } else if (st.status === 'failed') {
        clearInterval(iv)
        setRunning({ runId, progress: 0, error: st.error || 'failed' })
      }
    }, 800)
  }

  async function inject() {
    if (!injectText.trim() || !running) return
    haptic('tap')
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
        jsx('div', { className: 'text-sm font-medium', children: 'Review in progress' }),
        jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
          children: running.total ? `Round ${running.round} of ${running.total} — ${running.progress}%` : `${running.progress}%` }),
      ]}),
      jsxs('div', { className: 'h-2 w-full overflow-hidden rounded-full bg-(--ui-bg-quaternary)', children: [
        jsx('div', { className: 'h-full rounded-full bg-primary transition-all', style: { width: `${running.progress}%` } }),
      ]}),
      liveGraph && jsx(GraphSvg, { graph: liveGraph, height: 300 }),
      jsxs('div', { className: 'flex items-center gap-2', children: [
        jsx(Input, {
          className: 'flex-1',
          placeholder: 'Inject a counter-move mid-run — e.g. "Publish the eval suite first"',
          value: injectText, onChange: e => setInjectText(e.target.value),
        }),
        jsx(Button, { disabled: !injectText.trim(), onClick: inject, children: 'Inject ⚡' }),
      ]}),
    ]}),
    running && running.error && jsx(Callout, { icon: 'error', tone: 'var(--destructive)', title: 'Run failed', children: running.error }),

    // finished result
    result && jsxs('div', { className: 'flex flex-col gap-3', children: [
      jsxs(Card, { children: [
        jsx('div', { className: FIELD_LABEL, children: 'Competition read' }),
        jsxs('div', { className: 'flex flex-wrap items-center gap-3', children: [
          jsx(SeaAxis, { sea: result.sea }),
          result.friction != null && jsx(FrictionBar, { friction: result.friction, color: result.sea ? result.sea.color : 'var(--ui-accent)' }),
          result.blocker && jsx('span', { className: 'text-xs text-(--ui-text-secondary)', children: `veto player: ${result.blocker}` }),
        ]}),
      ]}),
      jsxs('div', { className: 'grid grid-cols-2 gap-3', children: [
        jsx(Card, { children: jsx(GraphSvg, { graph: result.graph }) }),
        jsx(Card, { className: 'max-h-[520px] overflow-auto', children: jsx(Markdown, { text: result.report }) }),
      ]}),
      result.claims && result.claims.length > 0 && jsxs(Card, { children: [
        jsx('div', { className: 'text-sm font-medium', children: 'Score the claims — did the review call it?' }),
        ...result.claims.map(c => jsxs('div', { key: c.id, className: 'flex items-start gap-2 text-xs', children: [
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
        jsxs('div', { className: 'flex items-center gap-2 pt-1', children: [
          jsx('span', { className: 'text-xs text-(--ui-text-tertiary)', children: 'overall verdict:' }),
          ...['right', 'partial', 'wrong'].map(v => jsx(Button, {
            key: v, size: 'xs', variant: 'outline',
            onClick: () => verify(v), children: v,
          })),
        ]}),
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
