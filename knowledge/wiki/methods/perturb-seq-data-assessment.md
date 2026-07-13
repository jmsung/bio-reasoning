---
title: Assessing external Perturb-seq datasets — compute plan & tooling
cites:
  - source/2022-replogle-genome-scale-perturb-seq.md
  - source/2021-papalexi-eccite-seq-immune-checkpoints.md
  - source/2016-dixit-perturb-seq.md
  - source/2024-peidli-scperturb.md
  - findings/housekeeping-transfer-hypothesis.md
---

# Assessing external Perturb-seq datasets — compute plan & tooling

How to evaluate candidate augmentation datasets (roadmap #2) without drowning in
compute. **Core principle: work at pseudobulk level first.** Almost every
augmentation-audit question (which perturbations overlap ours, effect sizes,
cross-cell-type consistency) needs *per-perturbation mean profiles*, not
individual cells — and pseudobulk is laptop-sized even when the raw data is not.

## Two levels of assessment

| Level | Uses | Size | Hardware |
|---|---|---|---|
| **Metadata + pseudobulk** | perturbation lists, per-perturbation mean expression, DE summaries, cross-cell-type correlation | MBs–~1 GB | laptop |
| **Full single-cell** | all cells in memory, reprocessing, single-cell modeling/training | tens–100+ GB | server (RAM, maybe GPU) |

## Per-dataset compute

| Dataset | Full single-cell | Laptop? | Note |
|---|---|---|---|
| Papalexi (THP-1) [[2021-papalexi-eccite-seq-immune-checkpoints]] | <1 GB | yes | small |
| Dixit (mouse DC) [[2016-dixit-perturb-seq]] | a few GB (~200K cells) | yes | pseudobulk easy |
| Replogle GW (K562) [[2022-replogle-genome-scale-perturb-seq]] | ~30–100+ GB (~2.5M cells) | pseudobulk yes / full no | full → server (≥64 GB RAM); pseudobulk <1 GB |
| Replogle essential (K562/RPE1) | a few GB each | pseudobulk yes | powers the housekeeping cross-cell-type test |
| scPerturb (per dataset) [[2024-peidli-scperturb]] | 100s MB–~10 GB each | pick & choose | download only relevant subsets |

## Hardware rule of thumb

- **< ~100K cells** → any laptop (8–16 GB RAM).
- **100K–1M cells** → 32 GB RAM, or `anndata` backed mode.
- **> 1M cells in memory** (full Replogle GW) or **any model training** → server.
- **GPU** → only for Track C fine-tuning / foundation-model or GEARS-style
  training. *Not* needed for EDA/assessment. Track A is API-based (no local GPU).

## Tooling

- `scanpy` + `anndata` for `.h5ad`; `pertpy` for one-line dataset loaders
  (Replogle, Papalexi, Norman, …). Not yet repo deps — add in their own PR.
- **Big-file trick:** `anndata.read_h5ad(path, backed='r')` reads from disk
  without loading the full matrix into RAM — lets a laptop inspect Replogle GW.
- Compute pseudobulk by grouping cells on the perturbation label and taking the
  mean (chunk/stream if backed).

## Staged plan

1. **Stage 1 — laptop:** pull metadata + pseudobulk for the four candidates; run
   the augmentation-audit questions, including the **housekeeping K562↔RPE1
   invariance test** (do housekeeping-gene perturbations correlate across the two
   Replogle cell types more than immune/lineage genes? — [[housekeeping-transfer-hypothesis]]).
   All <a few GB, <16 GB RAM.
2. **Stage 2 — server:** only if Stage 1 warrants it — full single-cell
   integration, or Track C training (server + GPU).

**Species caveat:** most candidates are human (K562/THP-1/RPE1); our Track A data
is mouse → ortholog mapping needed before cross-dataset comparison. Dixit (mouse)
is the exception.

- **Possible bridge — UCE (Universal Cell Embedding).** A candidate way around the
  ortholog-mapping step: UCE grounds gene identity in **ESM2 protein embeddings**,
  giving a **species-agnostic, zero-shot** cell/gene representation across 8 species
  (knowledge-base `domains/bio-foundation-models/source/2026-rosen-universal-cell-embedding.md`).
  It embeds cells into one shared latent space, so human external Perturb-seq and
  mouse macrophages could in principle be compared/borrowed without an explicit
  ortholog map. **Caveat:** UCE is a *representation* model, not a perturbation
  predictor — it does not model knockdown direction; use it only as a cross-species
  feature/bridge for the augmentation lead, not as the predictor itself. Untested here.
