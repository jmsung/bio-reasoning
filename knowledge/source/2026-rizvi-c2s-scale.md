---
source_url: https://doi.org/10.1101/2025.04.14.648850
source_type: papers
title: "Scaling Large Language Models for Next-Generation Single-Cell Analysis"
author: Syed Asad Rizvi et al.
retrieved: 2026-07-16
doi: 10.1101/2025.04.14.648850
---

# Scaling Large Language Models for Next-Generation Single-Cell Analysis

**Authors:** Syed Asad Rizvi, Daniel Levine, Aakash Patel, Shiyang Zhang, Eric Wang, Curtis Jamison Perry, Ivan Vrkic, Nicole Mayerli Constante, Zirui Fu, Sizhuang He, David Zhang, Cerise Tang, Zhuoyang Lyu, Rayyan Darji, Chang Li, Emily Sun, David Jeong, Lawrence Zhao, Jennifer Kwan, David Braun, Brian Hafler, Hattie Chung, Rahul M. Dhodapkar, Paul Jaeger, Bryan Perozzi, Jeffrey Ishizuka, Shekoofeh Azizi, David van Dijk
**Year:** 2026
**Venue:** bioRxiv (Yale University; Google Research / DeepMind)

## Abstract
C2S-Scale scales the Cell2Sentence framework — which represents an scRNA-seq profile as a textual "cell sentence" of rank-ordered gene names — into a family of large language models trained on over one billion tokens of transcriptomic data, biological text, and metadata. Scaling to 27 billion parameters yields consistent gains in predictive and generative capability and enables tasks needing synthesis across multi-cellular context. Reinforcement-learning fine-tuning (GRPO) produces strong perturbation-response prediction, natural-language interpretation, and biological reasoning. This predictive strength drove a dual-context virtual screen that nominated the CK2 kinase inhibitor silmitasertib (CX-4945) for context-selective upregulation of MHC-I antigen presentation, experimentally confirmed in human cell models unseen during training. C2S-Scale surpasses both specialized single-cell foundation models and general-purpose LLMs.

## Key contributions
- A scaled Cell2Sentence LLM family (410M → 27B parameters) unifying transcriptomic and textual data at ~1B-token scale, with demonstrated scaling laws in both full fine-tuning and LoRA regimes.
- GRPO (Group Relative Policy Optimization) reward-based fine-tuning that targets phenotype-linked gene programs (e.g. apoptosis, interferon response) to improve perturbation-response fidelity.
- A dual-context in-silico virtual screen that discovers a context-dependent drug (silmitasertib) and validates it experimentally — an end-to-end model→wet-lab discovery loop.

## Methods
Expression profiles are converted to cell sentences (genes listed high-to-low abundance) and used to train Gemma-family LLMs from 410M to 27B parameters on a multi-task corpus of cell sentences, biological text, and metadata. Downstream fine-tuning has two stages: supervised fine-tuning, then GRPO with rewards computed on scGPT-embedded generated-vs-real cells restricted to phenotype gene sets (e.g. 95 interferon genes from MSigDB hallmark sets ∩ HVGs). Perturbation benchmarks use the Dong et al. cytokine dataset, L1000 (bulk), and SciPlex3 (187 small molecules, 9 held-out drugs, ChemCPA OOD split). Baselines span expression-only scFMs (scGPT, Geneformer, scFoundation), spatial model Nicheformer, perturbation models (scGen, CellOT, CondOT, BioLord, ChemCPA), and frontier LLMs (Llama-3, GPT-4o, Gemini 1.5 Pro). NL tasks scored by BERTScore (F1); perturbation by scFID, MMD, Wasserstein.

## Key results
- State-of-the-art across diverse tasks: C2S-Scale is the only model with consistent high-tier performance across cell-type annotation, embedding, NL interpretation, and perturbation prediction, beating scGPT/Geneformer/scFoundation and GPT-4/Gemini.
- Scaling holds: performance improves monotonically with parameters (410M→27B) and training compute (FLOPs), and with LoRA rank and token count for a fixed 27B model.
- Perturbation: GRPO cuts scFID on interferon genes by 16%; on L1000 apoptosis it lifts Kendall's τ by 9.2% (410M) / 4.9% (1B) and Pearson's r by 6.6% / 3.6% over SFT. Best-in-class scFID/MMD/Wasserstein on fully unseen combinatorial and small-molecule perturbations.
- Spatial: significantly outperforms Nicheformer, scGPT, and GPT-4o on neighborhood prediction; adding BioGRID + CellPhoneDB interaction data gives the biggest gain.
- Discovery: dual-context screen nominated silmitasertib; predicted to raise MHC-I only in high-IFN primary-tumor context, confirmed in WAGA cells where silmitasertib + low-dose IFN-β gave a dose-dependent MHC-I MFI increase (no effect alone).

## Why it matters for our work
This is the scaled successor to Cell2Sentence and the strongest evidence yet for the Track C thesis that an LLM can be a computational engine for cellular behavior — a plain rank-ordered gene-list ("cell sentence") input, no bespoke encoder, beating dedicated scFMs at perturbation prediction. Directly relevant to Tracks A/B: GRPO reward shaping on phenotype gene programs is a concrete recipe for improving directional (up/down/none) perturbation calls, and the cell-sentence representation is a lightweight input we could feed to GPT-OSS. The dual-context virtual screen also models the kind of context-conditioned reasoning the challenge probes.

## Limitations / open questions
- The full model (27B, GRPO on H100s) is heavy; the leaderboard-valid GPT-OSS-120B path differs, so transfer of the GRPO recipe to our open-weights setup is untested.
- Perturbation gains are metric-level (scFID/MMD/Wasserstein/τ); how they map to the discrete up/down/none scoring of Tracks A/B is not shown.
- The silmitasertib validation is a single-compound, single-context anecdote; screen precision/recall over the full library is not reported, and the mechanism is uncharacterized.
