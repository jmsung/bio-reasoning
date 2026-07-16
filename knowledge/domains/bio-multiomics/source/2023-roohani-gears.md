<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: Predicting transcriptional outcomes of novel multigene perturbations with GEARS
authors: [Roohani et al.]
year: 2023
doi: 10.1038/s41587-023-01905-6
source_url: https://www.nature.com/articles/s41587-023-01905-6
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Predicting transcriptional outcomes of novel multigene perturbations with GEARS

**Authors:** Yusuf Roohani, Kexin Huang, Jure Leskovec
**Year:** 2023
**Venue:** Nature Biotechnology (42(6):927–935), DOI 10.1038/s41587-023-01905-6

## Abstract
GEARS (Graph-Enhanced Gene Activation and Repression Simulator) couples deep learning with biological knowledge graphs to predict transcriptional responses to genetic perturbations from single-cell RNA-seq (Perturb-seq) data. Its distinguishing capability is predicting the postperturbation transcriptome for gene combinations that were **never experimentally perturbed** — including perturbations of genes unseen at training. On genetic-interaction prediction it achieves ~40% higher precision than prior approaches and identifies the strongest interactions roughly twice as effectively.

## Key contributions
- Predicts multigene (combinatorial) perturbation outcomes even when the constituent single genes lack experimental data.
- 30–50% MSE improvement over baselines for single-gene perturbations.
- Classifies five genetic-interaction subtypes: synergy, suppression, neomorphism, redundancy, epistasis.
- Bayesian uncertainty scores flag low-confidence predictions (e.g., poorly connected genes).

## Methods
GEARS is a graph neural network over two knowledge-graph priors. Each gene gets two learned embeddings: a **gene-state** embedding refined by a GNN over a **gene coexpression graph** (edges from Pearson correlation in the training data), and a **gene-perturbation** embedding refined by a GNN over a **Gene Ontology (GO)-derived graph** (edges from pathway-membership Jaccard similarity). To predict a perturbation, the perturbation embeddings of the targeted gene(s) are **summed** and passed through an MLP — so a novel combination is a composition of learned single-gene perturbation signals, enabling zero-/few-shot combinatorial prediction. A cross-gene MLP layer captures transcriptome-wide effects, and per-gene decoder MLPs map to expression changes. An autofocus, direction-aware loss upweights differentially expressed genes while preserving up/down direction.

## Key results
- **Held-out single genes:** 30–50% MSE improvement; >2× better Pearson correlation across cell lines; improved directional accuracy.
- **Two-gene perturbations:** 30% improvement across generalization cases; **53% improvement when both genes are unseen** in training; 50% greater enrichment in top DE genes.
- **Genetic-interaction precision@10:** ~40% improvement for four of five subtypes; **>90% improvement for redundancy and epistasis**; 2× accuracy on the top-ten strongest interactions.
- **Non-additive effects** captured ~40% better than baselines for three subtypes.
- **Cell-fitness validation:** R² 0.64–0.93 when trained on fitness; synergistic vs buffering interactions separated significantly (P<0.0013 / P<4×10⁻⁵).

## Why it matters for our work
GEARS is the **canonical KG+GNN perturbation predictor** — the reference deep-learning baseline that LLM/agent methods (e.g. PBio-Agent, PerturbQA) are measured against, and a primary **Track C** touchstone. Our task is closely related: predict, for a (perturbed gene, target gene) pair, whether the target goes **up / down / none** under macrophage CRISPRi, in a **zero-overlap** setting where evaluation perturbations are unseen at training. GEARS demonstrates that a **GO-derived graph prior** plus coexpression structure is what lets a model generalize to unseen and combinatorial perturbations — exactly the generalization we need, and the same GO-graph prior mirrors the reasoning/knowledge-graph approach we are pursuing. Its five-way interaction taxonomy and direction-aware loss are directly relevant to framing our up/down/none label and to distinguishing additive from non-additive target responses.

## Limitations / open questions
- Requires training on the **same cell type / condition**; cross-cell-type transfer is not established (matters for macrophage-specific CRISPRi).
- Accurate **combinatorial** prediction still needs some combinatorial training data; pure zero-shot combos degrade.
- Performance **degrades for genes poorly connected** in the coexpression/GO graphs — a concern when target or perturbed genes are sparsely annotated.
- Confounders: cell cycle, gene-editing efficiency assumptions, postperturbation heterogeneity.
- Open: how well does a GNN prior compete with or complement LLM reasoning when there is **zero overlap** between train and test perturbation sets (our regime)?
