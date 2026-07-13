---
source_url: https://arxiv.org/abs/2408.10609
source_type: papers
title: "PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis"
author: Yan Wu et al.
year: 2024
retrieved: 2026-07-13
---

# PerturBench: Benchmarking Machine Learning Models for Cellular Perturbation Analysis

**Authors:** Yan Wu, Esther Wershof, Sebastian M. Schmon, Marcel Nassar, Błażej Osiński, Ridvan Eksi, Zichao Yan, Rory Stark, Kun Zhang, Thore Graepel
**Year:** 2024 (v1 Aug 2024; v4 Oct 2025)
**Venue:** arXiv:2408.10609 [cs.LG]; NeurIPS 2024/2025 poster. Code: github.com/altoslabs/perturbench

## Abstract
PerturBench is a comprehensive, modular framework for benchmarking ML models that predict single-cell transcriptomic responses to perturbations (genetic knockdown/overexpression, small molecules, combinations, cytokines). It bundles a user-friendly training/evaluation platform, a curated collection of diverse perturbational datasets, and a set of metrics designed to fairly compare models and dissect their behavior. Evaluating published and baseline models across datasets, the authors find no single architecture dominates, that simpler models are competitive and scale well, and that widely-used models suffer failure modes like posterior/mode collapse that traditional fit metrics fail to detect.

## Key contributions
- A modular PyTorch/Lightning/Hydra + Scanpy/AnnData platform for perturbation-model dev and eval.
- Six standardized public datasets with defined splits and tasks.
- Rank-based metrics that complement RMSE/cosine and expose mode collapse.
- Empirical finding that simple baselines rival complex VAEs, especially at scale.

## Methods
**Models:** published — CPA, SAMS-VAE, BioLord, GEARS, scGPT embeddings; baselines — Linear (one-hot pert+covariate), Latent Additive, Decoder-Only (covariate-only, no expression input); plus ablations (CPA noAdv, SAMS-VAE no-sparsity).
**Datasets:** Norman19 (combo genetic), Srivatsan20 (chemical), Frangieh21 (genetic), McFaline-Figueroa23 (genetic, scaling), Jiang24 (1.6M cells, genetic), OP3 (chemical) — spanning 91k–1.6M cells and 1–30 biological states.
**Metrics:** fit — RMSE, cosine LogFC; distributional — MMD/energy distance (gene + PCA space), DEG recall (top-20); **rank metrics** — rank_average, cosine-LogFC rank (0 = perfect, ~0.5 = random), which measure whether a prediction is closer to its true perturbation than to others.
**Generalization scenarios:** (1) covariate transfer — train perturbations in some cell contexts, test on held-out contexts; (2) combinatorial — train singles, predict duals; (3) data scaling; (4) data imbalance across covariates.

## Key results
- No architecture wins across all conditions; simpler baselines are competitive and scale better.
- Decoder-Only (covariate-only) scored ~0.47 rank (near random) despite decent cosine/RMSE — the signature of mode/posterior collapse (same prediction for every perturbation) that fit metrics miss.
- On Jiang24 (1.6M cells), Decoder-Only reached best rank (~0.32) while CPA/SAMS-VAE degraded (~0.40+).

## Why it matters for our work
Our task is a coarsened version of this exact problem: predict, for a (perturbed gene, target gene) pair, whether the target goes up/down/none — macrophage CRISPRi, zero-overlap perturbation split, with `none` the 55% majority class. PerturBench's covariate/unseen-perturbation transfer setup is the generalization regime our zero-overlap split imposes, so borrow its discipline: (1) do **not** trust RMSE/accuracy alone — a model that always predicts `none` mirrors mode collapse and would score deceptively well against a 55% majority, so add a **rank/ordering metric** and per-class (up/down) recall to the validation harness; (2) report **DEG-recall-style** hit rate on the true up/down calls; (3) treat simple baselines (linear one-hot, additive) as serious contenders across Tracks A/B/C, not just sanity checks — they scale and generalize. The `none`-majority trap is precisely the fit-metric blind spot this paper warns about.

## Limitations / open questions
- Benchmarks bulk-mean / distributional response, not the discretized up/down/none label our tracks use — mapping their metrics onto a 3-class problem needs care.
- Rank metrics are relative within a dataset; absolute biological correctness (does this DEG really move?) is not directly certified.
- No macrophage CRISPRi dataset in the suite; transfer of its conclusions to our specific cell system is untested.
- Foundation-model embeddings (scGPT) were included only as features, not exhaustively tuned — open question whether newer FMs change the "simple wins" verdict.
