---
source_url: https://doi.org/10.1038/s41586-024-08411-y
source_type: papers
title: "A cell atlas foundation model for scalable search of similar human cells"
author: Graham Heimberg et al.
retrieved: 2026-07-16
doi: 10.1038/s41586-024-08411-y
---

# A cell atlas foundation model for scalable search of similar human cells

**Authors:** Graham Heimberg, Tony Kuo, Daryle J. DePianto, Omar Salem, Tobias Heigl, Nathaniel Diamant, Gabriele Scalia, Tommaso Biancalani, Shannon J. Turley, Jason R. Rock, Héctor Corrada Bravo, Josh Kaminker, Jason A. Vander Heiden, Aviv Regev
**Year:** 2024
**Venue:** Nature (Genentech / gRED)

## Abstract
SCimilarity is a deep-metric-learning foundation model for single-cell RNA-seq that learns a unified, interpretable low-dimensional representation in which transcriptionally similar cells sit close together, enabling rapid similarity search across tens of millions of cell profiles from diverse studies. Trained on a 23.4-million-cell corpus of 412 human scRNA/snRNA-seq studies, it lets a user query with a single cell profile or a cell-state centroid and retrieve the most similar cells across the whole body, annotated with tissue, disease, and in-vitro context. The authors used it to search for fibrosis-associated macrophage (FM) and fibroblast states from interstitial lung disease (ILD), revealing similar cells across other fibrotic diseases and tissues, and experimentally validated that a 3D hydrogel system reproduces the top in-vitro macrophage hit.

## Key contributions
- Frames cell search as a metric-learning problem (analogous to facial-recognition embeddings), yielding a reusable, retraining-free foundation model for scRNA-seq.
- Combines a supervised triplet loss (Cell Ontology-labeled anchor/positive/negative triplets) with an unsupervised MSE reconstruction loss (β weighting) to decouple faithful cell representation (query) from cross-study mixing (integration).
- Ships a searchable 23.4M-cell reference plus tooling for query, annotation, outlier/confidence scoring, and Integrated-Gradients gene attribution.

## Methods
SCimilarity is trained on 7.9M profiles from 56 studies (203 Cell Ontology terms), sampling 50M hard-mined triplets weighted by study and cell type, with anchor and positive cells drawn from different studies. Ambiguous ancestor–descendant ontology pairs are excluded so no manual harmonization is needed; labels are used only in training (inference needs no labels or fine-tuning). The chosen model uses β = 0.001, margin = 0.05, optimizing combined query and integration scores. Approximate nearest-neighbor search over the precomputed reference uses hnswlib.

## Key results
- Query fidelity: SCimilarity's similarity scores matched gene-signature retrieval scores at Spearman ρ = 0.77, versus 0.54 (scFoundation) and 0.59 (scGPT).
- Annotation: a single pretrained model matched author kidney labels 86.5% (vs scANVI 85.2%, CellTypist 90.4%, TOSICA 87.2%); on a held-out CITE-seq set (22 immune subsets) it hit 75.3%, outperforming scANVI (52.2%), CellTypist (59.1%), TOSICA (44.4%).
- Speed: searching the ANN index takes ~20 ms; scoring 2.5M cells took 2 s and finding the top 10,000 of 23.4M took 0.05 s, versus 2 h 46 min for a literature gene-signature scan.
- Generalization: trained only on 10x Chromium, it embedded 7 other platforms well; 79.5% of in-vivo holdout cells scored high-confidence vs 43.8% low-confidence for in-vitro cells (excluded from training).
- Biology: FM-like cells were common in ILD/COVID-19 lung, rarer in healthy lung (~0.40%), and present in some cancers (PDAC, uveal melanoma, colon); Integrated-Gradients attributions recovered known markers (AUC ~0.84 vs marker genes).

## Why it matters for our work
For Track C, SCimilarity is a concrete, open example of a non-transformer single-cell foundation model whose value comes from a well-shaped embedding + retrieval loop rather than autoregressive generation — useful as a contrast to scGPT/scFoundation when we pick and justify a Track C base model. Its metric-learning framing (query by cell-state centroid, nearest-neighbor retrieval, confidence/outlier scoring) is directly relevant to reasoning about cell state under perturbation and could inform how we ground up/down/none predictions in similar reference cells rather than de novo generation.

## Limitations / open questions
- Trained exclusively on 10x Chromium droplet data; non-10x platforms (Seq-well, SMART-Seq2) and in-vitro/tumor/iPSC-derived cells are poorly represented (43.8% low confidence).
- Depends on Cell Ontology annotations for training triplets; closely related states (memory vs naive T cells, CD56bright vs CD56dim NK) remain hard to resolve for all methods.
- Designed for similarity search and annotation, not perturbation-response prediction — no direct notion of how a cell moves under a genetic/chemical perturbation.
