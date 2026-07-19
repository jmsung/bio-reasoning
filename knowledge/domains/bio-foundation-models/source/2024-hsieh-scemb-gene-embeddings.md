---
source_url: https://doi.org/10.1101/2024.09.24.614685
source_type: papers
title: "scEMB: Learning context representation of genes based on large-scale single-cell transcriptomics"
author: Kang-Lin Hsieh et al.
retrieved: 2026-07-16
doi: 10.1101/2024.09.24.614685
---

# scEMB: Learning context representation of genes based on large-scale single-cell transcriptomics

**Authors:** Kang-Lin Hsieh, Yan Chu, Xiaoyang Li, Patrick G. Pilié, Yulin Dai
**Year:** 2024
**Venue:** bioRxiv (preprint; PMC11463607)

## Abstract
scEMB is a transformer-based single-cell foundation model that learns context-aware gene embeddings from large-scale single-cell transcriptomics. Pretrained on over 30 million single-cell transcriptomes curated from CZ CELLxGENE, it uses a binned-expression strategy to integrate data across platforms while preserving expression hierarchies and cell-type specificity. On downstream tasks (batch integration, clustering, cell-type annotation) it performs competitively with scGPT and Geneformer, and the authors extend it to in silico perturbation and correlation analyses that recover known CRISPRi perturbation effects and Alzheimer's disease (AD) risk genes.

## Key contributions
- A BERT-backbone scEMB model pretrained on >30M cells (CZ CELLxGENE) with an scGPT-style 100-bin expression tokenization and expression-order-preserving positional embeddings.
- In silico perturbation prediction via cosine similarity of cell embeddings between control and CRISPR-perturbed cells (masking the targeted gene).
- In silico correlation analysis linking disease state-transition embeddings to perturbation effects to nominate therapeutic targets.
- Parameter-efficient fine-tuning recipes (LoRA and Prefix Tuning) for domain adaptation.

## Methods
The backbone is a 12-layer BERT-style transformer producing 768-dimensional cell embeddings (averaged encoder output). Pretraining is masked language modeling: 15% of genes per cell are masked and predicted from remaining context, on unlabeled data. Expression values are normalized to CPM, log1p-transformed, binned into 100 intervals, and ranked. For perturbation work, cell embeddings are concatenated with gene-perturbation embeddings from a PPI/GO-guided gene-relationship graph learned by a 3-layer graph attention network (GAT), then passed through a two-layer MLP to predict altered gene expression. Benchmarks used PBMC 10k (clustering/batch integration, zero-shot), SEA-AD brain MTG (cell-type annotation, fine-tuned), a GSE178317 iPSC-derived microglia CRISPRi dataset (39 single-sgRNA genes), and ROS/MAP snRNA-seq for AD.

## Key results
- Zero-shot clustering and batch integration on PBMC 10k were on par with Geneformer and scGPT (metrics include KMeans NMI/ARI, cLISI, iLISI, kBET, graph connectivity); abstract frames scEMB as superior, discussion as competitive.
- Cell-type annotation on SEA-AD brain MTG (train one batch, test another) was strong across all three models, with differences mainly on rare cell types (AUROC / F1 / accuracy).
- In silico perturbation on 39 CRISPRi genes: top-10 predictions recovered known microglia genes CSF1R and TGFBR1/2; housekeeping gene AARS showed highest cosine similarity.
- In silico correlation analysis surfaced known AD GWAS risk genes PLCG2, SORL1, and TREM2 among top cellular-state-vs-perturbation cosine-similarity hits.

## Why it matters for our work
scEMB is a Track C open-weights-style single-cell foundation model directly comparable to Geneformer and scGPT, which anchor our foundation-model landscape. Its masked-gene, cosine-similarity approach to in silico perturbation is a concrete, embedding-based recipe for the up/down/none perturbation-prediction framing in Tracks A/B: mask the target gene, compare control vs. perturbed cell embeddings, and rank affected genes. The PPI/GO GAT graph fused with cell embeddings is a useful pattern for injecting gene-regulation priors into a prediction pipeline.

## Limitations / open questions
- Preprint; text reports qualitative comparisons and figure-based metrics without head-to-head numeric tables in the body, so the exact margin over scGPT/Geneformer is unclear (abstract "superior" vs. discussion "on par").
- Zero-shot perturbation prediction is flagged as unreliable because most perturbation conditions are absent from pretraining; the fine-tune / correlation workaround is proposed but validated only on small microglia/AD case studies.
- The housekeeping gene AARS ranking highest hints the cosine-similarity signal may conflate ubiquitous expression with true perturbation impact.
