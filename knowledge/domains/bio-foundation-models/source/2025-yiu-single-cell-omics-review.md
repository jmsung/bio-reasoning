---
source_url: https://doi.org/10.1186/s12967-025-07091-0
source_type: papers
title: "Transformative advances in single-cell omics: a comprehensive review of foundation models, multimodal integration and computational ecosystems"
author: Yiu et al.
retrieved: 2026-07-16
doi: 10.1186/s12967-025-07091-0
---

# Transformative advances in single-cell omics: a comprehensive review of foundation models, multimodal integration and computational ecosystems

**Authors:** Taylor Yiu, Bin Chen, Haoyu Wang, Genyi Feng, Qiangqiang Fu, Huijing Hu
**Year:** 2025
**Venue:** Journal of Translational Medicine (PMC12560279; PMID 41146276)

## Abstract
A PRISMA-guided review (692 articles screened → 141 included) synthesizing how
foundation models (FMs) borrowed from NLP are reshaping single-cell multi-omics.
It organizes the field into three interconnected domains: (1) architectural
innovations and self-supervised pretraining, (2) multimodal and spatial
integration, and (3) interpretability-driven optimization plus computational
ecosystems. It argues the shift is a paradigm change toward scalable,
generalizable frameworks rather than incremental gains, while flagging persistent
gaps in interpretability, benchmarking, and clinical translation.

## Key contributions
- Taxonomy of representative scFMs (Tables 1-3) with reported scale, modalities,
  zero-shot/cross-species capabilities, bias risks, and openness.
- Comparison of multimodal integration strategies (contrastive, tensor/low-rank
  fusion, graph/optimal-transport) and when each dominates.
- A proposed community benchmark ("SCFM-DREAM") with six tracks and a mixed-metric
  reporting standard (Tables 6) with known biases and scalability notes.
- A translational roadmap tying scFMs to FDA GMLP / IMDRF SaMD regulatory paths.

## Methods
Systematic literature review under PRISMA: 692 articles screened, 157 full-text
reviewed, 141 included; two independent reviewers with consensus resolution.
Inclusion required original research integrating single-cell omics with deep
learning foundation models. Synthesis is narrative + comparison tables; no new
model or experiment is trained.

## Key results
- **scGPT** pretrained on 33M+ cells; used as the recurring reference FM for
  zero-shot annotation and perturbation prediction.
- **Nicheformer**: 57M dissociated + 53M spatially-resolved cells for spatial
  niche reasoning; **AIDO.Cell** on 50M cells; **EpiAgent** (ATAC) on 5M cells.
- **scPlantFormer** (lightweight, 1M Arabidopsis cells): reported 92% cross-species
  annotation accuracy in plants; **CellPatch** cuts compute up to 80%.
- Explicit caveat: no single FM or integration strategy is universally "best";
  heterogeneous data/objectives demand task- and data-matched evaluation with
  uncertainty reporting. Cites evidence (Ahlmann-Eltze; Wong et al.) that simple
  linear baselines can match/beat deep models on perturbation prediction.
- Named failure modes: negative transfer under domain shift, inflated metrics on
  in-vitro cell lines with shared backgrounds, loss of rare-cell structure when
  optimizing purely for batch mixing.

## Why it matters for our work
This is a current (2025) map of the Track C foundation-model landscape and the
perturbation-prediction literature underlying Tracks A/B. It corroborates our own
finding (Track B LB 0.488) that FMs do not automatically beat simple baselines on
perturbation tasks, and warns that small/homogeneous CV inflates rank metrics —
directly matching our "don't trust small CV" lesson. Its mixed-metric,
stratified-by-rarity reporting guidance is a useful checklist for evaluating
up/down/none predictions honestly.

## Limitations / open questions
- A narrative review, not a benchmark: reported metrics (e.g., 92% plant accuracy)
  come from cited papers, not re-run here — treat as claims, not head-to-head.
- Some proposals (SCFM-DREAM suite, digital twins, exascale workflows) are
  aspirational, not established.
- Clinical translation remains largely preclinical/retrospective; interpretability
  and standardization gaps are stated but unsolved.
