// Upfront Prediction — desktop plugin (unified package, desktop half).
//
// Loads UNCOMPILED: no JSX. Only imports @hermes/plugin-sdk, react, react/jsx-runtime.
// Surface: LEFT sidebar nav row + full center page (ROUTES_AREA). Not a right pane.
// The page POSTs to /api/plugins/upfront/run, polls /status/{id}, then renders the
// graph as pure React SVG and the markdown report.

import { host, haptic, useValue } from '@hermes/plugin-sdk'
import React from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

function stanceColor(s) {
  if (s < -0.3) return '#e5484d' // red
  if (s > 0.3) return '#46a758'  // green
  return '#f5a524'               // yellow
}

function layoutGraph(nodes, w, h) {
  // simple circular layout — good enough for 5-16 nodes, no library
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
    viewBox: `0 0 ${w} ${h}`, className: 'w-full rounded border border-(--ui-border) bg-(--ui-bg)',
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
          jsx('text', {
            x: n.x, y: n.y + 30, textAnchor: 'middle', fontSize: '11',
            fill: 'var(--ui-text)', children: n.name,
          }),
          jsx('text', {
            x: n.x, y: n.y + 3, textAnchor: 'middle', fontSize: '10',
            fill: '#fff', children: `${n.stance >= 0 ? '+' : ''}${(n.stance || 0).toFixed(1)}`,
          }),
        ],
      })),
    ],
  })
}

function UpfrontPage({ ctx }) {
  const [title, setTitle] = React.useState('Arete open-weight decision')
  const [decision, setDecision] = React.useState('')
  const [evidence, setEvidence] = React.useState('')
  const [urls, setUrls] = React.useState('')
  const [window, setWindow] = React.useState('48h')
  const [running, setRunning] = React.useState(null)  // {runId, progress, round, total, stances}
  const [result, setResult] = React.useState(null)    // {report, graph}
  const [history, setHistory] = React.useState([])
  const gateway = useValue(host.state.gateway)

  React.useEffect(() => {
    ctx.rest('/history').then(setHistory).catch(() => {})
  }, [])

  async function run() {
    haptic('tap')
    const docs = [{ type: 'decision', content: decision }]
    if (evidence.trim()) docs.push({ type: 'evidence', content: evidence })
    const urlList = urls.split('\n').map(u => u.trim()).filter(Boolean)
    const { run_id } = await ctx.rest('/run', {
      method: 'POST',
      body: { title, documents: docs, urls: urlList, window },
    })
    setRunning({ runId: run_id, progress: 0, round: 0, total: 0, stances: {} })
    // poll status; stances ride along so the graph updates live each round
    const iv = setInterval(async () => {
      const st = await ctx.rest(`/status/${run_id}`).catch(() => null)
      if (!st) return
      setRunning({ runId: run_id, progress: st.progress || 0, round: st.round || 0,
                   total: st.total || 0, stances: st.stances || {} })
      if (st.status === 'done') {
        clearInterval(iv)
        const [rep, g] = await Promise.all([
          ctx.rest(`/report/${run_id}`).catch(() => ({ report: '' })),
          ctx.rest(`/graph/${run_id}`).catch(() => ({ nodes: [], edges: [] })),
        ])
        setResult({ report: rep.report, graph: g })
        setRunning(null)
        ctx.rest('/history').then(setHistory).catch(() => {})
      } else if (st.status === 'failed') {
        clearInterval(iv)
        setRunning({ runId: run_id, progress: 0, error: st.error || 'failed' })
      }
    }, 800)
  }

  return jsxs('div', {
    className: 'flex h-full flex-col gap-4 overflow-auto p-4',
    children: [
      jsxs('div', { className: 'flex items-center justify-between', children: [
        jsx('div', { className: 'text-lg font-semibold', children: 'Upfront Prediction' }),
        jsx('div', { className: 'text-xs text-(--ui-text-tertiary)', children: `gateway: ${gateway}` }),
      ]}),
      // new entry form
      jsxs('div', { className: 'flex flex-col gap-3 rounded border border-(--ui-border) p-4', children: [
        jsx('div', { className: 'text-sm font-medium', children: 'New entry' }),
        jsx('input', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm focus:border-(--ui-accent) focus:outline-none',
          placeholder: 'Title — the decision you are predicting', value: title, onChange: e => setTitle(e.target.value),
        }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'Decision document — paste the plan / proposal here…',
          rows: 5, value: decision, onChange: e => setDecision(e.target.value),
        }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'Evidence (optional) — real data, quotes, numbers…',
          rows: 3, value: evidence, onChange: e => setEvidence(e.target.value),
        }),
        jsx('textarea', {
          className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
          placeholder: 'URLs — a blog post, a repo README, a landing page (one per line). Fetched as documents.',
          rows: 2, value: urls, onChange: e => setUrls(e.target.value),
        }),
        jsxs('div', { className: 'flex items-center gap-2', children: [
          jsx('select', {
            className: 'rounded border border-(--ui-border) bg-(--ui-bg) px-2 py-1 text-sm',
            value: window, onChange: e => setWindow(e.target.value),
            children: ['6h', '12h', '24h', '48h'].map(w => jsx('option', { key: w, value: w, children: w })),
          }),
          jsx('button', {
            type: 'button',
            className: 'rounded bg-(--ui-accent) px-4 py-1 text-sm text-white disabled:opacity-50',
            disabled: !decision.trim() || !!running,
            onClick: run, children: running ? `Simulating… ${running.progress}%` : 'Run prediction',
          }),
          running?.error && jsx('div', { className: 'text-sm text-red-500', children: running.error }),
        ]}),
      ]}),
      // live in-progress graph (renders from polled stances each round)
      running && !running.error && jsxs('div', { className: 'flex flex-col gap-2 rounded border border-(--ui-border) p-4', children: [
        jsxs('div', { className: 'flex items-center justify-between', children: [
          jsx('div', { className: 'text-sm font-medium', children: 'Simulation in progress' }),
          jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
            children: running.total ? `Round ${running.round} of ${running.total} — ${running.progress}%` : `${running.progress}%` }),
        ]}),
        jsxs('div', { className: 'h-2 w-full overflow-hidden rounded bg-(--ui-bg-secondary)', children: [
          jsx('div', { className: 'h-full bg-(--ui-accent) transition-all', style: { width: `${running.progress}%` } }),
        ]}),
        React.useMemo(() => {
          const nodes = Object.entries(running.stances || {}).map(([name, stance]) => (
            { id: name, name, stance }
          ))
          return nodes.length ? jsx(GraphSvg, { graph: { nodes, edges: [] } }) : null
        }, [running.stances]),
      ]}),
      // result (finished report + final graph)
      result && jsxs('div', { className: 'grid grid-cols-2 gap-4', children: [
        jsx(GraphSvg, { graph: result.graph }),
        jsx('pre', {
          className: 'whitespace-pre-wrap rounded border border-(--ui-border) p-3 text-xs',
          children: result.report,
        }),
      ]}),
      // previous runs — always visible so users can find history
      jsxs('div', { className: 'flex flex-col gap-1 rounded border border-(--ui-border) p-4', children: [
        jsx('div', { className: 'text-sm font-medium', children: 'Previous runs' }),
        history.length === 0
          ? jsx('div', { className: 'text-sm text-(--ui-text-tertiary)',
              children: 'No runs yet — run your first prediction above.' })
          : [
              jsx('div', { className: 'text-xs text-(--ui-text-tertiary)',
                children: 'Click any run to reopen & verify its frozen prediction.' }),
              ...history.map(h => jsx('button', {
                key: h.run_id, type: 'button',
                className: 'text-left text-sm text-(--ui-text-secondary) hover:text-(--ui-text)',
                onClick: async () => {
                  const [rep, g] = await Promise.all([
                    ctx.rest(`/report/${h.run_id}`).catch(() => ({ report: '' })),
                    ctx.rest(`/graph/${h.run_id}`).catch(() => ({ nodes: [], edges: [] })),
                  ])
                  setResult({ report: rep.report, graph: g })
                },
                children: `${h.title} — friction ${h.friction ?? '—'} — ${h.blocker ? 'blocker: ' + h.blocker : 'no blocker'}`,
              })),
            ],
      ]}),
    ],
  })
}

export default {
  id: 'upfront',
  name: 'Upfront Prediction',
  defaultEnabled: false, // opt-in via Capabilities → Plugins (marketplace pattern)
  register(ctx) {
    // LEFT sidebar nav row
    ctx.register({
      id: 'nav', area: 'sidebar.nav',
      data: { path: '/upfront', label: 'Upfront', codicon: 'graph' },
    })
    // full CENTER page
    ctx.register({
      id: 'page', area: 'routes',
      data: { path: '/upfront' },
      render: () => jsx(UpfrontPage, { ctx }),
    })
  },
}
