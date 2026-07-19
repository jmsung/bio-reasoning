---
source_url: https://doi.org/10.1038/s41592-025-02814-z
source_type: papers
title: "Nicheformer: a foundation model for single-cell and spatial omics"
author: Alejandro Tejada-Lapuerta et al.
retrieved: 2026-07-16
doi: 10.1038/s41592-025-02814-z
---

# Nicheformer: a foundation model for single-cell and spatial omics

**Authors:** Alejandro Tejada-Lapuerta, Anna C. Schaar, Robert Gutgesell, Giovanni Palla, Lennard Halle, Mariia Minaeva, Larsen Vornholz, Leander Dony, Francesca Drummer, Till Richter, Mojtaba Bahrami, Fabian J. Theis
**Year:** 2025
**Venue:** Nature Methods

## Abstract
Nicheformer is a transformer-based foundation model trained jointly on dissociated single-cell and image-based targeted spatial transcriptomics from human and mouse. It is pretrained on SpatialCorpus-110M — >110 million cells (57M dissociated, 53.83M spatially resolved) across 73 organs/tissues — using expression data only, with modality, organism, and assay context tokens. The learned embedding captures spatial context, and the authors design a new suite of spatial downstream tasks (spatial label prediction, neighborhood composition, and density prediction). Nicheformer, in both linear-probing and fine-tuning settings, systematically beats scRNA-only foundation models (Geneformer, scGPT, UCE), a spatial FM (CellPLM), and embedding baselines (scVI, PCA). Critically, models trained only on dissociated data fail to recover spatial microenvironment complexity, motivating multiscale integration. The model can transfer spatial context onto dissociated scRNA-seq.

## Key contributions
- SpatialCorpus-110M: a curated multiscale corpus combining dissociated scRNA-seq and image-based spatial transcriptomics (MERFISH, CosMx, Xenium) across human and mouse, 73 tissues.
- A joint FM that encodes modality/organism/assay as contextual tokens so dissociated and spatial data share one representation.
- A newly designed set of spatially-informed downstream tasks: cell-type/niche/region label prediction, neighborhood composition prediction, and neighborhood density prediction.
- Demonstration that spatial context can be transferred from spatial to dissociated data via a simple linear layer.

## Methods
Architecture: 1,500-token context, 12 encoder layers, 16 attention heads/layer, feed-forward size 1,024, 512-dim embedding — 49.3M parameters (chosen over smaller variants). Pretraining is self-supervised on expression only (no spatial coordinates). Cell representation is the mean of gene-token outputs from the last layer; contextual/metadata tokens are deliberately excluded from aggregation because their high output norm (a register-token effect, as in vision transformers) otherwise dominates the embedding and breaks cross-modality label transfer. Evaluation uses linear probing (frozen embedding + linear head) and fine-tuning (transformer weights updated), each trained one epoch, compared against Geneformer, scGPT, UCE, CellPLM, scVI, and PCA on held-out test sets. Downstream datasets: MERFISH mouse brain, CosMx human liver/lung, Xenium human lung/colon.

## Key results
- On MERFISH mouse brain, fine-tuned Nicheformer achieved the highest macro F1 for niche and region label prediction vs all baselines; differences were statistically significant. PCA with many components was competitive for linear-probing region prediction, but fine-tuned Nicheformer still led.
- On neighborhood composition prediction (radii for ~10/20/50/100 neighbors) across brain, liver, and lung, fine-tuned Nicheformer systematically had the lowest mean absolute error; linear-probing on Nicheformer embeddings also beat all other embeddings except fine-tuned Nicheformer. Liver was the weak spot (scVI competitive), attributed to low liver abundance in the corpus.
- Neighborhood density prediction: only the Nicheformer-embedding linear model gave positive R²; scVI and PCA performed worse than random (negative R²).
- Data-diversity ablation: a model trained on just 1% spatial data beat models trained on the same or 3× dissociated data; single-organism models underperformed on the other organism — spatial signal and diversity, not sheer cell count, drive performance (FDR-significant).

## Why it matters for our work
Directly relevant to Track C (open-weights foundation models). Nicheformer is a concrete scFM+spatial candidate whose central lesson — that dissociated scRNA-seq alone cannot recover spatial/microenvironment structure and that a jointly-trained embedding transfers spatial context to dissociated cells — bears on Track A/B up/down/none prediction wherever cellular context matters. Its context-token norm caveat (metadata tokens must be dropped from mean-pooling or they bias the embedding) is a practical warning for anyone pooling transformer gene tokens into a cell/perturbation representation. It also reinforces a recurring theme in our wiki: training-data diversity and abundance, not parameter count alone, gate FM performance.

## Limitations / open questions
- Performance degrades on tissues/cell types that are rare in the corpus (liver underperformed; rare midbrain/hypothalamus neurons predicted poorly).
- Spatial coordinates are not used in pretraining — only expression — so physical neighbor structure is left on the table; the authors flag graph-transformer pretraining as future work.
- Dropping contextual tokens avoids modality bias but discards potentially useful information; a small 49.3M-param model with no established genomics scaling laws and no standardized spatial FM benchmark yet.
