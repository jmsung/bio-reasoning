# Index

Catalog of all `source/` (per-artifact distillations, flat) and `wiki/`
(hand-curated synthesis) pages. New entries are added by `/wiki-ingest`,
`/wiki-learn`, and `/wiki-query --file-back`.

If you add a page manually, add an entry here too — or run `/wiki-lint --fix`
to catch the orphan.

## source/ — per-artifact distillations

Pages live under `knowledge/source/` (flat) or `knowledge/domains/<domain>/source/`
(synced corpus). Type lives in each page's `source_type:` frontmatter; this index
groups them by type for browsing.

### Papers

- [PerturbQA — Contextualizing perturbation experiments through language](../source/2025-wu-perturbqa.md) — arxiv.org · 2025 (ICLR)
- [Tahoe-100M — Giga-Scale Single-Cell Perturbation Atlas](../source/2025-zhang-tahoe-100m.md) — biorxiv.org · 2025
- [Replogle 2022 — Genome-scale Perturb-seq (CRISPRi, K562/RPE1)](../source/2022-replogle-genome-scale-perturb-seq.md) — Cell · 2022
- [Papalexi 2021 — ECCITE-seq immune checkpoints (THP-1)](../source/2021-papalexi-eccite-seq-immune-checkpoints.md) — Nat Genet · 2021
- [Dixit 2016 — original Perturb-seq (mouse dendritic cells)](../source/2016-dixit-perturb-seq.md) — Cell · 2016
- [scPerturb 2024 — harmonized single-cell perturbation data](../source/2024-peidli-scperturb.md) — Nat Methods · 2024
- [SynthPert — LLM biological reasoning via synthetic reasoning traces](../domains/ai-reasoning/source/2025-phillips-synthpert-reasoning-traces.md) — arXiv · 2025
- [KG + Reasoning LLMs for simple transcriptomic perturbation predictors](../domains/ai-reasoning/source/2026-fawkes-kg-reasoning-llm-perturbation-predictors.md) — arXiv · 2026
- [Plausibility Is Not Prediction — contrastive LLM perturbation reasoning](../domains/ai-reasoning/source/2026-yuan-plausibility-not-prediction-llm-perturbation.md) — arXiv · 2026
- [LLMs Meet Virtual Cell — a survey](../domains/bio-foundation-models/source/2025-li-llms-meet-virtual-cell-survey.md) — arXiv · 2025
- [DL perturbation prediction does not yet beat linear baselines](../domains/bio-multiomics/source/2025-ahlmann-eltze-dl-perturbation-vs-linear.md) — Nat Methods · 2025
- [Benchmarking generalizable single-cell perturbation prediction (scPerturBench)](../domains/bio-multiomics/source/2025-wei-scperturbench-generalizable-perturbation.md) — Nat Methods · 2025
- [PerturBench — benchmarking ML models for cellular perturbation](../domains/bio-multiomics/source/2024-wu-perturbench.md) — arXiv · 2024
- [CellBench-LS — single-cell foundation models in low-supervision](../domains/bio-foundation-models/source/2026-xu-cellbench-ls.md) — bioRxiv · 2026
- [GEARS — predicting outcomes of novel multigene perturbations](../domains/bio-multiomics/source/2023-roohani-gears.md) — Nat Biotechnol · 2023
- [CisTransCell — perturbation prediction via function, regulation, context](../domains/bio-multiomics/source/2026-zhang-cistranscell.md) — arXiv · 2026
- [scDFM — distributional flow matching for perturbation prediction](../domains/bio-multiomics/source/2026-yu-scdfm.md) — arXiv · 2026
- [Traxler 2025 — time-series + CRISPR screen of macrophage immune regulation (mouse)](../domains/bio-multiomics/source/2025-traxler-macrophage-crispr-timeseries.md) — Cell Systems · 2025
- [Binan 2025 — Perturb-FISH: CRISPR + spatial in THP-1 macrophages](../domains/bio-multiomics/source/2025-binan-crispr-spatial-macrophage-circuits.md) — Cell · 2025
- [D-SPIN — regulatory network models of perturbation response](../domains/bio-multiomics/source/2026-jiang-d-spin.md) — Cell · 2026

### Web

- [BioReasoning Challenge 2026 — overview](../source/2026-bioreasoning-challenge-overview.md) — genentech.github.io · 2026-06-06
- [Karpathy — LLM Wiki pattern](../source/karpathy-llm-wiki.md) — gist.github.com/karpathy · 2026-06-06

### Repos

- [tobi/qmd — local document search engine](../source/qmd.md) — github.com/tobi/qmd · 2026-06-06

### Talks

_(none yet)_

### Notion / Slack

_(none yet)_

## wiki/ — synthesis

### Findings

- [Track A EDA — data structure and predictive signal](findings/track-a-eda.md) — 2026-06-08
- [Housekeeping-perturbation transferability — augmentation lead](findings/housekeeping-transfer-hypothesis.md) — 2026-06-08
- [TabPFN / tabular foundation models for Track A and B](findings/tabpfn-for-perturbation-tracks.md) — 2026-07-15
- [Track B — the agent underperformed its own prior (rank-metric abstention)](findings/track-b-abstention-failure.md) — 2026-07-16

### Methods

- [Assessing external Perturb-seq datasets — compute plan & tooling](methods/perturb-seq-data-assessment.md) — 2026-06-08

### Decisions

- [0001 — PR-only workflow with squash-merge](decisions/0001-pr-workflow.md) — 2026-06-06
- [0002 — When to use skill form vs agent form](decisions/0002-skill-vs-agent-convention.md) — 2026-06-06
- [0003 — Personal vs team skill/agent layering](decisions/0003-personal-team-skill-layering.md) — 2026-06-06

### Concepts

_(none yet — entity / concept pages that span multiple sources)_
