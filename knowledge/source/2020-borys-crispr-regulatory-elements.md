---
source_url: https://doi.org/10.1186/s12864-020-6497-0
source_type: papers
title: "Identification of functional regulatory elements in the human genome using pooled CRISPR screens"
author: Borys & Younger
retrieved: 2026-07-16
doi: 10.1186/s12864-020-6497-0
---

# Identification of functional regulatory elements in the human genome using pooled CRISPR screens

**Authors:** Samantha M. Borys, Scott T. Younger
**Year:** 2020
**Venue:** BMC Genomics (2020), doi:10.1186/s12864-020-6497-0

## Abstract
Genome-scale pooled CRISPR screens are powerful tools for finding genetic
dependencies, but nearly all published screens perturb protein-coding genes —
which are <2% of the genome — leaving noncoding regulatory elements
(promoters, enhancers, silencers) largely uninterrogated. This work develops a
CRISPR-based screening framework that functionally profiles thousands of
noncoding regulatory elements in parallel. Using the tumor suppressor p53 as a
model, the authors built a pooled CRISPR library targeting thousands of p53
binding sites genome-wide, transduced it into dCas9-KRAB (CRISPRi) cells, and
identified regulatory elements that influence cell proliferation and the
p53-mediated DNA damage response. Many functional elements lie deep within
intergenic regions with no prior functional annotation.

## Key contributions
- A generalizable pooled-CRISPR framework for high-throughput functional
  profiling of noncoding regulatory elements (not just genes).
- Direct head-to-head comparison of CRISPRi (dCas9-KRAB) vs CRISPRko (Cas9) for
  perturbing regulatory elements — CRISPRi is recommended.
- Demonstration that regulatory elements can be functionally dissociated from
  their nearest protein-coding gene.

## Methods
Two libraries were built against previously reported p53 ChIP-Seq data in the
renal adenocarcinoma line 769P (selected because p53 knockout confers a
proliferative advantage only in wildtype-p53 lines, per Project Achilles). A
gene-targeting library carried 4 sgRNAs each against 330 predicted p53 target
genes; a peak-targeting library carried 11,434 sgRNAs against 4,930 p53
consensus motifs (CWWG[N]2-12CWWG) within 2,036 ChIP-Seq peaks, tiling all
PAM-containing sites within 16 bp of each motif, plus intergenic and
non-targeting controls. Screens ran in Cas9 or dCas9-KRAB 769P cells (MOI ~0.5,
1,000 cells/sgRNA, 21 days), analyzed with MAGeCK; DNA-damage screens added
250 nM doxorubicin. Selected hits were validated with individual sgRNAs via
proliferation and cell-cycle (S-phase) assays.

## Key results
- p53-targeting sgRNAs were among the most enriched, validating the assay; the
  proliferation advantage of p53 knockout was specific to wildtype-p53 lines.
- CRISPRi identified functional elements up to >200–250 kb from any annotated
  gene (e.g. Peak 384, Peak 685) — most functional peaks sat >10 kb from a TSS.
- Peak 1267 (in the TNFRSF10A intron) altered proliferation even though
  TNFRSF10A knockout did not — regulatory elements dissociate from proximal genes.
- Validation: repressing Peak 975 or Peak 685 blocked doxorubicin-induced
  arrest (4.27% and 3.72% cells in S-phase vs 0.5% for controls).
- CRISPRi and CRISPRko showed minimal overlap; CRISPRi better recapitulated
  known biology (degenerate p53 motifs tolerate Cas9 indels), so CRISPRi is
  preferred for regulatory-element screens.

## Why it matters for our work
The BioReasoning Challenge asks models to predict up/down/none directional
effects of perturbations on cellular phenotypes. This paper is a source of
ground-truth causal regulatory relationships beyond gene bodies: which noncoding
p53 binding sites, when repressed, drive proliferation or DNA-damage-response
phenotypes — and its striking finding that proximity to a gene does not predict
function is a caution for any Track A/B model that infers regulation from
distance-to-TSS or nearest-gene heuristics. The CRISPRi-vs-CRISPRko divergence
also warns that the perturbation modality shapes the observed direction, which
matters for reasoning over heterogeneous perturbation datasets.

## Limitations / open questions
- Single TF (p53), single cell line (769P) — generality across TFs/contexts untested.
- The actual gene targets of the intergenic regulatory elements were not
  identified; p53-independent mechanisms cannot be excluded.
- No optimized sgRNA design rules exist for regulatory elements, causing high
  guide-to-guide variability and possible off-target concerns for singly-targeted motifs.
