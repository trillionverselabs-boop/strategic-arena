# Credits, sources and licences

Strategic Arena (repository id `upfront`) is **MIT-licensed** and is a
**clean-room implementation**: no source code, data file or asset from any project
listed below is vendored in this repository. What we take from each is the *idea*,
and ideas are cited here rather than copied into the tree.

If you believe something here is used without credit, open an issue. The fix is a
citation — and if code is ever involved, a licence change, not an excuse.

---

## Papers we implement ideas from

| Paper | Id | What we take | Code in this repo |
|---|---|---|---|
| **CAMEL: Communicative Agents for "Mind" Exploration of LLM Society** — Li et al. | [arXiv:2303.17760](https://arxiv.org/abs/2303.17760) | Role framing and inception-style prompts; the role-flip / flake-reply / infinite-loop failure modes we guard against | None — our own prompt templates in `ingestion.py` |
| **OASIS: Open Agent Social Interaction Simulations with One Million Agents** | [arXiv:2411.11581](https://arxiv.org/abs/2411.11581) | Round-based simulation loop, action taxonomy, propagation of a move to parties not named in the input | None — `simulation.py` is ours |
| **MASS: Protocolizing LLM-Driven Agent-Based Modeling as a Quantitative Research Method** — Hu & Shen, 2026 | [MDPI 2673-2688/7/8/279](https://www.mdpi.com/2673-2688/7/8/279) | Replication manifest, scheduling discipline, the 8 failure modes, and the boundary rule that LLM simulation yields *pre-experimental evidence* | None — `manifest.py`, `failure_modes.py` are ours |
| **GraphRAG: From Local to Global** — Edge et al. | [arXiv:2404.16130](https://arxiv.org/abs/2404.16130) | Entity / relationship / claim extraction carrying source spans, so every party's position cites the line it stands on | None — `graph.py`, `claims.py` |
| **Generative Agents: Interactive Simulacra of Human Behavior** — Park et al. | [arXiv:2304.03442](https://arxiv.org/abs/2304.03442) | Memory stream, recency + importance + relevance retrieval, periodic reflection | None — `agents.py` |
| **Shapley Counterfactual Credits for Multi-Agent Reinforcement Learning** — Li et al. | [arXiv:2106.00285](https://arxiv.org/abs/2106.00285) | Credit by ablation: remove a party, measure what leaves the room | None — `leverage.py` |
| **Market Regime Council: Dynamic Credit Assignment in Multi-Agent LLM Decision Systems** — Pei et al. | [arXiv:2605.24490](https://arxiv.org/abs/2605.24490) | Exact Shapley over single / pairwise / grand coalitions; the coalition term that tells two objections from one | None — `leverage.py` |
| **Evaluating LLMs on Real-World Forecasting Against Expert Forecasters** — Lu | [arXiv:2507.04562](https://arxiv.org/abs/2507.04562) | Brier scoring as the honesty layer: a claim with a probability and a resolution date | None — `claims.py`, `reporting.py` |
| **Approaching Human-Level Forecasting with Language Models** — Halawi et al. | [arXiv:2402.18563](https://arxiv.org/abs/2402.18563) | Grounded retrieval before a probability is asserted; calibration reporting with n stated | None |
| **A Benchmark for Multi-Party Negotiation Games from Real Negotiation Data** — Benac et al. | [arXiv:2603.14066](https://arxiv.org/abs/2603.14066) | Validation target: does a simulated multi-party room's outcome distribution resemble real multi-party deals? | None — validation roadmap, not shipped behaviour |
| **Large Language Models as Virtual Survey Respondents** — Zhao et al. | [arXiv:2509.06337](https://arxiv.org/abs/2509.06337) | Validation target: a simulated party should reproduce the distribution of the real population it stands for | None — validation roadmap |
| **A Value for n-Person Games** — Shapley, L. S. (1953) | *Contributions to the Theory of Games II* | The attribution itself: the unique fair decomposition of a coalition game | None — the method, implemented in `leverage.py` |

## Projects and inspiration

**MiroFish** — [github.com/666ghj/MiroFish](https://github.com/666ghj/MiroFish),
licensed **AGPL-3.0**.

MiroFish explores the same territory with a much larger footprint: a swarm engine
that predicts how a landscape responds. Strategic Arena shares the *spirit* — test
a move against synthetic respondents before you ship it — and nothing else.

- **No MiroFish code, assets, prompts or data files are included in this
  repository.** Not a line, not a template, not a screenshot.
- AGPL-3.0 is a strong copyleft: if any of it were here, this repository could not
  be MIT. It is MIT because none of it is here.
- The two tools are complementary. If MiroFish is useful to you, use it and support
  it.

**Hermes Agent** — [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).
Strategic Arena is a Hermes plugin: it runs inside the agent, calls models through
`ctx.llm` (host-owned credentials), and renders through `@hermes/plugin-sdk`. It
does not modify Hermes, patch its markup, or override any core function.

## Third-party libraries

None vendored, none bundled. The plugin declares **no Python dependencies** of its
own: `pydantic` and `fastapi` are Hermes core requirements and are imported from the
host environment. The desktop half imports only `@hermes/plugin-sdk`, `react` and
`react/jsx-runtime`, which the Hermes Desktop renderer provides.

## Assets in this repository

- `assets/logo.svg`, `assets/banner.svg`/`.png`, `assets/how-it-works.png` — drawn
  for this project, MIT with the rest of the repository.
- No third-party icon set, font file or bitmap is bundled. Icons come from the
  app's own `Codicon` component; typography is the app's own font stack.

## Licence

MIT. Copyright (c) 2026 **LDMA Partners**, who hold the copyright and grant the
licence. TrillionVerse Labs is the studio name this work is made under; LeMultiFox
is the author. A commercial or contractual question goes to LDMA Partners; a
question about the code goes to LeMultiFox.

See [LICENSE](LICENSE).
