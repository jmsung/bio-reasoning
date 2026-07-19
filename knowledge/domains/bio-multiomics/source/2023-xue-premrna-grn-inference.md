---
source_url: https://doi.org/10.1101/gr.277488.122
source_type: papers
title: "Dissecting and improving gene regulatory network inference using single-cell transcriptome data"
author: Xue et al.
retrieved: 2026-07-16
doi: 10.1101/gr.277488.122
---

# Dissecting and improving gene regulatory network inference using single-cell transcriptome data

**Authors:** Lingfeng Xue, Yan Wu, Yihan Lin
**Year:** 2023
**Venue:** Genome Research

## Abstract
GRN inference from single-cell transcriptomes has long struggled to beat random
guessing. This paper systematically dissects *why* inference accuracy is limited
and shows that using **pre-mRNA** (rather than the typically used mature mRNA)
of target genes improves regulatory inference. Using chemical kinetic modeling
and simulated single-cell data, the authors show that a target gene's mature
mRNA level often fails to report upstream regulator activity because of gene-level
and network-level factors — a gap that pre-mRNA levels partially close. They
validate this on 30 public scRNA-seq data sets by using **intronic reads as a
proxy for pre-mRNA** (vs. exonic reads for mRNA), achieving higher inference
accuracy, and identify transcription-factor activity dynamics as a key modulator.

## Key contributions
- Delineates fundamental limits of GRN inference via kinetic modeling: mRNA half-life (hours) lags regulator dynamics, while pre-mRNA (splicing ~10 min) tracks it faster.
- Proposes using intronic reads from standard scRNA-seq as a practical pre-mRNA proxy — no new assay needed.
- Introduces **AEP** (average early precision), a top-network precision metric more robust than EPR/AUPR for sparse experimental GRNs.
- Provides a factor-dependency framework linking inference accuracy to gene kinetics, network motifs, and TF dynamics.

## Methods
Three tiers of evidence: (1) a single-gene chemical kinetic model quantifying how
splicing vs. degradation time scales bound inference accuracy; (2) synthetic
single-cell data from **dyngen** across linear/cycle/bifurcating/converging
backbones, reconstructed with **GENIE3** (random-forest) plus five other methods
(Pearson, propr, ARACNE, PIDC, TIGRESS), scored by AUPR; (3) 30 real 10x scRNA-seq
data sets, building pre-mRNA (intronic) and mRNA (exonic) count matrices, inferred
with GENIE3, evaluated against two ground truths — the high-confidence **DoRothEA**
network and the larger, lower-confidence **Motif GRN** — using AEP and AUPR.

## Key results
- In simulated data, the pre-mRNA method gave significantly higher AUPR than mRNA across all four network backbones, and consistently outperformed across all six inference algorithms; combining pre-mRNA + mRNA gave no advantage over pre-mRNA alone.
- Advantage is topology-dependent: largest for cycle backbones (dynamic regulators), smallest for bifurcating; reverses only when transcription rate is very low and regulation very slow.
- On real data, above ~0.15 precision pre-mRNA GRNs beat mRNA GRNs (DoRothEA); pre-mRNA won for most networks under Motif GRN, and the advantage survived subsampling reads to ~30%.
- Human forebrain (hFB): pre-mRNA reached ~50% precision at ~4% recall vs. mRNA's ~20% at ~2%.
- Accuracy is not correlated with intron/exon UMI depth — sparsity is not the dominant factor; TF activity dynamics (from scATAC-seq) predict the size of the pre-mRNA advantage.

## Why it matters for our work
The BioReasoning Track A/B up/down/none task is fundamentally a *directional gene
regulation* prediction. This paper is a caution and a lever: a target's steady-state
mRNA is a temporally lagged, often misleading readout of upstream TF activity, which
bounds how well any expression-based signal can predict regulatory direction. The
pre-mRNA/intronic-read idea suggests a concrete feature-engineering angle if
splicing-resolved counts are available, and the factor-dependency analysis (gene
kinetics, motifs, TF dynamics) offers a vocabulary for *why* certain
gene–perturbation pairs are intrinsically harder — useful for calibrating
confidence and abstention in our direction-prediction pipeline.

## Limitations / open questions
- Intronic reads are sparse in typical scRNA-seq, capping the pre-mRNA advantage; metabolic-labeling assays or cell aggregation are suggested remedies.
- Real-data evaluation depends on incomplete/noisy ground-truth GRNs (DoRothEA, Motif), so some data sets show mRNA winning.
- TF mRNA level remains a poor proxy for TF *activity* — the deeper unresolved bottleneck; regulon-summed pre-mRNA or activity estimation is proposed but untested here.
- Simulated networks were small due to compute limits; scaling behavior is unverified.
