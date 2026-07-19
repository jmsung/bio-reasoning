---
source_url: https://doi.org/10.1093/bib/bbae617
source_type: papers
title: "BioDSNN: a dual-stream neural network with hybrid biological knowledge integration for multi-gene perturbation response prediction"
author: Yuejun Tan et al.
retrieved: 2026-07-16
doi: 10.1093/bib/bbae617
---

# BioDSNN: a dual-stream neural network with hybrid biological knowledge integration for multi-gene perturbation response prediction

**Authors:** Yuejun Tan, Linhai Xie, Hong Yang, Qingyuan Zhang, Jinyuan Luo, Yanchun Zhang
**Year:** 2025
**Venue:** Briefings in Bioinformatics

## Abstract
BioDSNN predicts single-cell transcriptional responses to single- and multi-gene genetic perturbations. Prior methods split into two camps: generative models (VAE, diffusion) that fit the perturbed data distribution well but lack biological grounding for generalization, and knowledge-driven models (gene regulatory networks, pathways) that generalize better but under-fit. The authors argue neither balances the two modalities. BioDSNN uses a dual-stream architecture that processes single-cell sequencing data with a generative model and biological knowledge with graph networks plus a masked transformer, before merging the two streams. On benchmarks it achieves roughly a 20% reduction in mean squared error over GEARS.

## Key contributions
- A dual-stream design that keeps a data-driven stream (VAE over expression) and a knowledge-driven stream (GNN + masked attention) separate before a late fusion, avoiding the fit/generalize trade-off.
- Integration of three knowledge types: a gene co-expression graph (Pearson correlation), a perturbation graph, and ReactomeNet pathway structure used as the mask for a transformer-like masked-attention encoder.
- An autofocus loss (MSE variant) that up-weights differentially expressed (DE) genes by raising the error exponent, plus a directional loss for consistent up/down change relative to control.

## Methods
The knowledge stream initializes gene and perturbation embeddings, augments them via two GNN encoders (over the gene co-expression graph and perturbation graph), combines each gene embedding with the perturbation embedding, and refines through a masked-attention transformer whose mask comes from ReactomeNet. Summing the last embedding dimension reshapes to an n×m perturbation-effect matrix. The data-driven stream applies a VAE (latent dim 16, intermediate 32) to control expression, regenerating only originally non-zero genes. The predicted perturbation effect is added to the baseline expression matrix. Trained 20 epochs with Adam (lr=0.001, weight decay=5e-4).

## Key results
- ~20% MSE improvement over GEARS across all datasets, evaluated on the top 20 most DE genes.
- Higher fraction of predictions within ±5% of true mean expression than baselines across all three datasets.
- Superior Pearson correlation on K562 and RPE1 (Replogle single-gene screens); comparable to GEARS on Norman two-gene data.
- On Norman two-gene perturbations, closer alignment of genetic-interaction magnitude scores to ground truth and higher PCC than GEARS; detects more synergy/suppressor GI types.
- Ablations confirm both the VAE and masked-attention modules contribute.

## Why it matters for our work
BioDSNN is a direct GEARS successor for perturbation-response prediction, relevant to Track A/B where we predict gene up/down/no-change under perturbation. Its DE-gene-focused evaluation and autofocus loss reinforce our finding that rank/direction metrics hinge on the top DE genes, not the bulk transcriptome. The late-fusion of a generative expression model with pathway-masked attention is a candidate architecture pattern for direction prediction, and its Norman two-gene GI results are a benchmark for combinatorial reasoning.

## Limitations / open questions
- Efficacy depends heavily on training-data quality and available prior knowledge.
- Requires training on the same cell type as the prediction target — limited cross-cell-type transfer.
- Reported gains are relative (~20% MSE vs GEARS); no absolute MSE values or non-GEARS SOTA comparison surfaced in the text read.
