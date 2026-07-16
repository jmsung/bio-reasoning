<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: D-SPIN constructs regulatory network models from scRNA-seq that reveal organizing principles of perturbation response
authors: [Jiang et al.]
year: 2026
doi: TODO
source_url: https://www.sciencedirect.com/science/article/pii/S0092867426004630
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# D-SPIN constructs regulatory network models from scRNA-seq that reveal organizing principles of perturbation response

**Authors:** Jialong Jiang, Sisi Chen, Tiffany Tsou, Christopher S. McGinnis, Tahmineh Khazaei, Qin Zhu, Jong H. Park, Inna-Marie Strazhnik, Jost Vielmetter, Yingying Gong, John Hanna, Eric D. Chow, David A. Sivak, Zev J. Gartner, Matt Thomson
**Year:** 2026
**Venue:** Cell

> Note: distilled from the open bioRxiv preprint (doi:10.1101/2023.04.19.537364; preprint title "...from multiplexed scRNA-seq data..."). The Cell version is paywalled (S0092-8674(26)00463-0); metadata/results below are from the preprint full text.

## Abstract
D-SPIN is a computational framework that infers mechanistically interpretable, generative models of gene regulatory networks from scRNA-seq collected across thousands of perturbation conditions. It builds a probabilistic (spin-network / Markov random field) model of regulatory interactions between genes or gene-expression programs that fits the joint cell-state distribution across perturbations. Applied to large Perturb-seq and drug-response datasets, D-SPIN recovers key regulators of cell-fate decisions, reveals coordination of distant pathways under gene knockdown, dissects drug-response mechanisms in heterogeneous populations, and predicts cell-state distributions under unseen drug-dose combinations.

## Key contributions
- A single **unified** network learned jointly across all perturbation conditions (not one network per condition), enabling information integration across thousands of perturbations.
- Perturbations enter as node-level **response vectors h(n)** that bias the shared pairwise network J — a clean factorization of "core network" vs. "perturbation effect."
- Scales to thousands of genes and millions of cells via pseudo-likelihood inference and a parallelized procedure.
- Recovers **hidden/masked regulatory interactions** that correlation- or tree-based methods (GENIE3, GRNBoost2, PIDC) miss.

## Methods
D-SPIN models the transcriptional state of a cell as a vector of spins (genes, or coarse-grained **gene programs** discovered by unsupervised ONMF). It fits a **condition-dependent spin network model** (a Markov random field / maximum-entropy model): an energy function with a shared pairwise interaction matrix **J** (gene–gene or program–program couplings) plus a per-condition biasing field **h(n)** capturing how perturbation *n* activates/inhibits individual nodes. The learning problem factorizes into (1) inferring the unified network J and (2) inferring each perturbation's response vector; pseudo-likelihood approximates conditional dependence for large networks. The fitted model is generative — it can simulate the cell-state distribution under any condition, expose modular sub-network structure, and rank candidate regulators (e.g., TF→program interactions).

## Key results
- On a synthetic four-pathway benchmark, D-SPIN achieves directed-network **AUPRC 0.77 vs 0.44** for competing methods, uniquely recovering inhibitory interactions hidden under wild-type conditions.
- On genome-scale K562 Perturb-seq: focused on **3,136 knockdowns**, coarse-grained to **30 gene programs**; >98% of network edges are stable under resampling; Leiden decomposes the network into ~7 core cellular functions and 40 perturbation groups.
- Recovers erythroid regulators **KLF1, NFE2, GFI1B, GATA1** and myeloid regulators **SPI1 (PU.1), MEF2C** — where differential-expression analysis found only GATA1 and no myeloid regulators. Uniquely flags **NPM1** as a post-transcriptional (BCR-ABL1-dependent) inhibitor of both fates.
- On immunomodulatory-drug response, models drug combinations as additive recruitment of programs and predicts dose-combination cell states beyond the training data from a single combination experiment.

## Why it matters for our work
Our task is to predict, for a (perturbation gene, target gene) pair in macrophage CRISPRi, whether the target goes **up / down / none**. D-SPIN is directly on-point: it infers exactly a **perturbation-response regulatory network** — a signed interaction matrix J plus per-knockdown response fields — from the same Perturb-seq/CRISPRi data regime. This gives (a) a **structured prior** for network/mechanism reasoning in Track B: a learned J encodes which gene→gene (or program→program) couplings are positive vs negative; and (b) a way to **reason about propagation** — a knockdown lowers its node, and the sign of the inferred path to the target predicts up/down (vs "none" when the target is buffered by redundant inhibition, exactly the KLF1/SPI1/NPM1 buffering case). Its ability to recover interactions invisible to DE analysis suggests network inference beats naive per-perturbation correlation for the "none" class, where robustness masks direct effects. Practical: code is open (github.com/JialongJiang/DSPIN); the program-level abstraction (ONMF → 30 programs) is a candidate feature representation for the target gene.

## Limitations / open questions
- **Pairwise-only**: no higher-order (multi-body) or concentration-dependent interactions — may under-model combinatorial regulation.
- **Equilibrium model**: no dynamics/temporal ordering; cannot represent feedback-loop-dependent directed stationary states without extension.
- **Static core network J**: assumes perturbations don't rewire J (fine for knockdown/drug, but epigenetic reorganization in differentiation/disease would break it).
- Program-level coarse-graining trades gene-level resolution for interpretability — the right granularity for a specific target-gene prediction is task-dependent.
