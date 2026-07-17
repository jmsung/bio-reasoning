---
source_url: https://doi.org/10.64898/2025.12.15.694070
source_type: papers
title: "Comprehensive perturbation of transcription factors in human cardiomyocytes reveals the regulatory architecture of congenital heart disease"
author: Chikara Takeuchi et al. (senior: Gary C. Hon)
retrieved: 2026-07-16
doi: 10.64898/2025.12.15.694070
---

# Comprehensive perturbation of transcription factors in human cardiomyocytes reveals the regulatory architecture of congenital heart disease

**Authors:** Chikara Takeuchi, Sushama Sivakumar, Anjana Sundarrajan, Yihan Wang, Sean C. Goetsch, Huan Zhao, Lei Wang, Mpathi Nzima, Minnie Deng, Kartik N. Kulkarni, Lin Xu, Jun Wu, Bruce A. Posner, Maria H. Chahrour, W. Lee Kraus, Nikhil V. Munshi, Gary C. Hon (UT Southwestern)
**Year:** 2026
**Venue:** bioRxiv (preprint)

## Abstract

Over 100 genes are implicated in congenital heart disease (CHD), yet >50% of CHD
is genetically unexplained. The authors systematically CRISPRi-perturb **1983
transcription factors** (1747 DNA-binding + 236 epigenetic regulators) during
iPSC-to-cardiomyocyte differentiation using an optimized Perturb-Seq platform,
plus **981 putative TF enhancers**. They derive experimental TF-gene regulatory
networks, use them to map the regulatory architecture of CHD, deorphanize
under-sampled CHD TFs, and build **Percoder**, a Set-Transformer model that
predicts perturbed TFs from transcriptomes and interprets CHD patient data.

## Key contributions

- Largest cardiomyocyte TF Perturb-Seq to date: 1983 TFs, 765,351 QC-passed cells.
- Experimentally-derived GRN (25,615 TF-gene edges; 1316 TFs → 7122 genes),
  shown to be scale-free (power-law exponent 2.04) with hub CHD genes.
- Enhancer Perturb-Seq (981 enhancers of 107 TFs) linking non-coding CHD variants
  to TF phenotypes.
- **Percoder**: a Set-Transformer that classifies perturbed TFs from unlabeled
  cell-set transcriptomes and generalizes to out-of-sample and patient data.

## Methods

CRISPRi (dCas9-KRAB) pooled knockdown with expressed guide barcodes, read out by
scRNA-Seq across cardiac differentiation. A PCA-based **energy-distance** metric
scores transcriptome-wide phenotypes; **cNMF** defines 250 gene programs; reverse
PageRank ranks CHD-gene regulators. Dosage sensitivity is inferred from linear
(sensitive) vs exponential (buffered) TF-expression-to-phenotype fits across
multiple sgRNAs per TF. Percoder pools cells with a Set Transformer + softmax
classifier, using a conditional VAE (scVI) to calibrate batch effects for
out-of-sample prediction; ZINB modeling, all-genes input, and online label
smoothing improved accuracy.

## Key results

- **209 significant TF regulators** identified; strongly enriched for known CHD
  genes (p=4.4e-14) and de novo variant TFs (p=1.7e-4).
- Guilt-by-association deorphanizes under-sampled CHD TFs (CHAMP1, HMG20A, BPTF,
  ZSCAN10); CHAMP1 KD delays differentiation, confirmed by TNNT2 staining.
- CHD genes are hubs: MYH7 regulated by 71 TFs; 50 CHD genes averaged 7.4 TFs each.
- 144 TF-TE regulatory interactions; 5 dosage-sensitive TFs (ARID4B, RB1CC1,
  SOX4, TBX5, ZNF608).
- **Percoder**: 48.7% cell-sets correctly classified (102x random); 193/210
  perturbations AUC>0.75; predicts YAP1/ARNT/HIF1A in HLHS patient iPSC-CMs and
  TBX20/RB1/ATMIN in a GLYR1-mutant model, matching original studies.

## Why it matters for our work

Directly relevant to Tracks A/B: this is a large **CRISPRi-knockdown Perturb-Seq
resource** where the core task — inferring which TF was perturbed and its
downstream up/down effects — mirrors our up/down/none prediction. Percoder is a
concrete precedent that a **set-of-cells transformer** beats single-cell
prediction (they note it "dramatically outperforms" single-cell approaches like
the STATE model), informing Track C architecture choices. The experimentally
derived, scale-free GRN and gene programs are candidate priors/features for
perturbation-response modeling in a cardiac (vs our macrophage) context.

## Limitations / open questions

- Human iPSC-cardiomyocyte context; transfer to other cell types (e.g. our
  mouse macrophages) requires ortholog/context mapping.
- CRISPRi knockdown only (loss-of-function); no over-expression / gain-of-function.
- Percoder classifies among a fixed set of trained perturbations — misclassifies
  functionally redundant TFs and does not predict unseen regulators.
- Preprint (bioRxiv); many findings validated only by qPCR/IF on selected TFs.
