---
source_url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12393277/
source_type: papers
title: "scELMo: Embeddings from Language Models are Good Learners for Single-cell Data Analysis"
author: Tianyu Liu et al.
retrieved: 2026-07-16
doi: 10.1101/2023.12.07.569910
---

# scELMo: Embeddings from Language Models are Good Learners for Single-cell Data Analysis

**Authors:** Tianyu Liu, Tianqi Chen, Wangjie Zheng, Xiao Luo, Yiqun Chen, Hongyu Zhao
**Year:** 2025
**Venue:** bioRxiv (preprint; Yale, UCLA, Johns Hopkins)

## Abstract
scELMo (Single-cell Embedding from Language Models) uses a general-purpose LLM (GPT-3.5) both to write text descriptions of single-cell metadata (genes, proteins, cell types) and to embed those descriptions via the LLM's embedding layer. These frozen text embeddings are combined with raw expression profiles either by matrix operation (zero-shot framework) or by feeding them into a light task-specific model (fine-tuning framework). Without pre-training a new foundation model, scELMo handles clustering, batch-effect correction, and cell-type annotation, and its fine-tuning mode extends to in-silico treatment analysis and perturbation modeling. It reports matching or beating scGPT, Geneformer, GenePT, and GPTCelltype at far lower resource cost.

## Key contributions
- Reframes an scFM as reuse of a frozen LLM's text embeddings of gene/cell metadata — no domain pre-training.
- Two frameworks from the same embeddings: zero-shot (matrix combine) and fine-tuning (adaptor with contrastive learning).
- Weighted-average (wa) cell-embedding scheme that uses expression as weights, vs GenePT's arithmetic average (aa) which ignores expression scale.
- Adds cell-level (cell-type/state) embeddings, which GenePT could not.

## Methods
Candidate LLMs (GPT-2/3.5/4, Llama-2-70B, Mistral, bioGPT, Claude-2, Bard/PaLM-2) were screened for hallucination via BLEU and Human-Eval against NCBI/GeneCards; GPT-3.5 won on the accuracy/query-time trade-off. Cell embedding = AVG(X)·e_f + e_c, where e_f/e_c are LLM feature/cell embeddings; aa divides by gene count, wa divides each cell by its expression sum. For annotation and perturbation, embeddings are combined with existing models (kNN adaptor, CINEMA-OT, CPA, GEARS). In-silico target discovery zeroes a gene and measures the cosine-similarity shift of disease-cell embeddings toward control (threshold 1e-4, top-10 DEGs).

## Key results
- GPT-3.5 gene embeddings hit 0.931 kNN accuracy predicting Geneformer functional annotations; same-gene cosine similarity >0.9, cross-gene 0.74–0.84.
- wa beats aa for clustering, and beats SC3/scVI on 3/4 datasets; adding cell-type embeddings pushes clustering scores near 1.
- Fine-tuned adaptor annotation is comparable to scGPT/Geneformer but needs no A100-scale pre-training.
- Perturbation: GPT-3.5 embeddings improve GEARS PCC across 4 perturb-seq datasets (Wilcoxon p=0.027) and CPA R2 on Openproblems (p≈6e-12); improves CINEMA-OT causal separation (p=0.031).

## Why it matters for our work
Directly relevant to Track C (foundation models) and the Track A/B gene-perturbation prediction: scELMo is evidence that frozen LLM text embeddings of gene function are a cheap, strong biological prior — no pre-training, runs without a GPU cluster. For our up/down/none direction prediction, its GEARS/CPA gains show LLM gene embeddings inject useful perturbation-target knowledge into expression-change predictors. The aa-vs-wa and cell-type-embedding ablations are practical recipes if we build our own LLM-embedding features.

## Limitations / open questions
- Frozen GPT-3.5 embeddings; newer/stronger LLMs likely help but untested here.
- No knowledge for recently discovered genes → weak on rare-disease / low-resource data.
- Hard to scale to high-feature modalities (GWAS, scATAC-seq); perturbation gains are modest and dataset-dependent.
