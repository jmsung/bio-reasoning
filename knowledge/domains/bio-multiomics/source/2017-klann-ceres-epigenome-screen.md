---
source_url: https://doi.org/10.1038/nbt.3853
source_type: papers
title: "CRISPR–Cas9 epigenome editing enables high-throughput screening for functional regulatory elements in the human genome"
author: Tyler S. Klann et al.
retrieved: 2026-07-16
doi: 10.1038/nbt.3853
---

# CRISPR–Cas9 epigenome editing enables high-throughput screening for functional regulatory elements in the human genome

**Authors:** Tyler S. Klann, Joshua B. Black, Malathi Chellappan, Alexias Safi, Lingyun Song, Isaac B. Hilton, Gregory E. Crawford, Timothy E. Reddy, Charles A. Gersbach
**Year:** 2017
**Venue:** Nature Biotechnology

## Abstract
Millions of non-coding regulatory elements have been mapped by consortia and GWAS, but assigning function to them remains hard. This work introduces CERES (CRISPR–Cas9-based epigenomic regulatory element screening), a high-throughput method to test regulatory-element activity in native genomic context. Using catalytically dead Cas9 fused to a KRAB repressor (dCas9-KRAB) or a p300 activator (dCas9-p300), plus lentiviral sgRNA libraries targeting DNase I hypersensitive sites (DHSs) around a gene of interest, the authors run both loss- and gain-of-function screens at the β-globin and HER2 loci in human cells. CERES recovered known and novel regulatory elements, some of which were cell-type- or perturbation-direction-specific.

## Key contributions
- CERES: pooled epigenome-editing screen tiling gRNAs across DHSs (not the whole locus), enabling native-context functional annotation of candidate regulatory elements.
- Pairs repression (dCas9-KRAB) and activation (dCas9-p300) to probe both loss- and gain-of-function, revealing direction-dependent element behavior.
- Uses chromatin-accessibility (DNase-seq) DHS maps to focus the library, giving a larger effective window per gRNA than saturation tiling.

## Methods
DNase-seq DHSs around a target gene were used to design lentiviral gRNA libraries (10,739 gRNAs / 281 DHSs over a 4.5 Mb β-globin region; 12,189 gRNAs / 433 DHSs over a 4 Mb HER2 region), plus non-DHS control gRNAs. Cells stably expressing dCas9-KRAB or dCas9-p300 were transduced at low MOI (one gRNA/cell), selected, then FACS-sorted for the top and bottom 10% of target-gene expression (mCherry reporter for HBE1; immunostaining for HER2). gRNA abundance in each sorted population was measured by sequencing; DHSs were called by grouping gRNAs within a DHS and using linear regression on high-vs-low enrichment. Hits were validated with individual gRNAs (RT-qPCR, flow) and epigenetic marks confirmed by ChIP-qPCR (H3K27ac for p300, H3K9me3 for KRAB).

## Key results
- β-globin loss-of-function (dCas9-KRAB): the only DHSs enriched in low-HBE1 cells were the four LCR enhancers HS1–4 and the HBE1 promoter; HBG1/2 promoters enriched in high-HBE1 cells (competition relief). Screen vs individual-gRNA validation Spearman ρ = 0.9429 (mCherry) and ρ = 0.8857 (HBE1 mRNA).
- HER2 loss-of-function (dCas9-KRAB, A431): identified the HER2 promoter, intronic DHSs, and DHSs near the GRB7 promoter; validation ρ = 0.5175 (mRNA), ρ = 0.5701 (protein).
- HER2 gain-of-function (dCas9-p300, HEK293T): profile largely mirrored the KRAB screen in the opposite direction (promoter + first intron); validation ρ = 0.7818 (mRNA), ρ = 0.8545 (protein).
- Direction/cell-type dependence: an intronic DHS (DHS_1553) was a KRAB hit in A431 but not a p300 hit in HEK293T, yet was recovered by p300 in A431 — some elements are cell-type-specific, and repression and activation screens are complementary. A Cas9-mutagenesis saturation screen mostly hit coding exons and missed known regulatory elements, favoring the epigenome-editing approach.

## Why it matters for our work
CERES is a concrete demonstration that the *direction* of a perturbation (activate vs repress) and the *cell type* determine whether a regulatory element scores — directly relevant to the BioReasoning Challenge Track A/B up/down/none prediction, where a model must reason about direction-of-effect rather than just "is this element involved." It also grounds the biology of enhancer→gene regulation (LCR/HS enhancers, promoter competition, DHS-based candidate selection) that a reasoning system should encode when predicting how a genetic or epigenetic perturbation shifts target-gene expression.

## Limitations / open questions
- Only two loci (β-globin, HER2) in a handful of cell lines; generalization across the genome is untested here.
- Screens are per-DHS with a size cap (≤30–50 gRNAs/DHS), so within-element resolution (which TF motif) is coarse — the authors suggest follow-up saturation mutagenesis.
- KRAB/p300 asymmetry means a single-direction screen can miss real elements; comprehensive annotation requires both, roughly doubling cost.
- Validation correlations for HER2 were moderate (ρ ≈ 0.52–0.57 in the KRAB screen), reflecting noise in native-context functional readouts.
