# Upfront — Positioning

**Status:** spec for **0.2.0**. Sections marked _(ships in 6.x)_ describe behaviour that does not exist yet; the README is updated in task 6.9 once the code is real.

---

## What this is

**Upfront is a strategic-response review, not a predictor.**

You bring a move — a launch, a deprecation, an open-weight release, a price change. Upfront maps the players who can stop it, the coalitions they form, the move that converts the decisive player, and how contested the ground actually is. Then it writes down what it expects and scores itself against what happened.

| Game concept | Upfront's object |
|---|---|
| The move | the decision document |
| Players | extracted stakeholders — each with an interest, an information set, and **veto power** |
| Coalition structure | camps (stance + oppose/support edges) |
| Veto player | the blocker — the player without whom the move does not pass |
| Best response | counter-moves |
| Counterfactual | mid-run injection: the same game, one variable changed _(6.x)_ |
| Payoff proxy | stance delta → friction delta |
| Stability claim | repeated runs agreeing in direction (MASS: directional consistency) _(6.x)_ |
| Contestability | red / purple / blue ocean read _(6.x)_ |
| Track record | calibration ledger — every frozen claim scored _(6.x)_ |

### Why "review" and not "prediction"

Every paper underneath this product says the same thing, and MASS states it as a boundary rule: *do not claim the simulation predicts real outcomes, and do not treat a single run as a stable conclusion.* What the method legitimately produces is:

- **mechanism exploration** — what resistance the move generates, and through whom;
- **counterfactual contrast** — does the counter-move change the outcome, or just feel like it would;
- **risk identification** — the veto player you had not budgeted for;
- **research-design preparation** — the questions to ask before you commit.

A forecast you cannot score is marketing. A review whose calls are recorded and later checked is an instrument. Upfront is the second thing.

---

## What we are allowed to claim

Three sentences, and no more:

1. "This is a structured, grounded review of who can block this decision and what changes their position."
2. "Every run publishes falsifiable claims with their evidence, and every claim is scored against what actually happened."
3. "The track record — hit rate and friction error over N scored runs — is the product's accuracy claim. Not any single report."

## What we never claim

- That it **predicts** an outcome, or estimates a real causal effect.
- That it **solves** the game, finds an **equilibrium**, or computes a Nash outcome. It tests a response; it does not solve a model.
- That LLM agents are samples of real people.
- That one run, or three scored runs, are evidence of accuracy. Every number carries its `n`.

---

## Sea state — competition level _(ships in 6.x)_

Sea state is a **landscape-level** read of how contested the move is, on a single
left-to-right axis:

```
   HIGH competition            MEDIUM                 LOW competition
   RED ocean  ─────────────────  PURPLE ocean  ────────  BLUE ocean
   everyone fighting for        a real contest with       open water —
   the same fish                winnable ground           nobody contesting
                                                          (this is the good end)
```

| State | Competition | Meaning | Trigger | Colour |
|---|---|---|---|---|
| **Red ocean** | **high** | Everyone is fighting for the same fish. Blood in the water. | veto player stance < −0.7, **or** ≥ 2 blocking camps, **or** friction ≥ 65 | `#e5484d` |
| **Purple ocean** | **medium** | Contested middle: a real fight, with ground you can win. **The common case**, and the most useful one. | everything in between | `#8b5cf6` |
| **Blue ocean** | **low** | Open water. Nobody is contesting this — the good end, and worth checking you are not also uninteresting. | friction < 35 **and** zero camps leaning against | `#3b82f6` |

**Why purple is the middle.** Red and blue are the two ends of a contestability reading
(Kim & Mauborgne's red-ocean / blue-ocean framing): crowded bloody competition versus
uncontested space. The interesting strategic answer is almost never one of the extremes —
it is *"there is a fight here, and here is the ground I can win."* Purple is that middle,
and it is the honest default: pretending most decisions are blue oceans is how planning
decks lie.

**Rules:**
- The axis runs **red (left, high) → purple → blue (right, low)**. Order is fixed.
- Never colour alone: the chip always carries the words ("Purple ocean", "competition: medium") and a `title` explaining the trigger.
- Purple must remain distinguishable for colour-blind readers; the text label is the guarantee.
- Node stance colours stay **red / amber / green** (against / undecided / for). Sea state is **red / purple / blue**. Same first and last word, different layer — say "stance" or "sea state" explicitly in every legend.

---

## Paper → mechanism map (what is honored, and what is not yet)

| Paper / skill | Required mechanism | Status |
|---|---|---|
| MASS (multi-agent-social-simulation) | replication manifest; harness + local checks; repeated runs for directional consistency; validation targets | **Partial** — manifest lands in 6.1, harness/typed failures in Phase 1, repeated-run consistency still open |
| GraphRAG (graphrag-principles) | entity/relationship/**claim** extraction with source spans; claim-based validation | **Partial** — camps exist, claim extraction lands in 6.3/6.7 |
| Generative Agents | memory stream + recency/importance retrieval; believability measured | **Partial** — retrieval implemented (`agents.py`), believability unmeasured |
| OASIS | recommendation-driven propagation, wide action set, scale evidence | **Not honored** — 4 actions, no RecSys, no scale evidence |
| CAMEL | inception prompting, task specifier, critic-in-the-loop | **Not honored** — role framing only |
| Calibration | predictions scored against outcomes over time | **Not honored** — lands in 6.4/6.5 |

The table is deliberately unflattering. A reviewer who finds an overclaim in the README will distrust everything else in the plugin; a reviewer who finds an honest gap list will trust the rest.

---

## Naming

- Product: **Upfront** — "your opponent, before they exist."
- Category: **strategic response review** (or "adversarial decision review").
- Never: "prediction engine", "forecast", "simulator of reality", "game solver".
- In one line: *"Paste a decision. See who can veto it, what changes their mind, how contested the ground is — then check the call in 48 hours."*

### The final name may change after completion — here is the cost

Identity (`upfront`) is deliberately kept separate from the display name so a late rename is cheap where it should be, and explicit where it is not.

| Rename | Cost | What must change |
|---|---|---|
| **Display name** (what a user reads) | 1 line | `PRODUCT_NAME` in `desktop/plugin.js`, README title, this file |
| **Catalog / marketing name** | low | `docs/catalog-entry.draft.yaml` `name:` + `title:`, then the `plugin-catalog/` PR |
| **Repo name** | low | GitHub rename (301-redirects), `git remote set-url origin`, local folder name |
| **Plugin id** (`upfront`) | **high — plan a migration** | tool names `upfront_*`, data path `$HERMES_HOME/upfront/`, install folder `plugins/strategic-arena`, history provenance. Needs: rename data dir, rewrite manifest/tool prefixes, keep old tool names as aliases for one release |

Default decision until the user says otherwise: **keep the id `upfront`, change only the display name.**

---

## Known limits (say these out loud, unprompted)

1. **Pre-experimental evidence.** Not causal, not a forecast. (MASS §5.4.)
2. **Prompt/model sensitivity.** Same documents on a different model can move stances. That is why every run records a manifest.
3. **Thin input → guesswork.** Input quality is scored and surfaced; a low-confidence run should be re-fed, not quoted.
4. **Small coalitions.** 3–16 stakeholders is a leadership team, not a market. Scale claims are out of scope.
5. **Track record needs volume.** Until 10+ scored runs, the ledger is a curiosity, not proof.
6. **Model choice is consent-gated.** Picking a model for the review needs `llm.model_override`; without it the run uses the active model. Prices shown are the catalogue's published per-token prices, fetched live and cached 6h — never a hardcoded table.
