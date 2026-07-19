---
source_url: https://doi.org/10.1038/s41592-024-02191-z
source_type: papers
title: "Toward universal cell embeddings: integrating single-cell RNA-seq datasets across species with SATURN"
author: Yanay Rosen et al.
retrieved: 2026-07-16
doi: 10.1038/s41592-024-02191-z
---

# Toward universal cell embeddings: integrating single-cell RNA-seq datasets across species with SATURN

**Authors:** Yanay Rosen, Maria Brbić, Yusuf Roohani, Kyle Swanson, Ziang Li, Jure Leskovec
**Year:** 2024
**Venue:** Nature Methods

## Abstract
Joint analysis of single-cell RNA-seq datasets across species is normally limited to one-to-one homologous genes, discarding most biologically relevant genes and worsening as more species are added. SATURN (Species Alignment Through Unification of Rna and proteiNs) is a deep-learning method that learns *universal cell embeddings* by coupling RNA expression with protein embeddings from a protein language model (ESM2). This lets it integrate datasets from different species regardless of genomic similarity, transfer cell-type annotations across evolutionarily remote species, and redefine differential expression in a cross-species setting.

## Key contributions
- Introduces **macrogenes**: learned groups of functionally related intra- and inter-species genes sharing similar protein-language-model embeddings, replacing the one-to-one homolog bottleneck.
- Couples gene expression with **protein language model (ESM2)** representations so functional similarity — including remote homology missed by sequence-alignment tools — drives integration.
- Enables **multispecies differential expression** in macrogene space, characterizing conserved and divergent gene programs across species.

## Methods
SATURN takes scRNA-seq counts from one or more species, ESM2 protein embeddings of each species' proteins, and initial within-species cell annotations (clustered if unavailable). It maps genes to a shared macrogene space where a gene's importance to a macrogene is a learned neural-network weight reflecting protein-embedding similarity. The network is first pretrained as an autoencoder with a zero-inflated negative binomial (ZINB) loss, regularized to reconstruct protein-embedding similarities via the gene-to-macrogene weights. Using this as initialization, SATURN then applies a weakly supervised metric-learning objective that pushes dissimilar cells within a dataset apart while pulling similar cells across datasets together, integrating species while preserving within-species cell-type structure.

## Key results
- Built a **mammalian cell atlas of 335,000 cells** across nine tissues integrating Tabula Sapiens (human), Tabula Microcebus (mouse lemur) and Tabula Muris (mouse); also integrated frog (97,000 cells) and zebrafish (63,000 cells) embryogenesis datasets.
- On frog↔zebrafish label transfer (median accuracy of a logistic classifier over 30 runs; ceiling 0.93), SATURN **outperforms baselines by a large margin** — including SAMap, Harmony, scVI and Scanorama — and also beats the best baseline on the mammalian atlas.
- Macrogenes recapture homology: using top-ranked genes per species, **56% of macrogenes** contain a BLASTP homolog pair (vs 0.25% random); rising to **91.2%** with ten top-ranked genes (vs 18.8% random).
- **Robust** to protein-language-model choice (ESM2 vs ESM1b vs ProtXL) and to the number of macrogenes.

## Why it matters for our work
SATURN is a Track C-relevant foundation-model pattern: it fuses a **protein language model with expression data** to produce transferable cell embeddings, and it is a concrete example of using PLM-derived gene representations to encode gene *function* rather than treating genes as anonymous matrix columns. That framing — genes carry biological priors from protein sequence — is directly reusable when thinking about how a foundation model should represent perturbed genes for Track A/B up/down/none prediction, especially for out-of-distribution or poorly annotated genes where one-to-one homolog / co-expression signals are weak. The macrogene idea (grouping functionally related genes) is a candidate feature-engineering or embedding strategy for our gene-regulation modeling.

## Limitations / open questions
- Requires **initial within-species cell annotations** (or clustering) and a mapping between species' cell types to score label transfer — supervision that may not exist for novel systems.
- Demonstrated on cross-species **integration / annotation transfer**, not on perturbation-response or directional expression-change prediction (our Track A/B task).
- Depends on protein sequences and a protein language model per species; unclear how it handles non-coding regulators or genes with poor protein representations.
