---
source_url: https://doi.org/10.1093/bib/bbaf359
source_type: papers
title: "Inferring cell-type-specific gene regulatory network from cellular transcriptomics data with GeneLink+"
author: Zhang et al.
retrieved: 2026-07-16
doi: 10.1093/bib/bbaf359
---

# Inferring cell-type-specific gene regulatory network from cellular transcriptomics data with GeneLink+

**Authors:** Wei Zhang, Bowen Shao, Wenrui Li, Wenbo Guo, Jiaxin Lyu, Guangyi Chen, Chuanyuan Wang, Zhi-Ping Liu (Shandong University; Tsinghua University; CUHK)
**Year:** 2025
**Venue:** Briefings in Bioinformatics (2025), doi:10.1093/bib/bbaf359 (PMC12286779)

## Abstract
GeneLink+ infers cell-type-specific gene regulatory networks (ctGRNs) from transcriptomic data by framing GRN inference as **directed graph link prediction** — scoring causal TF→target edges. It extends the authors' earlier GENELink by replacing static graph attention (GAT) with **residual-GATv2 blocks** that combine a dynamic attention mechanism with residual/skip connections. This mitigates over-smoothing (node homogenization after many graph-convolution layers) that otherwise erases the distinct features of key regulator genes, and preserves cell-type-specific gene features for more interpretable, directional edge attribution. A **modified dot-product scoring scheme with learnable weights** adaptively prioritizes informative gene pairs. Benchmarked across seven scRNA-seq datasets, GeneLink+ matches or beats 10 SOTA methods, and applies to scRNA-seq, snRNA-seq, and spatial transcriptomics.

## Key contributions
- Residual-GATv2 encoder block: GATv2 dynamic attention + residual connections to fight over-smoothing and retain key-gene features.
- Modified dot-product scoring with learnable weights for directional (causal) edge attribution.
- A **hard-negative-sampling** train/eval protocol that removes an evaluation bias inflating AUROC/AUPRC on sparse ground-truth networks (fixed positive:negative ratios cause information leakage).
- Applicability across three modalities: scRNA-seq, snRNA-seq, and spatially resolved transcriptomics (SRT).

## Methods
For each of seven BEELINE-sourced scRNA-seq datasets (hESC, hHEP, mDC, mESC, mHSC-E/GM/L), gene subsets are TFs + 500 or TFs + 1000 most-variable genes, evaluated against three ground-truth network types (cell-type-specific ChIP-seq, non-specific ChIP-seq, STRING functional interactions; plus a LOF/GOF network for mESC), for 44 dataset configurations total. The model stacks residual-GATv2 attention layers (three layers chosen as the speed/accuracy sweet spot) to encode genes, then scores ordered gene pairs via the learnable dot product. Ground-truth ctGRNs for downstream applications are built by filtering database networks (hTFTarget, RegNetwork) with high-PCC/MI edges and PCA-CMI pruning to cut false positives.

## Key results
- Highest AUPRC of **0.81** on TFs+500 cell-type-specific hHEP, ~8% over next-best GNNLink.
- AUPRC **0.61** on TFs+500 LOF/GOF mESC, **~22%** over GNNLink.
- Outperforms or matches all 11 compared methods (GENIE3, GRNBoost2, SCODE, DeepSEM, CNNC, GNE, GENELink, GNNLink, PCC, MI) across the 7 datasets (mean over n=15 runs).
- Ablations: GATv2 > GAT; adding the residual module gives the largest gain; the modified dot product improves directional precision.
- Biology recovered: core TFs POU2F1/POU2F2 (B cells), TBX21/RUNX3 (CD4/CD8 T), CEBPA/CEBPB (CD14+ monocytes); microglia AD subnetworks; E2F1/FGFR1 rewiring in the DCIS→IDC breast-cancer transition.

## Why it matters for our work
Track A/B ask for the direction of a gene's response (up/down/none) to a perturbation — fundamentally a directed regulatory-edge question. GeneLink+ is a concrete, benchmarked recipe for **directional** TF→target link prediction on single-cell data, directly relevant to our direction-fusion work (residual-GATv2 as an over-smoothing-robust encoder, learnable-weighted dot product as a directional scorer). Its hard-negative-sampling caution also reinforces our own lesson (Track B) that small/biased splits give misleading rank metrics — a reason to distrust inflated CV.

## Limitations / open questions
- Ground-truth ctGRNs are semi-synthetic (database + PCC/MI filtering); "accuracy" is against imperfect reference networks, not experimentally validated causal edges.
- Requires a prior/background network (hTFTarget, RegNetwork) — not fully de novo.
- Benchmarked on curated gene subsets (TFs + 500/1000), not genome-scale; scalability to whole transcriptomes untested here.
- Gains over GNNLink are modest on non-specific ChIP-seq networks; the advantage is specific to cell-type-specific inference.
