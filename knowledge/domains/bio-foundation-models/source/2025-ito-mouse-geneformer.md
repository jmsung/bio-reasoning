---
source_url: https://doi.org/10.1371/journal.pgen.1011420
source_type: papers
title: "Mouse-Geneformer: A deep learning model for mouse single-cell transcriptome and its cross-species utility"
author: Keita Ito et al.
retrieved: 2026-07-16
doi: 10.1371/journal.pgen.1011420
---

# Mouse-Geneformer: A deep learning model for mouse single-cell transcriptome and its cross-species utility

**Authors:** Keita Ito, Tsubasa Hirakawa, Shuji Shigenobu, Hironobu Fujiyoshi, Takayoshi Yamashita
**Year:** 2025
**Venue:** PLOS Genetics

## Abstract
Geneformer is a Transformer-encoder foundation model pretrained on human scRNA-seq that excels at human transcriptome tasks, but the mouse — the primary mammalian model organism — lacked an equivalent. The authors built mouse-Geneformer by assembling a 21-million-cell mouse scRNA-seq corpus ("mouse-Genecorpus-20M") and pretraining Geneformer on it with the same rank-value-encoding + masked-token strategy. The model captures mouse transcriptome structure, improves cell-type classification after fine-tuning, and via in silico perturbation recovers disease-causing genes later validated in vivo. After ortholog-based gene-name conversion, mouse-Geneformer also analyzes human data cross-species, matching human-Geneformer on cell-type classification and on a myocardial-infarction perturbation model, but only partially on COVID-19 (a human-specific disease mice don't model).

## Key contributions
- First species-specific port of the Geneformer architecture to mouse, demonstrating the architecture generalizes to any species with a large scRNA-seq corpus.
- Released mouse-Genecorpus-20M: ~21M raw profiles filtered to 20,630,028 cells from healthy mice across many organs and developmental stages (excludes cancer/immortalized lines and doublets/damaged cells).
- Showed bidirectional cross-species transfer via homology-based gene-name conversion (human↔mouse), including with scGPT.

## Methods
Pretraining follows the original human Geneformer: rank-value encoding converts each cell to a ranked gene token sequence with a [CLS] token, then masked-token prediction (15% of tokens masked). Downstream cell-type and disease classification use per-organ fine-tuning (80/20 train/test split; accuracy + F1 metrics). In silico perturbation deletes/activates genes in a fine-tuned model and measures cosine similarity of the shifted cell state toward the target disease/normal state. Cross-species analysis converts gene names to orthologs before fine-tuning. Baselines: scDeepSort (GNN), scVAE (GMVAE), human-Geneformer, scGPT.

## Key results
- Cell-type classification across 12 mouse organs: mouse-Geneformer averaged 96.73% accuracy (always >93%), vs scDeepSort 66.34% and scVAE 72.95%.
- Pretraining helped in all cases; largest gain was +8.22% accuracy on embryo data.
- In silico perturbation recovered in-vivo-validated genes: Slc12a3 for diabetic kidney disease (cosine 0.018), Slc35b1 for UMOD nephropathy, Apoe for COP1-KO microglia (cosine 0.36).
- Cross-species (human data, fine-tuned): accuracy 95.59% (thymus), 99.97% (cerebral cortex), 87.82% (breast) — within 0.01–0.30% of human-Geneformer.
- Human myocardial-infarction perturbation agreed with human-Geneformer (Ankrd1 activation, Myh7 deletion); COVID-19 perturbation only partially agreed, a species limitation.

## Why it matters for our work
Directly relevant to Track C foundation-model strategy: it shows Geneformer's rank-value-encoding + masked-token recipe is a robust, transferable backbone, and that ortholog-based gene-name conversion enables zero-shot/fine-tuned cross-species transfer — useful if we need to borrow mouse-trained representations or reason about conserved gene networks. The in silico perturbation results (single-gene deletion shifting cell state toward disease, ranked by cosine similarity) are a concrete template for Track A/B up/down/none directional prediction: perturbation direction maps to expression-change direction, and the myocardial-vs-COVID contrast is a caution that species-specific and non-conserved regulation limits cross-species generalization.

## Limitations / open questions
- Homology-based conversion ignores species-specific regulation; cross-species accuracy degrades for tasks with many cell-type classes and for human-specific biology (COVID-19).
- Disease labels are coarse (organ-level diseased vs normal); only models >90% subtype accuracy were used, biasing toward easy separations.
- Perturbation validation is anecdotal (a few known genes per disease), not a systematic benchmark of directional prediction.
