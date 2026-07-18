# Track B — Description of Approach

**From:** Joo · **For:** Jongmin (to structure into a plan)

> _Early approach notes (2026-07-14), since validated/extended by the findings: functional biological tools, graded confidence, and the dual-OOD holdout were **confirmed**; the agentic literature/dataset-crawl idea was **tested → parity** (external knowledge doesn't crack DE, and arbitrary literature is off the allowed-data list). See [`reports/technical-report.md`](../reports/technical-report.md) and [`knowledge/wiki/findings/external-knowledge-does-not-crack-de.md`](../knowledge/wiki/findings/external-knowledge-does-not-crack-de.md)._

Track B is the agentic tool-use track: same task and data as Track A (predict
up/down/none for a perturbation–gene pair, same AUROC metric), but the model may
**reason and call tools** across many rounds per row. Where Track A leans on a
hand-built evidence prior, Track B is our **unbiased, agent-driven experiment** —
give the agent the right tools and let its reasoning find the signal, with
minimal hand-crafted rules. The contrast between the two is the interesting
result.

## Shared evidence that still applies (from our EDA + literature)

- **AUROC metric** → the agent must emit **graded confidence**, not a hard
  A/B/C (e.g. seed-ensembling or explicit probabilities); hard labels waste the
  metric.
- **Fully disjoint test** (zero shared perturbations/genes with train) →
  **identity lookups into training data are near-useless per-row**; retrieval
  has to be **functional** — GO / pathway / PPI / cross-dataset analogs.
- **Direction is the tractable axis** (housekeeping→up, immune/myeloid→down);
  DE-vs-none is harder. The agent can rediscover this, or be handed it as a tool.

## Approach (structure left to you)

- Equip the agent with **biological-knowledge tools** rather than
  training-identity lookups: gene annotation / GO (mygene.info), pathways,
  protein interactions (STRING), and the augmentation datasets (Replogle,
  Papalexi, Dixit) as functional-analog evidence.
- Give the agent a **literature/dataset crawl tool** so it can search and pull
  in relevant papers and public datasets on demand (PubMed / bioRxiv, GEO,
  scPerturb, …) — making evidence discovery part of the reasoning loop rather
  than a fixed, pre-loaded set.
- Keep it **unbiased** — minimize hand-coded rules, so we're genuinely testing
  whether agentic reasoning *itself* recovers the biology (the point of the
  experiment, and in the spirit of "system over micro-management").
- Optionally expose the Track A evidence prior *as a tool* the agent may
  consult, so we can **ablate hand-prior vs pure reasoning**.
- Mind the practical limits: tool-count / call and prompt-token caps; log
  `tokens_used` and tool-call counts to weigh quality against cost.

## What we're actually testing

On the same leak-free split (hold out entire perturbations and genes), does
**unbiased agentic reasoning match or beat the cheap, biology-grounded Track A
prior — and at what token cost?**
