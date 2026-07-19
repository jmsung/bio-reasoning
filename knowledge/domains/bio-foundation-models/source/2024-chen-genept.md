---
source_url: https://doi.org/10.1101/2023.10.16.562533
source_type: papers
title: "GenePT: A Simple But Effective Foundation Model for Genes and Cells Built From ChatGPT"
author: Yiqun Chen et al.
retrieved: 2026-07-16
doi: 10.1101/2023.10.16.562533
---

# GenePT: A Simple But Effective Foundation Model for Genes and Cells Built From ChatGPT

**Authors:** Yiqun Chen, James Zou
**Year:** 2024
**Venue:** bioRxiv (Stanford)

## Abstract
GenePT is a foundation model for genes and cells built without any single-cell pretraining. Instead of learning representations from millions of expression profiles (as Geneformer and scGPT do), GenePT takes the NCBI text summary of each gene and passes it through OpenAI's GPT-3.5 `text-embedding-ada-002` API to produce a 1,536-dimensional gene embedding. Cell embeddings are derived two ways: GenePT-w (expression-weighted average of gene embeddings, L2-normalized) and GenePT-s (translate each cell into a sentence of gene names ranked by expression, then embed the sentence). With no dataset curation or additional training, GenePT matches or beats expression-trained single-cell foundation models on gene-property and cell-type tasks, arguing that LLM embeddings of literature are a simple, complementary, resource-efficient path to biological foundation models.

## Key contributions
- Shows LLM text embeddings of gene summaries encode intrinsic gene biology (RQ1) and that sentence-of-genes embeddings encode cell biology (RQ2), with no expression-data pretraining.
- Two lightweight cell-embedding recipes: GenePT-w (weighted gene-embedding average) and GenePT-s (GPT-3.5 sentence embedding of expression-ranked gene names).
- Uses an orthogonal information source (literature) vs expression-derived models, motivating ensembling; embeds ~33,000 genes plus ~60,000 HGNC aliases.

## Methods
Gene names were unified from Geneformer and scGPT vocabularies; for each gene, the NCBI summary (mean 73 words) was embedded with GPT-3.5 into a 1,536-d vector. scRNA-seq is scanpy-normalized (10,000 counts/cell, log1p) before building cell embeddings. Downstream tasks reuse the exact benchmarks from Geneformer/scGPT: gene functional-class prediction (15 classes), four binary gene-property tasks, gene-gene interaction (GGI), protein-protein interaction (PPI, three datasets), unsupervised gene programs, cell-type clustering (six datasets, ARI/AMI/ASW), and batch-integration. Classifiers are deliberately simple off-the-shelf L2-regularized logistic regression / random forests with cross-validation to guard against overfitting.

## Key results
- Gene functional class (15-way): 96% accuracy on a 30% held-out split; on the 21,000-gene Gene2vec-overlap subset GenePT hit 0.95 vs Gene2vec 0.86 (5-fold CV).
- Gene-gene interaction: GenePT AUC 0.82 vs 0.65–0.67 for Gene2vec/scGPT/Geneformer embeddings and 0.51 random; beats Du et al.'s DNN (0.77).
- PPI: GenePT beats all baselines on all three PPI datasets; only ~4% train/test leakage in Lit-BM, and removing overlapping pairs did not change performance.
- Cell clustering (nine tasks): scGPT and GenePT gave the most biological signal on five and four tasks respectively; GenePT-s > GenePT-w > Geneformer on ARI/AMI.
- Batch effect: on cardiomyocytes, patient-cluster ARI fell from 0.33 (raw) to 0.07 (GenePT-s); disease-label prediction 88% (GenePT-s and scGPT tie) vs 71% Geneformer.

## Why it matters for our work
GenePT is a strong Track C reference point: it shows that a text-only, no-pretraining embedding built from NCBI summaries + an LLM embedding API can rival expensive single-cell foundation models on gene-property and cell-type tasks — a cheap baseline and a complementary signal to expression-based models like scGPT/Geneformer. Its evidence that literature embeddings capture gene-gene/protein-protein interactions and dosage-sensitivity is directly relevant to reasoning about gene regulation and up/down/none direction prediction (Tracks A/B), and its ensembling result (text + expression embeddings beat either alone) suggests a concrete lever for our own predictors.

## Limitations / open questions
- Only uses existing NCBI summaries, so poorly documented or novel gene functions are missed; embeddings are not tissue/cell-type specific and may miss context-dependent roles.
- Quality is capped by the frozen GPT-3.5 embedding model; fine-tuning or newer embedders could shift results, and closed-API dependence limits reproducibility.
- Cell-type clustering concordance is an admittedly limited proxy for embedding utility; not evaluated on perturbation-response or drug-gene tasks (flagged as future work).
