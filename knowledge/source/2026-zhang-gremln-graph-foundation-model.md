---
source_url: https://doi.org/10.1101/2025.07.03.663009
source_type: papers
title: "GREmLN: A Cellular Graph Structure Aware Transcriptomics Foundation Model"
author: Mingxuan Zhang et al.
retrieved: 2026-07-16
doi: 10.1101/2025.07.03.663009
---

# GREmLN: A Cellular Graph Structure Aware Transcriptomics Foundation Model

**Authors:** Mingxuan Zhang, Vinay Swamy, Rowan Cassius, Léo Dupire, Charilaos Kanatsoulis, Evan Paull, Mohammed AlQuraishi, Theofanis Karaletsos, Andrea Califano
**Year:** 2026
**Venue:** bioRxiv (preprint)

## Abstract
GREmLN (Gene Regulatory Embedding-based Large Neural model) is a single-cell RNA-seq foundation model that embeds gene-token graph structure directly into the transformer attention mechanism via graph signal processing. Unlike prior scRNA foundation models (Geneformer, scGPT, scFoundation) that treat genes as ordered token sequences, GREmLN uses molecular-interaction graphs — gene regulatory networks (GRNs) or protein-protein interaction (PPI) networks — as a relative-position/inductive-bias signal, since scRNA expression vectors are inherently orderless sets. The model produces biologically informed, cell-specific gene embeddings and reports superior performance on cell-type annotation, graph-structure understanding, and fine-tuned reverse perturbation prediction while using far fewer parameters.

## Key contributions
- A Graph Diffusion Kernel (GDK) attention that transforms only the *query* embeddings by a diffusion-kernel Gram matrix derived from the token graph's normalized Laplacian, biasing attention toward graph-implied long-range (low-frequency) dependencies while keys/values preserve original token information.
- Chebyshev-polynomial approximation (truncated at K ≪ G) of the kernel Gram matrix to scale spectral operations to large graphs and long gene sequences, avoiding per-batch matrix exponential / eigendecomposition.
- A masked-modeling pretraining objective conditioned on cell-type-specific GRN Laplacians; graph priors act as an inductive bias enabling parameter-efficient architectures and faster convergence.

## Methods
Inputs are a gene-identity embedding (never masked) concatenated with a binned gene-rank embedding (30% of rank tokens masked); a `<CLS>` token attends to all genes but sits outside the graph. Expression is total-count normalized to 1e6 and log1p-transformed before ranking. Attention uses the diffused query score S_ij = q_i^T Φ_L^{1/2} k_j, where Φ_L is built from a non-negative spectral filter over the Laplacian eigenvalues. To avoid leaking cell-type labels, cell-type-specific GRNs are combined into an integrated network, and per-cell graphs are assembled via two Bayesian updates (type-specific edge posteriors averaged under a k-NN cell-type posterior). Evaluation deliberately uses low-capacity heads (linear models, shallow MLPs) so results reflect embedding quality, on datasets non-overlapping with pretraining.

## Key results
- Highest scores on all cell-type classification metrics on the human immune dataset, and superior zero-shot annotation on held-out non-immune cells.
- Only **10.3M** learnable parameters — under one-third of the baselines and one-tenth of scFoundation — yet outperforms them, highlighting the value of GRN guidance over model scale.
- Best GRN edge-prediction (masked-edge recovery, 15% edges masked) by a significant ROC/PRC margin on healthy human data, and best out-of-distribution generalization on cancer-infiltrating myeloid cells from unseen cell types/tissues.
- Ablation (remove GDK → naive dot-product attention) causes substantial degradation, largest on masked-edge prediction and zero-shot annotation, confirming the inferred GRN carries predictive signal.
- State-of-the-art reverse perturbation prediction (Adamson Perturb-Seq) frozen and fine-tuned; PPI priors help frozen embeddings, GRN priors help fine-tuning (a bias-variance trade-off). Monotonic scaling across 1/3/6-layer models (7.4M/10M/24.2M params).

## Why it matters for our work
GREmLN is a Track C open-weights candidate that injects gene-regulatory structure as an architectural inductive bias rather than learning it implicitly — directly relevant to the BioReasoning Challenge's gene-regulation-prediction framing. Its GRN/PPI-conditioned embeddings and fine-tuned perturbation head speak to Track A/B up/down/none prediction, where a compact (10M-param), regulation-aware representation could improve signal on subtle single-gene perturbations that stump larger sequence-only models. The graph-as-prior idea is a strong contrast to Geneformer/scGPT/scFoundation and a candidate strategy for our gene-regulation modeling.

## Limitations / open questions
- GRNs are inferred from expression, risking information duplication; the authors argue via ablation that graphs add signal, but circularity remains a caveat.
- Perturbation task uses only single-gene CRISPR (Adamson) with low class separability; baselines were not fine-tuned due to compute limits, weakening head-to-head fine-tuned comparison.
- Preprint (not peer-reviewed); combinatorial perturbations, optimal-intervention selection, and attention-based module recovery are left as future work.
