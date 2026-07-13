---
source_url: https://www.cell.com/cell-systems/fulltext/S2405-4712(25)00179-6
source_type: papers
title: Integrated time-series analysis and high-content CRISPR screening delineate the dynamics of macrophage immune regulation
author: Traxler et al.
year: 2025
retrieved: 2026-07-13
---

# Integrated time-series analysis and high-content CRISPR screening delineate the dynamics of macrophage immune regulation

**Authors:** Peter Traxler, Stephan Reichl, Lukas Folkman, Lisa Shaw, Victoria Fife, Amelie Nemc, Djurdja Pasajlic, Anna Kusienicka, Daniele Barreca, Nikolaus Fortelny, André F. Rendeiro, Florian Halbritter, Wolfgang Weninger, Thomas Decker, Matthias Farlik, Christoph Bock
**Year:** 2025
**Venue:** Cell Systems (vol. 16, iss. 8, art. 101346; DOI: 10.1016/j.cels.2025.101346)

> Note: distilled from the open lab page (medical-epigenomics.org/papers/traxler2025) + GitHub/GEO metadata; the Cell Systems full text is paywalled (HTTP 403). Method magnitudes below are from the abstract/lab summary, not the full results tables.

## Abstract
The authors build a time-resolved regulatory map of how murine macrophages respond to immune stimuli. They profile gene expression (RNA-seq) and chromatin accessibility (ATAC-seq) across a time course under multiple stimulation conditions, then functionally test candidate regulators at scale with a combined CROP-seq + CITE-seq single-cell CRISPR screen. Integrating the time-series and perturbation data yields molecular drivers of pathogen-induced macrophage dynamics and a broadly reusable method for dissecting immune-regulatory programs.

## Key contributions
- Time-resolved multi-omic (transcriptome + chromatin) atlas of macrophage response to six distinct immune stimuli.
- High-content single-cell CRISPR screen (CROP-seq fused with CITE-seq surface-protein readout) linking gene knockouts to transcriptional + phenotypic states.
- Assigns new regulatory roles in immune homeostasis and pathogen response to transcription, splicing, chromatin, and Mediator-complex factors.
- Public, reproducible pipeline (Snakemake) + full GEO data release.

## Methods
- **Cell system:** murine (mouse) macrophages.
- **Stimuli/perturbations:** six immune stimuli in the time-series; *Listeria monocytogenes* infection highlighted for detailed CROP-seq analysis.
- **Time-series:** paired RNA-seq (GSE263759) and ATAC-seq (GSE263758) sampled across multiple time points per condition.
- **CRISPR screen:** CROP-seq + CITE-seq. A proof-of-concept KO15 screen (15 target genes; GSE263760) scaled to a KO150 screen (150 target genes; GSE263761). Single-cell readout of each knockout's effect on expression and surface markers. SuperSeries: GSE263763.
- **Code:** github.com/epigen/macrophage-regulation (Snakemake workflows); supplemental tables S1–S6.

## Key results
- Identified/confirmed regulatory roles for transcription factor **Spi1/PU.1** and **JAK-STAT** pathway members in macrophage homeostasis and pathogen response.
- Macrophage activity modulated by splicing proteins **SFPQ** and **SF3B1**, histone acetyltransferase **EP300**, cohesin subunit **SMC1A**, and Mediator subunits **MED8** and **MED14** — implicating splicing, chromatin looping, and the Mediator complex as immune-response modulators.
- Produced a time-resolved regulatory map showing crosstalk among immune signaling pathways during pathogen response. (Effect-size magnitudes are in the paywalled results tables; not captured here.)

## Why it matters for our work
Our Track A/B data are **CRISPRi knockdowns in mouse macrophages**, predicting `(perturbation gene, target gene) → up/down/none`. This paper is our **exact cell type and near-exact assay** — a CRISPR perturbation × single-cell transcriptomic readout in murine macrophages under immune stimulation — making it a strong source of macrophage-specific regulatory priors and a candidate augmentation/grounding dataset (RNA-seq/ATAC-seq/CROP-seq all on GEO under GSE263763).

Concretely:
- The **KO150 gene list** (GSE263761) is a curated set of macrophage immune regulators; overlap with our perturbation-gene set would let us borrow ground-truth perturbation→expression links directly. Worth cross-referencing the exact target list against ours.
- Named regulators (**Spi1/PU.1, JAK-STAT, EP300, SFPQ, SF3B1, SMC1A, MED8/14**) are priors for *which perturbations drive immune programs* — e.g. PU.1 as a master macrophage TF should show broad, high-magnitude downstream effects; Mediator/cohesin/splicing factors act as general amplifiers/repressors rather than program-specific TFs. This can inform how we weight "hub" perturbations vs. peripheral ones.
- The **ATAC-seq time-series** gives accessibility-based regulatory-link priors (TF→target) that could ground a `(pert, target) → direction` model beyond expression alone.

**Caveat:** their assay is CRISPR **knockout** (CROP-seq) under active stimulation; ours is CRISPR**i knockdown**. Direction of effect should transfer, but magnitude/completeness differ (KO vs. partial knockdown), and stimulation context may not match our baseline condition — verify before using as hard labels.

## Limitations / open questions
- Distilled from abstract + metadata only; per-gene effect magnitudes and the full KO150 target list are in the paywalled paper/supplement — need the PDF or GEO supplementary tables to confirm gene-set overlap with our tracks.
- Exact time points and number of primary vs. cell-line macrophages not confirmed here.
- KO (this paper) vs. CRISPRi (our data) mismatch: quantitative transfer of effect sizes is unverified.
- Stimulus panel (incl. *Listeria*) is pathogen-driven; how well findings generalize to our unstimulated/baseline condition is open.
