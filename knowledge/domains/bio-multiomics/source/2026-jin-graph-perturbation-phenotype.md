---
source_url: https://doi.org/10.64898/2026.03.20.712202
source_type: papers
title: "A graph-based learning approach to predict the effects of gene perturbations on molecular phenotypes"
author: Yiyang Jin et al.
retrieved: 2026-07-16
doi: 10.64898/2026.03.20.712202
---

# A graph-based learning approach to predict the effects of gene perturbations on molecular phenotypes

**Authors:** Yiyang Jin, Yuriy Sverchkov, Anastasiya Sushkova, Michael Ohtake, Christopher Emfinger, Mark Craven
**Year:** 2026
**Venue:** bioRxiv (preprint)

## Abstract
Large-scale CRISPR knockout/knockdown screens are expensive, so this work presents a general, learning-method-agnostic, graph-based approach that predicts whether perturbing a gene will significantly affect a molecular phenotype, given measured effects for other genes. Each gene is a node in a knowledge graph; each phenotype is represented by one or more surrogate "target" nodes. A feature vector for every (source gene, phenotype) pair is fed to standard classifiers. Across four diverse phenotypes the learned models show relatively high accuracy, beat standard baselines, learn well from small training sets, benefit from multiple evidence sources, and often transfer across phenotypes.

## Key contributions
- A phenotype-agnostic framing: represent a phenotype as surrogate target node(s) in a knowledge graph, then learn a binary classifier over (source gene, phenotype) feature vectors — one model can serve multiple phenotypes, unlike prior single-phenotype methods (DeepEP, DeepHE, EPGAT) or expression-only methods (GEARS, BioDSNN).
- A rich feature representation combining source-node, target-node, and source-target relation (path/diffusion) features drawn from STRING PPIs, Human Protein Atlas abundances, UniProt/Reactome localization, and GO annotations.

## Methods
The knowledge graph uses the human physical subnetwork of STRING for edges; node attributes are cellular abundance (Human Protein Atlas), 41 binary subcellular-localization features (UniProt + Reactome), and 64-dim node2vec embeddings of a GO-similarity graph (built the GEARS way from Jaccard overlap of GO annotations). The feature vector x(g,P) concatenates source features n(g), target features n(P), and source-target relation features e(g→P). Relation features encode path evidence n-grams (E/D/T STRING evidence categories), best-path confidence products of STRING combined scores, path topology (shortest-path thermometer encoding, path counts, degree products), random-walk-with-restart diffusion scores (α = 0.2/0.4/0.6), and cosine/difference similarities between source and target feature groups. Four learners are applied: elastic-net logistic regression, random forest, XGBoost, and neural nets, with balanced class weights and internal 5-fold CV for hyperparameter tuning. Labels come from genome-scale CRISPR screens (MaGeCK FDR < 0.1 = positive) for four phenotypes: cholesterol homeostasis (target SREBP2), cholesterol uptake (LDLR), influenza A replication (8 host-interacting targets), and mitochondrial protein abundance (source = knocked-out gene, target = measured protein).

## Key results
- Average AUROC of 0.72 across the four phenotypes, with the four learning methods performing comparably — evidence of generality.
- Learning methods exceed the shortest-path-length and target-diffusion baselines for all phenotypes; a learned model gives the best accuracy in 3 of 4 phenotypes (RWR/heat positive-diffusion baselines are competitive and best on influenza).
- Learning curves often reach near-maximum AUROC with only a small fraction of the training data.
- Ablations: models using all features are top or second-best in every case; source-target relation features consistently add predictive value and, being node-identity-agnostic, enable cross-phenotype transfer. Every evidence-type feature group has predictive value.
- Transfer learning across phenotypes generally works (models trained on one phenotype predict another), except mitochondrial protein abundance, which relies heavily on target features and does not transfer. Results are insensitive to negative-instance definition and to target-node specification.

## Why it matters for our work
This is a direct, interpretable alternative to the foundation-model framing behind Track C. The BioReasoning Challenge's Track A/B ask for up/down/none-style directional calls on perturbation effects; this paper shows a lightweight knowledge-graph + classic-ML pipeline that predicts significant-effect vs not, generalizes to unseen genes and phenotypes, and works with small training sets — attractive where labeled perturbation data is scarce. The evidence-fusion recipe (PPI paths, diffusion scores, localization, GO embeddings, abundance) and the finding that node-agnostic relation features transfer across phenotypes are reusable design cues for our own gene-regulation prediction and for engineering features that complement scFM embeddings.

## Limitations / open questions
- Binary "significant effect vs not" only; does not predict effect direction or magnitude, and average AUROC 0.72 leaves substantial headroom.
- Requires a phenotype to be expressible as a small set of surrogate target nodes — awkward for phenotypes without obvious target proxies.
- Depends on noisy genome-wide screens with many false negatives; authors flag graph augmentation (transcriptional regulation, orthology), more data, GNN extensions, and interpretability as future work.
