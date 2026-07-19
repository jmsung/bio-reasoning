---
source_url: https://doi.org/10.1038/s41467-025-59867-z
source_type: papers
title: "Combinatorial prediction of therapeutic perturbations using causally-inspired neural networks"
author: Guadalupe Gonzalez et al.
retrieved: 2026-07-16
doi: 10.1038/s41467-025-59867-z
---

# Combinatorial prediction of therapeutic perturbations using causally-inspired neural networks

**Authors:** Guadalupe Gonzalez, Xiang Lin, Isuru Herath, Kirill Veselkov, Michael Bronstein, Marinka Zitnik
**Year:** 2025
**Venue:** Nature Communications (preprinted on bioRxiv)

## Abstract
PDGrapher is a causally-inspired graph neural network (GNN) that predicts combinatorial *perturbagens* — sets of therapeutic target genes — capable of reversing a disease phenotype. Instead of learning how a perturbation changes a phenotype (the forward problem tackled by scGen, CellOT, GEARS, ChemCPA, Biolord), PDGrapher solves the *inverse* problem: given a diseased and a desired treated cell state, it directly predicts which genes to perturb. It embeds cell states on a gene network, learns a latent representation, and outputs an optimal combinatorial intervention. Across nine chemical-perturbation cell lines it finds effective perturbagens in more test samples than competing methods, and it is competitive on ten genetic-perturbation datasets, while training up to 25× faster than baselines.

## Key contributions
- Reframes phenotype-driven drug discovery as *direct inverse prediction* of perturbagens rather than exhaustive forward-response search over a perturbation library.
- Two GNN modules on a "proxy causal graph" (PPI or GRN) where edge mutilations encode intervention effects: a perturbagen-discovery module `f_p` and a response-prediction module `f_r`.
- A dual objective: a **supervision loss** (predict the correct target set directly) plus a **cycle loss** (response after intervening on predicted genes should reconstruct the treated state).
- Benchmarks across 38 preprocessed datasets: 2 intervention types (chemical multi-gene, genetic single-gene CRISPR KO), 11 cancer types, and 2 graph types (BioGRID PPI ~10.7k nodes/152k edges; GENIE3 GRNs).

## Methods
Given a diseased expression profile, `f_p` outputs a candidate target set `U'`; `f_r` then predicts the response of perturbing `U'` and is trained on paired disease- and treatment-intervention data. Both modules train simultaneously with independent early stopping. Evaluation uses two splits: **random** (train/test within a cell line) and **leave-cell-out** (train on one line, test on unseen lines). Ranking quality is scored with nDCG, percentage of accurately predicted samples (≥1 of top-N genes correct), and recall@1/10/100. Notably, "disease intervention data" (paired healthy/diseased profiles) exists only for lung/breast/prostate lines, so the model must also work from treatment data alone.

## Key results
- Outperforms the second-best method in **all nine** chemical cell lines on nDCG (margins 0.001–0.13) and predicts ground-truth targets in **4.5%–13.4% more test samples**.
- Generalizes in leave-cell-out: **5.0%–8.7% more** accurately predicted samples than the runner-up across eight held-out lines.
- Predicted targets sit significantly closer (shortest-path) to ground-truth targets than chance (avg 2.77 vs 3.11; Mann-Whitney p<0.001), consistent with the local-network hypothesis.
- **Up to 25× faster training than scGen, >100× faster than CellOT** (100k epochs); scGen would need ~8 years for the leave-cell-out experiments.
- Weak dependence on healthy-control data: in 4/9 lines the no-disease-intervention model matched or beat the full model. Ablation shows supervision loss is essential; SuperCycle balances target accuracy and reconstruction fidelity. For A549 lung cancer, 8/10 top predicted targets had Open Targets evidence (vs 2/10 random) and it recovered KDR/VEGFR-2.

## Why it matters for our work
PDGrapher is the clearest example in our corpus of *inverse* perturbation modeling — predicting the intervention that yields a target state rather than the state that follows an intervention. That framing is orthogonal to the BioReasoning Challenge's forward up/down/none direction task (Tracks A/B), but it sharpens the distinction between "response prediction" and "perturbagen discovery" that our agentic Track B pipeline conflates. Its causal-graph inductive bias (edge mutilation on PPI/GRN) and the finding that network-proximity structure carries signal are directly relevant to gene-regulation strategy and to any Track C approach that wants a graph prior rather than a pure sequence/transcriptomics foundation model.

## Limitations / open questions
- Genetic (single-gene KO) datasets yield much weaker signal than chemical multi-gene ones (recall margins <1%), attributed to compensatory mechanisms masking KO phenotypes.
- Depends on a "proxy causal graph" (BioGRID PPI or GENIE3 GRN) whose quality bounds performance; the causal claim is inductive-bias, not verified causality.
- Absolute recall values are modest — the combinatorial target-set task remains hard.
- Restricted to cancer cell lines with LINCS-style bulk expression; no single-cell or in-vivo validation.
