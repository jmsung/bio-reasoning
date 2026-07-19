---
source_url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12855003/
source_type: papers
title: "Scouter predicts transcriptional responses to genetic perturbations with large language model embeddings"
author: Ouyang Zhu et al.
retrieved: 2026-07-16
doi: 10.1038/s43588-025-00912-8
---

# Scouter predicts transcriptional responses to genetic perturbations with large language model embeddings

**Authors:** Ouyang Zhu, Jun Li (Department of Applied and Computational Mathematics and Statistics, University of Notre Dame)
**Year:** 2025
**Venue:** Nature Computational Science (Brief Communication)

## Abstract
Perturb-seq experiments reveal causal gene effects but are throughput-limited, so most perturbations of interest are never assayed. Existing predictors (GEARS, biolord) encode prior knowledge via Gene Ontology (GO) graphs, whose sparsity and incomplete gene coverage cap their accuracy and applicability. Scouter instead represents each gene by a dense LLM embedding and feeds it through a lightweight compressor–generator neural network. It predicts genome-wide transcriptional responses to both single- and two-gene unseen perturbations, cutting errors from GO-based state-of-the-art by half or more, and beats fine-tuned expression foundation models while requiring no pretraining and running on standard hardware.

## Key contributions
- Replaces GO-graph gene priors with dense LLM gene embeddings (GenePT's length-1,536 vectors from OpenAI `text-embedding-ada-002` over NCBI gene descriptions).
- A simple compressor–generator net; two-gene perturbations handled by summing the two genes' embeddings.
- Works for perturbations absent from the GO graph, where GEARS/biolord cannot predict at all.
- No pretraining; trains end-to-end on one Perturb-seq dataset in under 1 h on an A40 or even a MacBook M2 CPU.

## Methods
Evaluated on the five GEARS-preprocessed Perturb-seq datasets (Dixit, Adamson, Norman, Replogle K562, Replogle RPE1, ~5,000 genes each). To handle as few as ~20 distinct perturbations, Scouter pairs a randomly sampled control cell with a randomly sampled perturbed cell as input/output, yielding n0·Σnk training samples rather than averaged profiles. For gene g it takes E(g) plus K=300 random control cells and returns per-cell predictions (mean as point estimate). Trained with Adam and GEARS's autofocus direction-aware loss (power-scaled MSE + direction-consistency penalty); a separate model per dataset over five (Dixit: ten) train/val/test splits where test perturbations are held out.

## Key results
- Metrics: normalized MSE and 1 − normalized PCC over the top-20 DEGs (both smaller = better). Scouter achieves the lowest of both on all five datasets.
- Single-gene: on average Scouter's MSE/1−PCC are ~half of biolord (48.9% / 56.0%) and GEARS (51.0% / 54.1%).
- Two-gene (Norman): MSE/1−PCC less than half of biolord (34.7% / 38.2%) and less than a quarter of GEARS (21.2% / 22.6%) — gains larger than single-gene.
- Beats fine-tuned foundation models scGPT, scELMo, scFoundation on Adamson and Norman by large margins.
- Example: for CDKN1A perturbation, more accurate than both baselines on 18/20 top DEGs; still predicts for TIMM23, which is missing from the GO graph.
- Ablations: truncating/scrambling NCBI gene text degrades accuracy (e.g. K=10 vs K=100 raises normalized MSE up to 117%), confirming the LLM prior carries real signal; swapping GO for LLM embeddings improves GEARS/biolord too.

## Why it matters for our work
Scouter is direct evidence for the Track A/B thesis: dense LLM gene embeddings are a stronger, more complete perturbation prior than GO graphs, and they let a model predict for genes with no graph coverage — exactly the unseen-perturbation regime the challenge tests. Its direction-aware GEARS loss and the top-20-DEG normalized MSE / 1−PCC metrics map onto our up/down/none direction task and are cheap to adopt. For Track C it is a pointed counterexample: a no-pretraining, CPU-trainable model outperforming fine-tuned scGPT/scELMo/scFoundation, arguing that frozen LLM text embeddings plus a light head may beat heavyweight foundation-model fine-tuning for perturbation prediction.

## Limitations / open questions
- Depends entirely on GenePT text embeddings, so genes with poor/sparse NCBI descriptions (novel or rare genes) inherit weak priors.
- Benchmarked only on five GEARS datasets; only Norman covers two-gene perturbations.
- A separate model is trained per dataset — no demonstrated cross-dataset or cross-cell-line transfer.
- Uses a single frozen `text-embedding-ada-002`; newer/biomedical embedders and larger DEG sets are only partly explored in supplements.
