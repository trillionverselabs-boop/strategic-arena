// Upfront — desktop plugin (unified package, desktop half).
//
// Loads UNCOMPILED: no JSX. Only imports @hermes/plugin-sdk, react, react/jsx-runtime.
// Surface: LEFT sidebar nav row + full center page (ROUTES_AREA).
// The page POSTs to /api/plugins/upfront/run, polls /status/{id} for live stances,
// can inject a counter-move mid-run, then renders the graph, the report, and the
// frozen claims you score later.

import { host, haptic, useValue, ROUTES_AREA, SIDEBAR_NAV_AREA } from '@hermes/plugin-sdk'
import React from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const BUILD = '0.2.0 · gapfix'        // bump on every UI change — how you know the app reloaded
const PRODUCT_NAME = 'Upfront'         // display only — one line to rename the product

const SEA = {
  red: { label: 'Red ocean', color: '#e5484d', level: 'high', meaning: 'everyone fighting for the same fish' },
  purple: { label: 'Purple ocean', color: '#8b5cf6', level: 'medium', meaning: 'contested middle — winnable ground' },
  blue: { label: 'Blue ocean', color: '#3b82f6', level: 'low', meaning: 'open water — nobody contesting' },
}
const SEA_ORDER = ['red', 'purple', 'blue']   // left = high competition, right = low

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

function GraphSvg({ graph }) {
  const w = 560, h = 420
  const nodes = graph?.nodes || []
  const edges = graph?.edges || []
  const placed = layoutGraph(nodes, w, h)
  const byId = Object.fromEntries(placed.map(n => [n.id, n]))
  return jsxs('svg', {
    viewBox: `0 0 ${w} ${h}`,
    className: 'w-full rounded border border-(--ui-border) bg-(--ui-bg)',
    children: [
      ...edges.map((e, i) => {
        const a = byId[e.from], b = byId[e.to]
        if (!a || !b) return null
        return jsx('line', {
          key: `e${i}`, x1: a.x, y1: a.y, x2: b.x, y2: b.y,
          stroke: 'var(--ui-border)', strokeWidth: 1.5,
          strokeDasharray: e.label === 'opposes' ? '4 3' : undefined,
        })
      }),
      ...placed.map(n => jsxs('g', {
        key: n.id,
        children: [
          jsx('circle', { cx: n.x, cy: n.y, r: 16, fill: stanceColor(n.stance), opacity: 0.9 }),
          jsx('text', { x: n.x, y: n.y + 30, textAnchor: 'middle', fontSize: '11',
            fill: 'var(--ui-text)', children: n.name }),
          jsx('text', { x: n.x, y: n.y + 3, textAnchor: 'middle', fontSize: '10', fill: '#fff',
            children: `${n.stance >= 0 ? '+' : ''}${(n.stance || 0).toFixed(1)}` }),
        ],
      })),
    ],
  })
}

// Competition axis: red (high) on the left -> blue (low) on the right.
function SeaAxis({ sea }) {
  if (!sea || !sea.state) return null
  return jsxs('div', { className: 'flex items-center gap-1', children: [
    jsx('span', { className: 'mr-1 text-xs text-(--ui-text-tertiary)', children: 'competition' }),
    ...SEA_ORDER.map(key => {
      const conf = SEA[key]
      const active = sea.state === key
      return jsx('span', {
        key,
        title: `${conf.label} — ${conf.meaning}`,
        className: 'rounded px-2 py-0.5 text-xs ' + (active ? 'font-semibold text-white' : 'text-(--ui-text-tertiary)'),
        style: active ? { backgroundColor: conf.color } : { border: '1px solid var(--ui-border)' },
        children: conf.level,
      })
    }),
    jsx('span', { className: 'ml-1 text-xs text-(--ui-text-secondary)', children: sea.label }),
  ] })
}

function Help({ text }) {
  return jsx('span', { title: text, className: 'ml-1 cursor-help text-(--ui-text-tertiary)', children: 'ⓘ' })
}

function Field({ label, help }) {
  return jsxs('div', { className: 'flex items-center text-xs font-medium text-(--ui-text-secondary)',
    children: [label, jsx(Help, { text: help })] })
}

function Markdown({ text }) {
  const lines = String(text || '').split('\n')
  return jsx('div', { className: 'flex flex-col gap-1 text-xs', children: lines.map((ln, i) => {
    const key = `md${i}`
    if (ln.startsWith('### ')) return jsx('div', { key, className: 'text-sm font-semibold', children: ln.slice(4) })
    if (ln.startsWith('## ')) return jsx('div', { key, className: 'mt-2 text-sm font-semibold', children: ln.slice(3) })
    if (ln.startsWith('# ')) return jsx('div', { key, className: 'text-lg font-semibold', children: ln.slice(2) })
    if (ln.startsWith('> ')) return jsx('div', { key, className: 'border-l-2 pl-2 text-(--ui-text-tertiary)', children: ln.slice(2) })
    if (ln.startsWith('- ')) return jsx('div', { key, className: 'pl-3', children: `• ${ln.slice(2)}` })
    if (!ln.trim()) return jsx('div', { key, className: 'h-1' })
    return jsx('div', { key, children: ln })
  }) })
}

function UpfrontPage({ ctx }) {
  const [title, setTitle] = React.useState('Arete open-weight decision')
  const [decision, setDecision] = React.useState('')
  const [evidence, setEvidence] = React.useState('')
  const [urls, setUrls] = React.useState('')
  const [window, setWindow] = React.useState('24h')
  const [running, setRunning] = React.useState(null)
  const [result, setResult] = React.useState(null)
  const [history, setHistory] = React.useState([])
  const [injectText, setInjectText] = React.useState('')
  const [claimHits, setClaimHits] = React.useState({})
  const gateway = useValue(host.state.gateway)

  React.useEffect(() => {
    ctx.rest('/history').then(setHistory).catch(() => {})
  }, [])

  async function openRun(runId) {
    const [rep, g, cl] = await Promise.all([
      ctx.rest(`/report/${runId}`).catch(() => ({ report: '' })),
      ctx.rest(`/graph/${runId}`).catch(() => ({ nodes: [], edges: [] })),
      ctx.rest(`/claims/${runId}`).catch(() => ({ claims: [] })),
    ])
    const meta = history.find(h => h.run_id === runId) || {}
    setResult({
      runId, report: rep.report, graph: g, claims: cl.claims || [],
      sea: meta.sea_state ? { state: meta.sea_state, label: meta.sea_label, color: meta.sea_color, why: meta.sea_why } : null,
    })
    setClaimHits({})
  }

  async function run() {
    haptic('tap')
    const docs = []
    if (decision.trim()) docs.push({ type: 'decision', content: decision })
    if (evidence.trim()) docs.push({ type: 'evidence', content: evidence })
    const urlList = urls.split('\n').map(u => u.trim()).filter(Boolean)
    const { run_id } = await ctx.rest('/run', {
      method: 'POST',
      body: { title, documents: docs, urls: urlList, window },
    })
    setResult(null)
    setRunning({ runId: run_id, progress: 0, round: 0, total: 0, stances: {} })
    const iv = setInterval(async () => {
      const st = await ctx.rest(`/status/${run_id}`).catch(() => null)
      if (!st) return
      setRunning({ runId: run_id, progress: st.progress || 0, round: st.round || 0,
        total: st.total || 0, stances: st.stances || {} })
      if (st.status === 'done') {
        clearInterval(iv)
        setRunning(null)
        ctx.rest('/history').then(setHistory).catch(() => {})
        await openRun(run_id)
      } else if (st.status === 'failed') {
        clearInterval(iv)
        setRunning({ runId: run_id, progress: 0, error: st.error || 'failed' })
      }
    }, 800)
  }

  async function inject() {
    if (!injectText.trim() || !running) return
    haptic('tap')
    await ctx.rest(`/inject/${running.runId}`, {
      method: 'POST',
      body: { name: 'Counter-move', description: injectText },
    }).catch(() => {})
    setInjectText('')
  }

  async function verify(verdict) {
    if (!result) return
    await ctx.rest(`/verify/${result.runId}`, {
      method: 'POST',
      body: { verdict, hits: claimHits },
    }).catch(() => {})
    ctx.rest('/history').then(setHistory).catch(() => {})
  }

  // Hooks must run unconditionally: build the live graph before the return.
  const liveGraph = React.useMemo(() => {
    const nodes = Object.entries(running?.stances || {}).map(([name, stance]) => ({ id: name, name, stance }))
    if (!nodes.length) return null
    return { nodes, edges: result?.graph?.edges || [] }
  }, [running?.stances, result])

  const canRun = (decision.trim() || urls.trim()) && !running

  return jsxs('div', {
    className: 'flex h-full flex-col gap-4 overflow-auto p-4',
    children: [
      jsxs('div', { className: 'flex items-center justify-between', children: [
        jsx('div', { className: 'text-lg font-semibold', children: PRODUCT_NAME }),
        jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
          children: `gateway: ${gateway} · build ${BUILD}` }),
      ]}),

      // new entry
      jsxs('div', { className: 'flex flex-col gap-3 rounded border border-(--ui-border) p-4', children: [
        jsx('div', { className: 'text-sm font-medium', children: 'New review' }),
        jsx(Field, { label: 'Title (required)', help: 'Name the decision you are reviewing. Short, specific, one line. Shows in run history.' }),
        jsx('input', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm focus:border-(--ui-accent) focus:outline-none',
          placeholder: 'Title — the decision you are reviewing', value: title,
          onChange: e => setTitle(e.target.value),
        }),
        jsx(Field, { label: 'Decision document', help: 'Paste the plan or proposal — the move being reacted to. Optional if you give a URL.' }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'Decision document — paste the plan / proposal here…',
          rows: 5, value: decision, onChange: e => setDecision(e.target.value),
        }),
        jsx(Field, { label: 'Evidence (optional, recommended)', help: 'Real data, quotes, numbers, sources. The single biggest driver of output quality.' }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'Evidence (optional) — real data, quotes, numbers…',
          rows: 3, value: evidence, onChange: e => setEvidence(e.target.value),
        }),
        jsx(Field, { label: 'URLs (optional)', help: 'One per line. Fetched as documents with the URL kept as provenance. A repo URL ingests its README.' }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'URLs — blog post, repo README, landing page (one per line).',
          rows: 2, value: urls, onChange: e => setUrls(e.target.value),
        }),
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx(Field, { label: 'Window', help: '6h = 8 rounds, 12h = 12, 24h = 16, 48h = 20. Longer = slower and more thorough.' }),
          jsx('select', {
            className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
            value: window, onChange: e => setWindow(e.target.value),
            children: ['6h', '12h', '24h', '48h'].map(w => jsx('option', { key: w, value: w, children: w })),
          }),
          jsx('button', {
            type: 'button',
            className: 'rounded bg-(--ui-accent) px-4 py-1 text-sm text-white disabled:opacity-50',
            disabled: !canRun,
            onClick: run,
            children: running ? `Reviewing… ${running.progress}%` : 'Run review',
          }),
          running && running.error && jsx('div', { className: 'text-sm text-red-500', children: running.error }),
        ]}),
      ]}),

      // live run + god-mode injection
      running && !running.error && jsxs('div', { className: 'flex flex-col gap-2 rounded border border-(--ui-border) p-4', children: [
        jsxs('div', { className: 'flex items-center justify-between', children: [
          jsx('div', { className: 'text-sm font-medium', children: 'Review in progress' }),
          jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
            children: running.total ? `Round ${running.round} of ${running.total} — ${running.progress}%` : `${running.progress}%` }),
        ]}),
        jsxs('div', { className: 'h-2 w-full overflow-hidden rounded bg-(--ui-bg-secondary)', children: [
          jsx('div', { className: 'h-full bg-(--ui-accent) transition-all', style: { width: `${running.progress}%` } }),
        ]}),
        liveGraph && jsx(GraphSvg, { graph: liveGraph }),
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx('input', {
            className: 'flex-1 rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
            placeholder: 'Inject a counter-move mid-run — e.g. "Publish the eval suite first"',
            value: injectText, onChange: e => setInjectText(e.target.value),
          }),
          jsx('button', {
            type: 'button',
            className: 'rounded bg-(--ui-accent) px-3 py-1 text-sm text-white disabled:opacity-50',
            disabled: !injectText.trim(), onClick: inject, children: 'Inject ⚡',
          }),
        ]}),
      ]}),

      // finished review
      result && jsxs('div', { className: 'flex flex-col gap-2', children: [
        jsx(SeaAxis, { sea: result.sea }),
        jsxs('div', { className: 'grid grid-cols-2 gap-4', children: [
          jsx(GraphSvg, { graph: result.graph }),
          jsx('div', { className: 'max-h-[520px] overflow-auto rounded border border-(--ui-border) p-3',
            children: jsx(Markdown, { text: result.report }) }),
        ]}),
        result.claims && result.claims.length > 0 && jsxs('div', { className: 'flex flex-col gap-2 rounded border border-(--ui-border) p-3', children: [
          jsx('div', { className: 'text-sm font-medium', children: 'Score the claims — did the review call it?' }),
          ...result.claims.map(c => jsxs('div', { key: c.id, className: 'flex items-start gap-2 text-xs', children: [
            jsx('span', { className: 'flex-1', children: `${c.claim}` }),
            jsx('button', {
              type: 'button',
              className: 'rounded border border-(--ui-border) px-1 ' + (claimHits[c.id] === true ? 'font-bold' : ''),
              onClick: () => setClaimHits({ ...claimHits, [c.id]: true }), children: '✓',
            }),
            jsx('button', {
              type: 'button',
              className: 'rounded border border-(--ui-border) px-1 ' + (claimHits[c.id] === false ? 'font-bold' : ''),
              onClick: () => setClaimHits({ ...claimHits, [c.id]: false }), children: '✗',
            }),
          ]})),
          jsxs('div', { className: 'flex items-center gap-2 pt-1', children: [
            jsx('span', { className: 'text-xs text-(--ui-text-tertiary)', children: 'overall verdict:' }),
            ...['right', 'partial', 'wrong'].map(v => jsx('button', {
              key: v, type: 'button',
              className: 'rounded border border-(--ui-border) px-2 py-0.5 text-xs',
              onClick: () => verify(v), children: v,
            })),
          ]}),
        ]}),
      ]}),

      // history
      jsxs('div', { className: 'flex flex-col gap-1 rounded border border-(--ui-border) p-4', children: [
        jsx('div', { className: 'text-sm font-medium', children: 'Previous reviews' }),
        history.length === 0
          ? jsx('div', { className: 'text-sm text-(--ui-text-tertiary)',
              children: 'No runs yet — run your first review above.' })
          : [
              jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
                children: 'Click any run to reopen & score its frozen calls.' }),
              ...history.map(h => jsx('button', {
                key: h.run_id, type: 'button',
                className: 'text-left text-sm text-(--ui-text-secondary) hover:text-(--ui-text)',
                onClick: () => openRun(h.run_id),
                children: `${h.title} — friction ${h.friction ?? '—'} — ${h.sea_label || '—'} — ${h.blocker ? 'veto: ' + h.blocker : 'no veto player'}${h.verified ? ' — ' + h.verified.verdict : ''}`,
              })),
            ],
      ]}),
    ],
  })
}

export default {
  id: 'upfront',
  name: PRODUCT_NAME,
  defaultEnabled: false, // opt-in via Capabilities → Plugins
  register(ctx) {
    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/upfront' },
        render: () => jsx(UpfrontPage, { ctx }),
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        data: { path: '/upfront', label: PRODUCT_NAME, codicon: 'graph' },
      },
    ])
  },
}
