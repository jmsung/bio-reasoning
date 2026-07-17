---
source_url: https://doi.org/10.1038/s12276-025-01487-0
source_type: papers
title: "Perturbomics: CRISPR–Cas screening-based functional genomics approach for drug target discovery"
author: Park et al. (senior: Tackhoon Kim)
retrieved: 2026-07-16
doi: 10.1038/s12276-025-01487-0
---

# Perturbomics: CRISPR–Cas screening-based functional genomics approach for drug target discovery

**Authors:** Byung-Sun Park, Mieun Lee, Jaeyeol Kim, Tackhoon Kim
**Year:** 2025
**Venue:** Experimental & Molecular Medicine (2025), DOI 10.1038/s12276-025-01487-0

## Abstract
Review of "perturbomics" — the systematic annotation of gene function by
measuring phenotypic changes after gene-activity modulation. It traces the field
from early arrayed-siRNA screens (limited by off-target effects, variable
knockdown, throughput) to modern pooled CRISPR–Cas screens, then surveys recent
technical advances (engineered Cas9 variants, single-cell readouts, organoid/in
vivo models) and case studies where CRISPR screens found therapeutic targets in
cancer, immunotherapy, metabolism, cardiac/neuro disease, and regenerative
medicine. Closes with how data-rich perturbation screens now feed AI models that
predict perturbation phenotypes.

## Key contributions
- A structured taxonomy of CRISPR screen modalities: knockout (Cas9), CRISPRi
  (dCas9–KRAB repression), CRISPRa (dCas9–VP64/VPR/SAM activation), Cas13
  knockdown, base/prime-editor variant screens, and continuous-evolution
  platforms (TRACE, HACE, PEER-seq) that beat PAM/editing-window limits.
- Maps how single-cell readouts (Perturb-seq, CROP-seq, CRISP-seq,
  Perturb-CITE-seq) turn screens from bulk viability/FACS metrics into full
  transcriptomic phenotypes and gene-regulatory-circuit reconstruction.
- Curated tables of validated target genes across cancer vulnerabilities,
  immunotherapy, metabolism, and cell-fate/differentiation.

## Methods
Narrative review (not a benchmark). Organizes the CRISPR-screen workflow: design
an in-silico sgRNA library → clone into lentivirus/AAV → transduce
Cas9-expressing cells → apply selective pressure (drug, nutrient limitation,
FACS marker, immune coculture, in vivo graft) → deep-sequence sgRNA
enrichment/depletion → validate hits. Contrasts loss-of-function vs.
gain-of-function designs, combinatorial (dual-sgRNA) screens for synthetic
lethality, and increasingly physiological models (organoids, assembloids,
genetically engineered mouse models, iPS/ES-derived lineages).

## Key results
- Case-study targets validated by CRISPR screens: WRN (synthetic-lethal in
  MSI-high cancers), CIP2A–TOPBP1 and PKMYT1 (BRCA-mut / CCNE1-amplified
  synthetic lethality), FAM50A/FAM50B paralog pair, AMD1 (BRAF-inhibitor
  resistance via polyamine biosynthesis/OXPHOS).
- Immunotherapy: APLNR, TRAF3, PTPN2, ADAR1, SETDB1, CD58 (loss drives
  IFN-γ-independent immune evasion) as tumor-intrinsic immune-evasion genes.
- CRISP-seq reconstructed TF regulatory modules (M1–M4) in dendritic cells;
  CROP-seq showed LCK/ZAP70 knockout mimics naive-T-cell transcriptomes.
- AI link: GEARS integrates CRISPRa + Perturb-seq data to predict combinatorial
  perturbation effects; generative models applied to Perturb-seq for phenotype
  prediction.

## Why it matters for our work
Directly frames the biology behind the BioReasoning Challenge. Track A/B ask a
model to predict a gene's up/down/none regulatory response to perturbation —
exactly the phenotypic-readout problem perturbomics operationalizes
experimentally, and the Perturb-seq/CROP-seq datasets this review catalogs are
the data class those tracks draw on. The explicit "perturbomics in the era of AI"
section (GEARS, generative Perturb-seq models) positions LLM/agentic prediction
as the next step in this pipeline, and the CRISPRi/CRISPRa direction distinction
maps cleanly onto our up- vs. down-regulation labels. Useful as a domain-grounding
reference when reasoning about why a perturbation should raise or lower a gene.

## Limitations / open questions
- Review, not new data — no benchmark numbers or reproducible metrics of its own.
- Notes most screens still use oversimplified 2D cancer lines; organoid/in vivo
  screens don't yet scale to genome-wide pooled formats.
- Cas9 knockout is limited to protein-coding, frame-bearing genes and is
  copy-number/DSB-toxicity confounded; base/prime editors are capped to small
  edits in a PAM-defined window.
- AI-prediction discussion is brief and citation-level; no evaluation of how well
  current models generalize to unseen perturbations.
