---
source_url: https://doi.org/10.1371/journal.pcbi.1013387
source_type: papers
title: "Gene regulatory network structure informs the distribution of perturbation effects"
author: Matthew Aguirre et al.
retrieved: 2026-07-16
doi: 10.1371/journal.pcbi.1013387
---

# Gene regulatory network structure informs the distribution of perturbation effects

**Authors:** Matthew Aguirre, Jeffrey P. Spence, Guy Sella, Jonathan K. Pritchard
**Year:** 2025
**Venue:** PLOS Computational Biology

## Abstract
Gene regulatory networks (GRNs) govern developmental and disease processes, yet
their architecture remains hard to infer efficiently. This paper introduces a
simulation framework to study how GRN structure shapes the distribution of
perturbation (knockout) effects. The authors generate realistic directed
scale-free networks with tunable group structure using a novel growth algorithm
(extending Bollobás et al., 2003 with groups and within-group affinity), then
model gene expression with a stochastic differential equation (SDE) that
enforces non-negativity and saturation. Simulating gene knockouts across 1,920
synthetic GRNs, they characterize how sparsity, modularity, and degree-tail
properties control network susceptibility to perturbation, identify a subset of
networks that recapitulate features of a genome-scale Perturb-seq study
(Replogle et al., 2022, K562), and assess which data types best support GRN
inference.

## Key contributions
- A network-generating algorithm producing directed scale-free graphs with tunable sparsity (`p`), group count (`k`), modularity (`w`), and in/out-degree tail (`δin`, `δout`).
- An SDE-based quantitative expression model (Euler-Maruyama forward simulation) supporting knockouts, knockdown/overexpression, rewiring, and noise perturbations.
- Systematic mapping of how each structural parameter governs the number of "hub knockout" and "hub target" genes.
- A demonstration that perturbation data recover fine-scale edges better than coexpression, while unperturbed data may suffice to recover coarse gene programs.

## Methods
Each of 1,920 GRNs (n = 2,000 genes) is built from one combination of generating
parameters, simulated to steady state, then each gene is knocked out (x_j = 0)
and the system re-equilibrated; the effect is the log2 fold-change in every other
gene's expression. Networks were compared to the Replogle et al. Perturb-seq
subset (5,247 perturbations matched to measured genes) using cumulative
distributions of incoming/outgoing effects and Kolmogorov-Smirnov statistics.
Inference value was probed by comparing perturbation effects vs. coexpression for
edge recovery, and truncated SVD + canonical correlation for recovering gene
programs from perturbed vs. unperturbed cells.

## Key results
- Most effects are tiny (86.6% below |log2FC| = 0.01), but each network has a median 5,296 large effects (~|log2FC| = 1).
- Effects decay with network distance: 77.3% of direct regulators (distance 1) exceed |log2FC| = 0.01, and 98.5% of above-threshold effects are mediated (indirect) rather than direct.
- Sparsity has the largest influence on hub counts; sparser, more modular networks with heavy out-degree (but not in-degree) tails are more resilient. Parameters explain ~half the variance (hub-KO model r² = 0.59; hub-target r² = 0.46).
- Best-matched networks to Perturb-seq share few regulators per gene (2–4), few groups (5–10), high modularity, and heavy out- but not in-degree tails — the "biologically realistic" regime.
- Perturbation effects out-predict coexpression for edge recovery in every network; coexpression is confounded by co-regulation. But low-rank programs are similar across perturbed and unperturbed cells unless perturbation effects exceed intrinsic noise.

## Why it matters for our work
This paper directly informs the BioReasoning Track A/B up/down/none prediction
task. Its finding that most perturbation effects propagate indirectly through
the network (98.5% mediated) and decay sharply with graph distance explains why
naive direct-regulator reasoning under-predicts and why so many gene pairs show
"none" — a structural prior our agent could exploit. The result that biologically
realistic GRNs are sparse, modular, and dominated by a few master regulators
suggests focusing predictive attention on hub regulators and within-module
targets. The perturbation-vs-coexpression comparison also cautions against
leaning on coexpression signals for causal (directional) predictions.

## Limitations / open questions
- Purely synthetic networks; all best-matched GRNs remain statistically distinguishable from real Perturb-seq distributions.
- Models a single cell type at equilibrium — ignores developmental trajectories, cell-type heterogeneity, and post-transcriptional/protein-level regulation.
- Validated against one dataset (Replogle K562); cross-cell-type generalization of the structural priors is assumed, not shown.
