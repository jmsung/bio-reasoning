---
source_url: https://doi.org/10.1101/2024.09.06.611573
source_type: papers
title: "CRISPRi with barcoded expression reporters dissects regulatory networks in human cells"
author: Jinyoung Kim et al.
retrieved: 2026-07-16
doi: 10.1101/2024.09.06.611573
---

# CRISPRi with barcoded expression reporters dissects regulatory networks in human cells

**Authors:** Jinyoung Kim, Ryan Y. Muller, Eliana R. Bondra, Nicholas T. Ingolia
**Year:** 2024
**Venue:** bioRxiv (preprint; PMC11398470)

## Abstract
The paper extends CiBER-seq (CRISPR interference with barcoded expression reporter sequencing) — previously established in budding yeast — to human cells. CiBER-seq couples a transcriptional reporter with a genome-scale sgRNA library, embedding a unique RNA barcode in the reporter for each sgRNA so that barcode abundance measured by bulk RNA sequencing reflects reporter activity in cells carrying that perturbation. The authors optimize single-copy integration of highly complex barcoded libraries into a defined human locus, control false discovery at the guide level, and apply the platform to an NF-κB reporter, recovering the canonical TNF-α → NF-κB signaling cascade from bulk RNA-seq alone with high time resolution.

## Key contributions
- First adaptation of CiBER-seq to mammalian (human K562) cells.
- Bxb1 recombinase "landing pad" in the AAVS1 safe-harbor locus for efficient single-copy integration of a genome-wide barcoded dual-sgRNA library (21,554-member pool, ~8 barcodes per sgRNA).
- Dual-SFFV control screen to quantify and correct barcode-dependent noise, enabling a reusable normalization for lower-coverage screens.
- Genome-scale NF-κB screen reading out a molecular (transcriptional) phenotype from bulk RNA-seq with sub-fluorescence time resolution.

## Methods
Starting from K562 lines expressing dCas9-KRAB (constitutive or dox-inducible), the authors introduced an attP landing pad, over-expressed Bxb1 to boost recombination, and nucleofected a modular donor library carrying two random 25-nt barcodes flanking an insertable reporter. Nucleofection integrated the library in ~29% of cells without selection. For screening, cells were selected to >500x coverage per barcode and >4000x per sgRNA, RNA was reverse-transcribed with UMI-tagged gene-specific primers, and barcode/UMI counts were analyzed with DESeq2, comparing matched reporter vs. constitutive-partner barcodes. For NF-κB, a synthetic 3× NF-κB-motif mCherry reporter (with constitutive iRFP partner) was assayed after 2 h and 5 h of TNF-α (5 ng/mL) stimulation.

## Key results
- Control dual-SFFV screen: none of 167,916 barcodes differed significantly between CRISPRi-induced/uninduced; only 13 of 21,446 sgRNAs showed a weak marginal effect — establishing low technical noise.
- Constitutive iRFP barcode counts correlated across timepoints at Spearman ρ = 0.992–0.993.
- NF-κB screen recovered hundreds of significant sgRNAs while the vast majority of 989 non-targeting sgRNAs had no effect; RELA (top hit) and REL scored strongest, plus TNFRSF1A, TRADD, SHARPIN, MAP3K7, the full IKK complex (IKBKG, CHUK, IKBKB), and SCF components (CUL1, FBXW11 — 2nd-ranked hit).
- 2 h and 5 h timepoints gave concordant hits (no significant differences between them), showing clear signal at an early point before fluorescence is detectable (mCherry only separable ~5 h by flow).
- Individual validation: 70–98% knockdown; canonical hits plus non-canonical NELFA and GNG12 blocked reporter induction.

## Why it matters for our work
CiBER-seq is a high-throughput source of causal gene→transcriptional-response perturbation data — exactly the up/down/none regulatory signal the BioReasoning Challenge Track A/B tasks ask models to predict. Its clean recovery of a known signaling cascade (direction and pathway membership) from bulk RNA-seq makes it a candidate ground-truth or benchmark for gene-regulation reasoning, and its molecular-phenotype readout complements single-cell Perturb-seq datasets already in our wiki (e.g., Replogle genome-scale Perturb-seq) as a lower-cost, faster-kinetics view of directed regulatory edges.

## Limitations / open questions
- Demonstrated on a single reporter pathway (NF-κB) in one cell line (K562); generality across pathways/cell types is asserted but not shown at scale.
- Reads out one engineered reporter at a time, not the whole transcriptome — pathway coverage is defined by reporter choice.
- Some pathway intermediates (adapters) were missed because single-gene knockdown does not always block signaling; sgRNA dropout also removed some genes.
- Preprint (not yet peer-reviewed at retrieval); barcode-dependent effects require the dual-SFFV normalization to fully control at low coverage.
