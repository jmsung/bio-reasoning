---
source_url: https://doi.org/10.1126/sciadv.abi4360
source_type: papers
title: "Parallel characterization of cis-regulatory elements for multiple genes using CRISPRpath"
author: Xingjie Ren et al.
retrieved: 2026-07-16
doi: 10.1126/sciadv.abi4360
---

# Parallel characterization of cis-regulatory elements for multiple genes using CRISPRpath

**Authors:** Xingjie Ren, Mengchi Wang, Bingkun Li, Kirsty Jamieson, Lina Zheng, Ian R. Jones, Bin Li, Maya Asami Takagi, Jerry Lee, Lenka Maliskova, Tsz Wai Tam, Miao Yu, Rong Hu, Lindsay Lee, Armen Abnousi, Gang Li, Yun Li, Ming Hu, Bing Ren, Wei Wang, Yin Shen
**Year:** 2021
**Venue:** Science Advances

## Abstract
CRISPRpath is a pooled CRISPR screening strategy that characterizes cis-regulatory elements (CREs) for multiple genes at once by choosing target genes that converge on a single well-defined biological pathway, so a single cell-survival phenotype reports on all of them. The authors screen candidate enhancers for six genes (HPRT1, MSH2, MSH6, MLH1, PMS2, PCNA) in the 6-thioguanine (6TG)–induced mismatch-repair (MMR) pathway in human iPSCs. Cells with impaired MMR (from silenced enhancers) survive 6TG, converting enhancer function into a selectable readout. By comparing CRISPRi vs. CRISPRn and varying selection pressure (6TG dose), CRISPRpath identifies active enhancers, ranks them by effect size, and links strong/weak enhancers to distinct chromatin and TF-motif signatures.

## Key contributions
- A scalable pooled-screen design that characterizes enhancers for *multiple* genes simultaneously by exploiting a shared pathway phenotype (cell survival), rather than one reporter/gene.
- Direct head-to-head comparison of CRISPRi (dCas9-KRAB) vs. CRISPRn (Cas9 nuclease) with an identical sgRNA library in the same genetic background.
- Tunable selection pressure (6TG dose) to quantitatively separate strong from weak enhancers.

## Methods
The library targeted ATAC-seq open-chromatin peaks within ±1 Mb of each of the six genes (10.6 Mb total): 35,763 sgRNAs (32,383 distal, 2,755 proximal/TSS+coding, 625 non-targeting), averaging 110 sgRNAs per peak; after filtering to high-specificity guides (GuideScan score >0.2, no ≤2-mismatch off-targets), 12,702 sgRNAs (~38/peak) were analyzed. Two engineered WTC11 iPSC lines (dox-inducible dCas9-KRAB and dox-inducible Cas9) were transduced at MOI 0.5, treated at three 6TG doses (1×=80, 2×=160, 3×=240 ng/ml), and survivors sequenced 7 days later. Enrichment vs. control was computed with edgeR/TMM (negative-binomial model); the 5th percentile of non-targeting p-values set an empirical 5% FDR, and enriched sgRNAs required fold change >2. A CRE was called an enhancer if ≥3 enriched sgRNAs targeted it. Hits were validated by CRISPRi + RT-qPCR, shRNA controls, and luciferase assays, and profiled with ATAC-seq, H3K4me3, H3K27ac, CTCF, RNA-seq, and H3K4me3 PLAC-seq.

## Key results
- 66 unique enhancers identified across the six genes; analysis focused on 63 from the 2×/3× CRISPRi screens (62 at 2×, 33 at 3×). CRISPRn recovered far fewer (19 at 2×, none at 3×) — CRISPRi outperformed CRISPRn for CRE screening.
- 2× and 3× screens were highly reproducible (Spearman ρ = 0.97 CRISPRi, 0.84 CRISPRn); 1× correlated poorly, so higher selection pressure reduces noise.
- Enhancers sit a mean ~530 kb from their target TSS (~10 intervening genes); weak negative correlation between enrichment score and distance (Pearson r = −0.36, P = 0.01).
- 60% (38/63) of enhancers overlapped annotated promoters ("enhancer-like promoters"), which had higher accessibility, H3K4me3/H3K27ac, transcription, and more chromatin interactions than control promoters.
- Strong enhancers (n=33, 3×) vs. weak (n=30, 2×) were separable by effect size: CRISPRi of strong enhancers cut target expression ~21% vs. ~6% for weak (TSS perturbation ~68%). Individual chromatin marks did not separate strong from weak, but combined active-mark signatures and TF motifs (SP/KLF, E2F enriched in strong) did.

## Why it matters for our work
The BioReasoning Challenge asks models to predict the direction of a gene's expression change (up/down/none) after a perturbation. CRISPRpath is a clean source of ground-truth enhancer→gene effects with graded magnitudes: which distal elements regulate which of six MMR/metabolism genes, and by how much. Its two headline findings are directly useful priors for Track A/B reasoning — (1) most enhancer perturbations produce *small* down-regulation (single-digit to ~20%), a caution against over-predicting large "up/down" effects and a rationale for a strong "none"/near-zero baseline; and (2) enhancer strength is encoded in *combined* chromatin signatures and TF-motif composition, not any single mark. It also documents that enhancers act at long range (~530 kb, ~10 genes away) and that promoters frequently double as enhancers — features a model must handle when linking regulatory elements to targets. For Track C foundation models, the graded strong/weak enhancer set is a candidate benchmark for effect-size calibration.

## Limitations / open questions
- CRISPRi cannot fully silence enhancers, so measured effect sizes are lower bounds; luciferase assays disagreed with in-context effect sizes and could not distinguish strong vs. weak.
- Small sample per gene: PLAC-seq contact-frequency differences between strong/weak enhancers were suggestive but not statistically significant; MSH2/MSH6 had to be excluded from distance analyses (too close to assign enhancers).
- Effect sizes are pathway- and cell-type-specific (iPSC, MMR genes); broadly expressed genes show small effects, so magnitudes may not transfer to cell-type-specific loci.
- The approach requires a convergent, selectable pathway phenotype — not every gene set qualifies.
