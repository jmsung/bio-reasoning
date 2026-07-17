---
source_url: https://doi.org/10.1038/s41586-026-10689-z
source_type: papers
title: "Universal cell embedding provides a foundation model for cell biology"
author: Rosen, Roohani, Agrawal et al. (senior: Quake, Leskovec)
retrieved: 2026-07-17
doi: 10.1038/s41586-026-10689-z
---

# Universal cell embedding provides a foundation model for cell biology

**Authors:** Yanay Rosen, Yusuf Roohani, Ayush Agrawal, Leon Samotorčan,
Tabula Sapiens Consortium, Stephen R. Quake, Jure Leskovec
**Year:** 2026 (Nature, open access; received 2023, accepted May 2026)
**Venue:** Nature · 10.1038/s41586-026-10689-z

## Abstract

UCE (Universal Cell Embedding) is a self-supervised foundation model that maps
any single cell's scRNA-seq profile into a shared latent space, **zero-shot** —
no cell-type labels, no per-dataset fine-tuning, no preprocessing/gene selection.
It is **genome-agnostic**: each gene is represented by an ESM2 protein-language-model
embedding of its protein product, so cells from any species (even non-homologous
genes / species unseen in training) embed into the same space. Used to build the
Integrated Mega-scale Atlas (IMA): 36M cells, 1,000+ cell types, dozens of tissues,
8 species.

## Key contributions

- 33-layer, 650M-param transformer over cells-as-"bags-of-RNA"; gene tokens = ESM2 embeddings, sorted by genomic location, grouped by chromosome; a CLS token is the cell embedding.
- Self-supervised objective: mask 20% of expressed genes, predict whether a sampled gene was expressed in the cell (binary) — no labels used.
- Genome-agnostic design enables zero-shot embedding of unseen species without homolog mapping.
- IMA: a 36M-cell integrated atlas built purely from zero-shot UCE embeddings.

## Methods

Trained on 300+ datasets / 36M cells (CellXGene), 40 days on 24×A100-80GB. Expression
counts give a weighted, normalized sample of a cell's genes → tokenized via ESM2
protein embeddings → transformer → CLS embedding. Fully unsupervised; cell embeddings
compared/annotated downstream via simple logistic classifiers on the frozen space.

## Key results

- On the scIB benchmark (Tabula Sapiens v.2, 581k cells): beats next-best Geneformer by **+13.9% overall, +16.2% bio-conservation, +10.1% batch-correction**, zero-shot.
- Zero-shot embeddings **match or beat fine-tuned** scVI / scArches / scGPT / Geneformer.
- Cross-species zero-shot label transfer: green monkey (17/17 nearest centroids correct), naked mole rat (17/24), chick heart (12/15) — no retraining.
- Emergent biology never trained for: developmental-lineage & germ-layer structure (>80% germ-layer classifier), Cell-Ontology-consistent hierarchy.
- Case study: identifies novel erythropoietin-producing **Norn cells** across kidney/lung/heart; applied to IPF vs COPD lung disease.

## Limitations / open questions

- **Embedding model, not a perturbation/generative predictor** — it predicts *what a cell is*, not how it responds to a perturbation. Direct relevance to our perturb-seq tracks is only as a cell-state feature/prior.
- Large evolutionary distances (e.g. *Drosophila*) still hard for cross-species cell-type transfer.
- Consistent with our KB's scFM caveats: [[2026-hou-scfm-benchmark]] (UCE only sometimes beats HVG+PCA; strongest at 1-shot annotation) and [[2025-kedzierska-scfm-zero-shot]] (scFMs often don't beat classical baselines zero-shot).
