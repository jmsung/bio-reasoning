---
source_url: https://doi.org/10.1186/s13059-025-03862-6
source_type: papers
title: "scKGBERT: a knowledge-enhanced foundation model for single-cell transcriptomics"
author: Yang Li et al.
retrieved: 2026-07-16
doi: 10.1186/s13059-025-03862-6
---

# scKGBERT: a knowledge-enhanced foundation model for single-cell transcriptomics

**Authors:** Yang Li, Guanyu Qiao, Hongli Du, Xin Gao, Guohua Wang
**Year:** 2025
**Venue:** Genome Biology (2025); PMC12642280

## Abstract
Current single-cell pre-trained models rely solely on expression data and fail to capture gene associations. scKGBERT is a knowledge-enhanced foundation model that jointly learns gene and cell representations by integrating 41M scRNA-seq profiles with a protein–protein interaction (PPI) knowledge graph of 8.9M regulatory relationships. It uses a dual-encoder BERT design plus a Gaussian cross-attention mechanism to emphasize key genes and improve biomarker identification, achieving superior performance across gene annotation, cell annotation, drug response, and disease prediction tasks while enhancing biological interpretability.

## Key contributions
- First unified pre-training framework to concurrently integrate RNA expression profiles and a structured PPI knowledge graph (from STRING) within a single architecture.
- Dual parallel Masked Language Models — a Sequence Encoder (S-Encoder) and a Knowledge Encoder (K-Encoder) — bridged by a novel Gaussian cross-attention mechanism.
- Interpretable per-gene attention weights that surface disease- and drug-resistance–associated marker genes.

## Methods
Knowledge is encoded by building a gene-centric graph from STRING and learning entity/relation embeddings with a TransR-style margin-based scoring (L1/L2 distance over (h,r,t) triples). The S-Encoder ingests rank-based gene-selection sequences (Geneformer strategy); the K-Encoder ingests the pre-trained knowledge embeddings. Both follow the BERT masked-LM paradigm (~15% tokens masked). A Gaussian-normalized cross-attention fuses sequence and knowledge features: raw dot-product scores are Gaussian-normalized (mean/std) before softmax to sharpen weight contrast and reduce over-smoothing, staying lightweight vs. kernel-based Gaussian attention. The model stacks three scKGBERT blocks (each = two parallel BERT blocks + a Gaussian fusion module), embedding dim 256, hidden 512, 4 attention heads, AdamW (lr 5e-5).

## Key results
- Cell annotation across ten tissues: highest average accuracy **0.9516**, beating scGPT, scFoundation, Geneformer, and supervised baselines (scDeepSort 0.5854, CaSTLe 0.8867).
- Cross-tissue transfer (fine-tune on liver → predict lung): highest accuracy **0.88** and F1 **0.86** among all evaluated models.
- Gene dosage-sensitivity prediction (fine-tuned on 10,000 cells): outperformed scGPT, scFoundation, Geneformer, and classical ML.
- Ablation: adding the knowledge graph **nearly doubled** top-relevant-gene detection vs. the no-graph variant (Muraro alpha-cells).
- Cross-modality drug response (scRNA-seq → bulk RNA-seq, Docetaxel): **+3% accuracy** and higher F1 vs. Geneformer; identified 727 high-weight tumor-state genes enriched in cancer pathways.
- Disease: on ~560,000 cardiac cells (DCM/HCM/NF), recovered known HCM/DCM marker genes (e.g., Notch1 pathway; KIT, NRP2, KLRF1).

## Why it matters for our work
scKGBERT is a Track C–relevant open foundation model whose central thesis — that injecting a gene-regulation prior (PPI graph) into an scRNA-seq transformer improves gene/cell prediction and interpretability — directly informs our gene-regulation strategy. Its knowledge-graph fusion and interpretable attention weights are a template for grounding Track A/B up/down/none perturbation predictions in biological priors rather than expression alone, and its cross-tissue/cross-platform generalization gains suggest knowledge injection helps under the distribution shift our tasks face.

## Limitations / open questions
- Gains reported vs. baselines but no released ablation on knowledge-graph choice (STRING vs. alternatives) beyond the with/without comparison.
- Restricted to transcriptomics + PPI; multi-omics (ATAC, proteomics, spatial) integration is future work.
- Interpretability rests on attention weights, whose causal validity is asserted via pathway enrichment, not perturbation validation.
- No head-to-head on our specific Track A/B perturbation-response metrics; transfer to up/down/none prediction is untested.
