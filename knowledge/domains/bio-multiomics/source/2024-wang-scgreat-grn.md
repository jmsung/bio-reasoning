---
source_url: https://doi.org/10.1016/j.isci.2024.109352
source_type: papers
title: "scGREAT: Transformer-based deep-language model for gene regulatory network inference from single-cell transcriptomics"
author: Yuchen Wang et al.
retrieved: 2026-07-16
doi: 10.1016/j.isci.2024.109352
---

# scGREAT: Transformer-based deep-language model for gene regulatory network inference from single-cell transcriptomics

**Authors:** Yuchen Wang, Xingjian Chen, Zetian Zheng, Lei Huang, Weidun Xie, Fuzhou Wang, Zhaolei Zhang, Ka-Chun Wong
**Year:** 2024
**Venue:** iScience (Cell Press)

## Abstract
scGREAT is a supervised deep-learning framework that infers gene regulatory networks (GRNs) from single-cell transcriptomics by casting GRN reconstruction as a binary classification of transcription-factor (TF)–target gene pairs. Its central analogy treats genes/cells like words/sentences, letting it adapt the NLP transformer to genomics. Each gene is represented by two learned "dictionaries": a gene-expression dictionary (a neural encoder over the scRNA-seq matrix) and a gene-biotext dictionary (BioBERT embeddings of the gene symbol), combined with a positional embedding that encodes TF-vs-target order. A modified transformer attention engine fuses these multimodal features to predict whether a regulatory edge exists (and, optionally, its direction via a 3-class causality head). Across seven BEELINE benchmarks and four ground-truth network types, scGREAT outperforms prior methods, and its predicted-but-unannotated edges are corroborated by literature and spatial transcriptomics.

## Key contributions
- Reframes GRN inference as an NLP-style sequence problem: TF-target pairs as token pairs through a transformer attention backbone.
- Two per-gene "dictionaries" (lookup tables): a neural-encoder gene-expression embedding and a BioBERT gene-symbol biotext embedding (both length 768), plus a positional embedding for regulatory direction.
- A causality-inference head (3-class: no edge / gene1→gene2 / gene2→gene1) inspired by CNNC, giving directionality on top of edge existence.
- External validation of novel predicted edges via spatial transcriptomics co-expression and a literature search.

## Methods
Data follow the BEELINE protocol (Pratapa et al., Nat. Methods 2020): 7 scRNA-seq datasets (hESC, hHEP, mDC, mESC, mHSC-E/GM/L), top 500/1000 most-variable genes, Z-score normalized. Ground-truth edges come from four networks (STRING, non-specific ChIP-seq, cell-type-specific ChIP-seq, LOF/GOF). Positives are known TF-gene edges; negatives use hard-negative sampling (HNS), drawing a same-TF non-edge per positive; a 2/3 train+val (9:1) vs 1/3 held-out test split follows GENELink. Inputs = summed expression + biotext + positional embeddings, fed to multi-head self-attention over the gene pair, then flattened through dense layers with PReLU, dropout 0.2, residual connections, and softmax. Trained with Adam (lr 1e-5), batch 32, ≤80 epochs on a single RTX 3080. Metrics: AUROC and AUPRC (the latter emphasized for class imbalance).

## Key results
- Best average AUROC of 0.913 across the seven datasets, vs the second-best GENELink at 0.867 (Table 2 backbone comparison; CNNC 0.666, GNE 0.735).
- Won AUROC on all 44/44 dataset-network combos and AUPRC on 93% (42/44); on cell-type-specific ChIP-seq, +6.3 / +15.5 / +23.9 points over GENELink / GNE / CNNC.
- Per-network average AUROC: STRING 94.3%, cell-type-specific 90.5%, non-specific ChIP-seq 89.4%, LOF/GOF 91.0%; specific-network AUPRC 76.65% (avg +34.1% over baselines).
- Ablations: removing the transformer drops AUROC 7.2 pts (90.2→82.9) and AUPRC 12.6 pts; removing BioBERT biotext costs only ~0.75 AUROC / 1.68 AUPRC — text helps but marginally.
- Competitive runtime (~5–12 min for TF+500/1000 genes) vs CNNC's 2–20 h; recovered unannotated edges (E2F1→TOP2A, SOX2→CCND1, TRIM28→ID1, STAT3→HIF1A) confirmed in the literature.

## Why it matters for our work
scGREAT is directly relevant to the BioReasoning Challenge's regulatory-direction framing: it predicts TF→target edges and, via its causality head, direction (gene1→gene2 vs gene2→gene1) — the same up/down/none-style decision structure as Track A/B. Two design choices are worth stealing: (1) fusing a text/LLM-derived gene embedding (BioBERT biotext) with an expression embedding — the same "literature embedding + expression" recipe as GenePT, and a lever for Track C foundation-model features; and (2) hard-negative sampling to combat the extreme sparsity of real regulatory edges, which mirrors our over-abstention problem on Track B. The ablation is a useful caution: the LLM/text channel added <1 point of AUROC here, so text embeddings are a complement, not a silver bullet — most signal came from expression + the transformer.

## Limitations / open questions
- Supervised: assumes reliable ground-truth edges and enough negatives; uniform/hard negative sampling can mislabel truly-regulatory pairs as negatives.
- BioBERT biotext adds little (<1% AUROC) — generic biomedical text doesn't capture dataset-specific regulation; authors propose semi-supervised learning and richer gene-symbol representations as future work.
- Fails on very sparse networks (mHSC-L: density ~0.048, only ~137 positives) where AUPRC underperforms; noisy datasets (mDC) show elevated false positives.
- Cannot always distinguish activation vs inhibition (e.g., HDAC2 missed edges) since identical expression patterns can carry opposite regulatory labels.
