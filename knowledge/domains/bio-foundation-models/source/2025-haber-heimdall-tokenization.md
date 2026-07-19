---
source_url: https://doi.org/10.1101/2025.11.09.687403
source_type: papers
title: "Heimdall: A Modular Framework for Tokenization in Single-Cell Foundation Models"
author: Ellie Haber et al.
retrieved: 2026-07-16
doi: 10.1101/2025.11.09.687403
---

# Heimdall: A Modular Framework for Tokenization in Single-Cell Foundation Models

**Authors:** Ellie Haber, Shahul Alam, Nicholas Ho, Renming Liu, Evan Trop, Shaoheng Liang, Muyu Yang, Spencer Krieger, Jian Ma
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Single-cell foundation models (scFMs) depend critically on how a cell's expression profile is tokenized into model inputs, yet this design space is poorly understood — each scFM ships its own bespoke tokenizer encoding different biological priors. Heimdall is an open-source framework that decomposes any scFM tokenizer into modular components: a gene-identity encoder (F_G), an expression encoder (F_E), and a "cell sentence" constructor (F_C) with submodules order, sequence, and reduce. Using a fixed transformer trained from scratch, the authors systematically evaluate tokenization strategies for cell-type classification under distribution shift (cross-tissue, cross-species, spatial gene-panel) plus a reverse perturbation task. Tokenization has minimal in-distribution impact but is decisive under shift, with F_G and order driving the largest gains and F_E adding further improvement; hybrid tokenizers recombined from existing scFMs outperform any single strategy.

## Key contributions
- A modular decomposition (F_G / F_E / F_C{order, sequence, reduce}) that reconstructs five existing tokenizers (Geneformer, scGPT, scBERT, scFoundation, UCE) in one framework and enables per-module ablation and attribution.
- Controlled benchmarks isolating the tokenizer by fixing model size, context length, and pretraining across all variants.
- Demonstration that hybrid tokenizers built by recombining modules beat the individual scFM tokenizers they came from.

## Methods
Each cell is encoded via F_G (gene identity: random, Gene2vec, GenePT, ESM2, HyenaDNA embeddings), F_E (expression: No-Op, quantile/integer/auto binning, continuous), and F_C which orders genes (expression-ranking vs. chromosome vs. random), forms the sequence (truncation to context), and reduces to a fixed input. Paired-cell tasks add an aggregator (elementwise mean/sum, symmetric/asymmetric concatenation). A small fixed transformer is trained from scratch (and optionally MLM-pretrained on 10k/100k/1M cells) and fine-tuned; performance is reported as Matthews correlation coefficient (MCC) over 3–10 random seeds, with paired Holm-corrected significance tests.

## Key results
- **In-distribution (cross-tissue) tokenizer choice barely matters:** Geneformer-tok best at MCC 0.40, others 0.36–0.39, overlapping a linear raw-expression baseline (0.40). MLM pretraining on up to 1M cells gave only marginal gains.
- **Cross-species:** scBERT-tok best (0.66) after orthology mapping; UCE-tok's advantage traces to its ESM2 sequence-derived F_G, not F_E/F_C.
- **Gene-panel shift (overlap-35):** scBERT-tok best (0.55), all tokenizers beat the linear baseline (0.40); F_G had the largest impact (Gene2vec strongest, its co-expression prior stabilizing unseen test genes).
- **Reverse perturbation:** scBERT-tok best (MCC 0.39), UCE-tok worst (0.17); adding any F_E to UCE-tok helped, and combining scBERT-tok's F_E with Geneformer-tok's order gave the largest boost.

## Why it matters for our work
For Track C (foundation models) this is a direct playbook: it isolates *which* tokenizer components actually drive generalization, showing that gene-identity embeddings and expression-aware ordering — not pretraining scale — govern cross-tissue, cross-species, and cross-panel transfer. Since our perturbation up/down/none prediction (Track A/B) is exactly a distribution-shift regime, the finding that F_E and order dominate the reverse-perturbation task suggests where to spend effort if we adapt an scFM: prefer expression-aware ordering (Geneformer-style) plus an explicit expression encoder, and a co-expression-informed F_G, rather than defaulting to any one off-the-shelf tokenizer.

## Limitations / open questions
- Pretraining ablations used only an MLM objective; other objectives / larger corpora could shift conclusions.
- A single small fixed transformer was tested; scaling or alternative architectures (e.g. state-space models) may change tokenizer trade-offs.
- Scope limited to cell-type classification and reverse perturbation — perturbation-response modeling, batch integration, GRN inference, and spatial tasks are untested.
