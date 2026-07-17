# Wiki log

Append-only history of ingests and queries.

## 2026-07-17 — Wiki-learn: Perturb-seq data lane closed end-to-end (real-LB)
- Insights filed: 1 (real-board confirmation)
- Updated pages: findings/direction-transfers-de-doesnt.md (status draft→measured + real-LB
  confirmation), findings/contrastive-de-core-assessment.md (Perturb-seq lane OPEN→CLOSED),
  findings/dir-ceiling-equal-weight-fusion.md (real-LB update), findings/curated-edges-fail-de-axis.md
  + findings/marginal-de-caps-at-degree.md (status draft→measured, kb-epistemic cleanup),
  index.md (pbio-agent-for-tracks orphan indexed)
- Source: `research/perturb-seq-real-lb-overlap` — the one reserved real-LB read landed baseline
  `fuse([GO,neighbour])` 0.585 → +external PerturbQA 0.586 (Δ+0.001, 66% cov). Confirms
  end-to-end that external measured data moves DE nothing and the dual-OOD split is honest; the
  only DE lever left (model-based logprob) is endpoint-blocked, so DE-driven rank-1 is *blocked*,
  not open via more data.

## 2026-07-16 — Wiki-learn: marginal DE caps at STRING degree
- Insights filed: 1
- New pages: findings/marginal-de-caps-at-degree.md
- Updated pages: index.md, findings/direction-transfers-de-doesnt.md (reverse cite)
- Source: `feat/richer-marginal-de` — DepMap ternary essentiality adds nothing on top of
  STRING degree (+ess 0.534±0.006 vs degree-only 0.536±0.007, Δ−0.001; essentiality
  collinear with degree). Marginal DE capped ~0.536; static/data DE route exhausted.

## 2026-07-16 — Wiki-learn: neighbour-retrieval is a direction lever, not a DE lever
- Insights filed: 1
- New pages: findings/neighbor-retrieval-direction-lever.md
- Updated pages: index.md, findings/curated-edges-fail-de-axis.md (reverse cite)
- Source: `feat/de-retrieval` — DE-AUROC 0.498 (chance) but DIR-AUROC 0.651±0.047; fusion +0.027 mean.


## 2026-07-16 — Wiki-learn: curated-edge DBs fail the DE axis
- Insights filed: 1
- New pages: findings/curated-edges-fail-de-axis.md
- Updated pages: findings/competitor-landscape.md (reverse cite)
- Source: `feat/de-detector` branch experiments — CollecTRI (0.4% edges), STRING 1-hop
  (1.6%), STRING 2-hop proximity (DE-AUROC 0.543). All curated-network DE channels too
  weak on arbitrary (pert,gene) pairs → go model-based (logprobs / neighbor-retrieval).

## 2026-07-16 — Update: two-stage direction blend beats the "blend exhausted" claim
- Updated pages: findings/track-b-abstention-failure.md — the earlier "blend
  exhausted" verdict was about the *raw α·agent+(1−α)·prior* blend. A *different*
  lever — rank-blending the two-stage GO-term model's **direction** into
  floor-to-prior — lifted Kaggle **LB 0.568 → 0.578** (branch two-stage-de-dir).
  Corrected the Takeaway: the DE ceiling is evidence-bound, but the direction
  axis still lifts with an orthogonal learned signal.
- Related: Track A two-stage GO-term model LB **0.561** (vs prior 0.529).

## 2026-07-16 — Wiki-learn: Track B floor-to-prior confirmed, blend exhausted
- Insights filed: 2
- Updated pages: findings/track-b-abstention-failure.md ("Fix direction" →
  measured outcomes: floor-to-prior LB 0.568 / OOD-val 0.564 = best config;
  blend gives no gain; ceiling is evidence-bound)
- New pages: none

## 2026-06-08 — Ingested source/2025-zhang-tahoe-100m
- Source: https://www.biorxiv.org/content/10.1101/2025.02.20.639398v1
- Type: papers

## 2026-06-08 — Ingested source/2025-wu-perturbqa
- Source: https://arxiv.org/abs/2502.21290
- Type: papers

## 2026-06-08 — Ingested source/2022-replogle-genome-scale-perturb-seq
- Source: https://www.sciencedirect.com/science/article/pii/S0092867422005979
- Type: papers

## 2026-06-08 — Ingested source/2021-papalexi-eccite-seq-immune-checkpoints
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8011839/
- Type: papers

## 2026-06-08 — Ingested source/2016-dixit-perturb-seq
- Source: https://www.cell.com/cell/fulltext/S0092-8674(16)31610-5
- Type: papers

## 2026-06-08 — Ingested source/2024-peidli-scperturb
- Source: https://www.nature.com/articles/s41592-023-02144-y
- Type: papers

## 2026-07-06 — Ingested source/2026-kim-pbio-agent
- Source: https://openreview.net/forum?id=5GIEGTv9y4 (code: https://github.com/icecream126/pbioagent_lincsqa)
- Type: papers
- raw: `raw/2026-kim-pbio-agent.md` (gitignored, README; paper PDF gated)
- source: `source/2026-kim-pbio-agent.md` (in git, distilled, hash 6996cfa65a75)

## 2026-07-13 — Ingested 14 perturbation-prediction papers (batch)
Search-and-ingest for macrophage gene-perturbation-prediction (Track A/B/C). 16 candidates found; 2 skipped as duplicates of existing pages (SUMMER = 2025-wu-perturbqa; "Progressive Multi-Agent Reasoning" = 2026-kim-pbio-agent). 14 new source pages:
- source/2025-phillips-synthpert-reasoning-traces (arXiv 2509.25346)
- source/2026-fawkes-kg-reasoning-llm-perturbation-predictors (arXiv 2606.08816)
- source/2026-yuan-plausibility-not-prediction-llm-perturbation (arXiv 2606.01042)
- source/2025-li-llms-meet-virtual-cell-survey (arXiv 2510.07706)
- source/2025-ahlmann-eltze-dl-perturbation-vs-linear (Nat Methods, 10.1038/s41592-025-02772-6)
- source/2025-wei-scperturbench-generalizable-perturbation (Nat Methods, 10.1038/s41592-025-02980-0)
- source/2024-wu-perturbench (arXiv 2408.10609)
- source/2026-xu-cellbench-ls (bioRxiv 10.64898/2026.04.01.714123)
- source/2023-roohani-gears (Nat Biotechnol, 10.1038/s41587-023-01905-6)
- source/2026-zhang-cistranscell (arXiv 2606.13713)
- source/2026-yu-scdfm (arXiv 2602.07103)
- source/2025-traxler-macrophage-crispr-timeseries (Cell Systems, 10.1016/j.cels.2025.101346)
- source/2025-binan-crispr-spatial-macrophage-circuits (Cell, 10.1016/j.cell.2025.02.012)
- source/2026-jiang-d-spin (Cell, S0092-8674(26)00463-0)

## 2026-07-15 — Wiki-learn: TabPFN for Track A/B
- Insights filed: 1
- New pages: findings/tabpfn-for-perturbation-tracks.md
- Updated pages: index.md, methods/pbio-agent-for-tracks.md

## 2026-07-17 — Wiki-learn: direction transfers, DE doesn't (lit-corroborated)
- Insights filed: 1
- New pages: findings/direction-transfers-de-doesnt.md
- Updated pages: index.md, findings/neighbor-retrieval-direction-lever.md, findings/curated-edges-fail-de-axis.md

## 2026-07-17 — Learned finding: LLM self-consistency fails the DE axis
- Kill-test (feat/de-logprob-self-consistency): Claude sonnet-4.5 sample-vote self-consistency,
  150 dual-OOD rows × 3 samples → AUROC_de 0.495 (chance), AUROC_dir 0.571. DE hypothesis dead.
- New page: findings/llm-self-consistency-fails-de-axis.md (predicted by the consult-KB gate).

## 2026-07-16 — Ingested 83 full-text distillations (feat/knowledge-base-expansion)
- Batch full-text ingest via paperclip + a discover→distill workflow (95 written, 3 removed as
  domains/ duplicates: GEARS, Ahlmann-Eltze linear-baselines, D-SPIN; 9 collided/merged → 83 net-new).
- Buckets (agents dropped, bio-reweighted): Track C single-cell foundation models + critiques;
  perturbation/expression prediction methods + benchmarks; gene-regulation biology (GRN inference,
  CRISPR functional screens, TF networks) + a slim bio-specific agent set (Biomni, Virtual Cell).
- All flat `knowledge/source/`, `source_type: papers`, deduped vs the 217-page corpus by title/DOI.
- Durable pages to be promoted to the knowledge-base SSOT + synced into domains/ later (out of band).
