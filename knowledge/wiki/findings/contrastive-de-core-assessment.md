---
title: CORE contrastive-LLM-DE likely won't transfer to our dual-OOD task — two concrete reasons
status: measured
cites:
  - domains/ai-reasoning/source/2026-yuan-plausibility-not-prediction-llm-perturbation.md
  - findings/direction-transfers-de-doesnt.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/curated-edges-fail-de-axis.md
---

# CORE contrastive-LLM-DE likely won't transfer to our dual-OOD task — two concrete reasons

[[../home]] | [[../index]]

**Status: measured — Goal-1 KB position + Goal-4 empirical result for `feat/de-contrastive-core`,
2026-07-17. Read the KB *before* building (the consult-first gate).**

Bottom line: Yuan et al. 2026 "Plausibility Is Not Prediction" (CORE) is genuinely **the one
LLM-DE framing with evidence** — it diagnoses the single-pair over-DE bias and fixes it with
*contrastive* evidence from a knowledge graph. But reading it against our own results, **CORE is
unlikely to move DE on *our* task**, for two concrete, independent reasons. This is a pre-build
kill argument; the surviving hypothesis is narrow.

## What CORE actually shows (Yuan 2026)

- LLMs over-call DE: a baseline predicts "yes" for **92.1%** of queries vs a **29.0%** true rate
  (Tahoe100M); per-gene discrimination near chance.
- Fix = **CORE**: retrieve related perturbations' known positive/negative outcomes from a
  biomedical KG, organize as contrastive evidence. Two variants:
  - **CORE-Voting** — aggregate the retrieved neighbours' outcomes. Per-gene AUROC **0.500 → 0.574
    (fixed budget) / 0.627 (full support)**, up to 0.703–0.711 on PerturbQA cell lines.
  - **CORE-Reasoning** — LLM reasons over the contrastive set. +26.0% AUROC / +19.8% acc / +28.6%
    F1 on drug data.

## Reason 1 — CORE-Voting *is* our already-failed neighbour-retrieval-DE

CORE-Voting = "retrieve related perturbations' known outcomes, aggregate." That is **exactly** our
neighbour-label-retrieval channel, which on our dual-OOD `holdout_split` scored **DE-AUROC 0.498 ±
0.006 — dead chance** ([[neighbor-retrieval-direction-lever]]), one of six independent DE channels
all at chance ([[direction-transfers-de-doesnt]]). CORE-Voting reaches 0.574–0.627 because its
benchmarks (PerturbQA / Tahoe cell lines) have **KG coverage of the query perturbations** and are
**not zero-overlap**. The paper is explicit: *"No zero-overlap regime like ours is directly
evaluated"* and *"sparse or biased graphs may not transfer to mouse-macrophage CRISPRi."* We are
that zero-overlap, sparse-coverage regime — and we already ran the voting mechanism. It's 0.498.

## Reason 2 — CORE's headline gains are bias-correction; AUROC is bias-invariant

CORE-Reasoning's large numbers (+19.8% acc, +28.6% F1) come from **fixing the over-DE
calibration bias** (92% "yes" → matched to the true rate). The paper's own limitation: gains are
*"largely from contrastive framing correcting bias, not from demonstrated perturbation-specific
mechanistic reasoning."* But **our metric is AUROC** — threshold-free and **invariant to a
systematic prediction bias** (uniformly shifting every score doesn't change the ranking). So the
mechanism behind most of CORE's improvement **does not apply to our scored axis.** Accuracy/F1
gains ≠ AUROC gains.

## The narrow surviving hypothesis

The only part not already ruled out: **CORE-Reasoning might add *rank* signal beyond neighbour-
voting** via genuine reasoning over the contrastive set (not just recalibration). Prior is low —
the paper attributes gains to bias-correction, and the rank-AUROC lever it does show (Voting) is
our 0.498 channel. But it's the one untested cell, so it earns a *cheap, gated* kill-test.

## Kill bar (set before building)

**DE-AUROC ≥ 0.55 on our dual-OOD OOD-val** (must beat neighbour-DE **0.498**) via `cfa_gate`, or
STOP and declare the LLM-DE angle exhausted → the **Perturb-seq data lane** ([[direction-transfers-de-doesnt]]:
"only new measured signal can move DE") is the path to rank-1. No moving the goalpost.

## Measured (feat/de-contrastive-core, 2026-07-17) — CORE-Voting KILLED empirically

Built the CORE machinery (`features/contrastive_context.py`, `models/core_de_scorer.py`) and ran
the voting variant on our dual-OOD split (`scripts/core_de_eval.py`, 5 seeds):

- **CORE-Voting DE-AUROC = 0.498 ± 0.006** (99% coverage) — **bit-for-bit the neighbour-retrieval-DE
  floor.** Does not clear the 0.55 kill bar. Reason 1 is now *measured*, not just argued: on our
  zero-overlap, sparse-KG regime the contrastive-aggregation mechanism is dead chance.
- **CORE-Reasoning** (LLM over the contrastive set) — **not run: endpoint-blocked** (Bing logprobs,
  same wall as `track-b-scoring-not-labeling`). Prior remains low (Reason 2: its gains are
  bias-correction, and AUROC is bias-invariant).

## Verdict

**The LLM-DE angle is exhausted** (7th DE approach at chance). CORE-Voting = 0.498 empirically;
CORE-Reasoning is a low-prior, endpoint-gated cell not worth waiting on. This closes the
prompt/framing lane for DE for the whole team: **only new measured signal moves DE**
([[direction-transfers-de-doesnt]]).

**Update (2026-07-17) — the Perturb-seq lane this page pointed to is now closed too.** The
"path to rank-1" framing above is superseded: `research/perturb-seq-real-lb-overlap` spent the
one real-LB read (baseline `fuse([GO, neighbour])` **0.585** → `+ external PerturbQA` **0.586**,
**Δ+0.001**, 66% coverage), confirming *end-to-end* — offline and on the board — that external
measured data moves DE nothing and the dual-OOD split is honest. With the static/data, curated-edge,
retrieval, and LLM-framing DE lanes all closed, the **only** remaining DE lever is model-based
token-logprob self-consistency — and it is **endpoint-blocked** (Bing logprobs). So DE-driven
rank-1 is currently **blocked**, not *open via more data*. The CORE machinery is kept so the
reasoning cell can be run in one script if a logprob endpoint ever lands — expected value low; do
not gate the roadmap on it.
