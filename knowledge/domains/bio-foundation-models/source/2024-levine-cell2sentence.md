---
source_url: https://doi.org/10.1101/2023.09.11.557287
source_type: papers
title: "Cell2Sentence: Teaching Large Language Models the Language of Biology"
author: Daniel Levine et al.
retrieved: 2026-07-16
doi: 10.1101/2023.09.11.557287
---

# Cell2Sentence: Teaching Large Language Models the Language of Biology

**Authors:** Daniel Levine, Syed Asad Rizvi, Sacha Lévy, Nazreen Pallikkavaliyaveetil, David Zhang, Xingyu Chen, Sina Ghadermarzi, Ruiming Wu, Zihe Zheng, Ivan Vrkic, Anna Zhong, Daphne Raskin, Insu Han, Antonio Henrique de Oliveira Fonseca, Josue Ortega Caro, Amin Karbasi, Rahul M. Dhodapkar, David van Dijk
**Year:** 2024
**Venue:** bioRxiv (Yale / UPenn; ICML 2024)

## Abstract
Cell2Sentence (C2S) adapts off-the-shelf large language models to single-cell transcriptomics by transforming a cell's gene-expression profile into a "cell sentence" — the gene names written in order of decreasing transcript abundance. This reformulates scRNA-seq as plain text, letting a standard causal LM be fine-tuned for cell generation, complex cell-type annotation, and data-to-text generation. The authors show GPT-2 fine-tuned with C2S generates biologically valid cells conditioned on cell type, predicts cell types from cell sentences, and produces natural-language biological summaries, while retaining general text ability — all using existing HuggingFace models and libraries.

## Key contributions
- A reversible rank-order encoding turning an expression vector into a sequence of gene-name tokens (a "cell sentence"), bridging NLP tooling and transcriptomics with no new architecture.
- Demonstrates that natural-language pretraining transfers to single-cell tasks: NL-pretrained-then-C2S models beat models trained on cell sentences from scratch.
- A single LM framework spanning three task families — conditional cell generation, combinatorial cell-label classification, and abstract/text generation from cells.

## Methods
Each dataset is QC-filtered, row/log-normalized (row sum 10⁴), then rank-order transformed so genes are listed high-to-low expression. A per-dataset log-linear regression maps a gene's log-rank back to expression, making the transform reversible. Models fine-tuned include GPT-2 (small/medium/large) and Pythia-160M, on an immune-tissue dataset (273,502 cell sentences, 35 cell types), a cytokine-stimulation dataset (140 combinatorial labels), and a 37M-cell multi-tissue dataset; sentences are typically truncated to the top-100 genes for compute. Baselines include single-cell FMs scGPT and Geneformer plus GPT-3.5-Turbo, Mistral-7B, and Mixtral-8×7B for the text task.

## Key results
- Reconstruction: the rank→expression linear model captures over 81% of gene-expression variance on immune tissue; fine-tuned models generate genes with over 99% validity and 98% uniqueness.
- Cell generation: generated cells correlate with real per-cell-type averages capturing over 94% of expression variation; k-NN cell-type accuracy on generated cells peaks at 54%, and NL-pretrained models beat from-scratch models.
- Annotation: C2S outperforms scGPT, Geneformer, and non-single-cell baselines on exact and partial combinatorial-label accuracy, including out-of-distribution bulk datasets (L1000, GTEx).
- Text generation: only C2S produces abstracts differentiated per study, sitting ~50% closer (MMD) to held-out ground-truth abstracts than GPT-3.5/Mixtral zero/10-shot baselines.

## Why it matters for our work
C2S is a direct precedent for the Track C hypothesis that a general LLM can be a computational engine for cellular behavior: it shows a plain GPT-2 becomes competitive with dedicated single-cell foundation models simply by reframing expression as ranked-gene text. The "cell sentence" (rank-ordered gene list) is a lightweight, tokenizer-free representation we could feed to GPT-OSS for perturbation up/down/none prediction (Tracks A/B) or cell-type reasoning — no bespoke encoder, and it keeps the model's language ability for producing explanations alongside predictions.

## Limitations / open questions
- Truncating to top-100 genes discards most of the transcriptome; the rank encoding drops absolute magnitudes, recovered only approximately via a per-dataset linear fit.
- Backbones are small (GPT-2/Pythia-160M) and scaling behavior is left to future work; k-NN cell-type accuracy (peak 54%) is modest.
- Per-dataset regression parameters must be saved and reapplied, and out-of-vocabulary/duplicate generated genes require post-hoc handling.
