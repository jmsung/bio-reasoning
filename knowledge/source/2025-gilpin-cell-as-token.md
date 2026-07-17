---
source_url: https://doi.org/10.1093/bioinformatics/btaf595
source_type: papers
title: "The cell as a token: high-dimensional geometry in language models and cell embeddings"
author: William Gilpin
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btaf595
---

# The cell as a token: high-dimensional geometry in language models and cell embeddings

**Authors:** William Gilpin (UT Austin Physics; Medici Therapeutics)
**Year:** 2025
**Venue:** Bioinformatics (review article)

## Abstract
A review arguing that single-cell "virtual cell" foundation models and natural-language embeddings share deep structure: both partition unstructured data into tokens placed in a high-dimensional vector space, both rely on the *distributional hypothesis* (similarity inferred from recurring context), and both derive their power from low-dimensional, anisotropic manifolds inside that space. Gilpin maps concepts from NLP embedding geometry (polysemy, static vs dynamic embeddings, analogy arithmetic, cross-lingual latent spaces, mechanistic interpretability) onto single-cell genomics, and uses the mismatches to predict where cell foundation models will struggle.

## Key contributions
- Frames the **cell (not the gene) as the natural "token"**: genes don't recur within a genome and need expression to vary, so cells are the minimal unit where meaningful context recurs.
- Systematic analogy table: word2vec matrix factorization ↔ low-rank single-cell count matrices; polysemy ↔ unresolved cell subtypes; analogy vectors ↔ conserved relative cell-type positions across organs/species; cross-lingual latent spaces ↔ universal/cross-species cell embeddings.
- Imports **mechanistic-interpretability tooling** (linear probes, sparse autoencoders, topological/intrinsic-dimension estimators) as a program for probing what cell foundation models actually encode.

## Methods
Conceptual review; no new experiments. Synthesizes NLP embedding theory (distributional hypothesis, self-attention producing context-dependent "clouds" per token, anisotropy signaling generative structure) against single-cell methods (diffusion pseudotime, RNA velocity, harmony batch correction, spatial transcriptomics, CITE-seq). Illustrations include a word2vec embedding of a novel and a PBMC scRNA-seq embedding. Code at github.com/williamgilpin/celltoken.

## Key results
- Both language and gene-expression manifolds have intrinsic dimensionality ~10^1 despite feature dimension ~10^2 (language) and ~10^5 measured genes (cells); downstream performance plateaus at a fixed multiple of manifold dimension.
- Anisotropy in embeddings indicates real structure in the generative process (linguistic or biological), not noise.
- Cell embeddings recover canonical low-dim shapes: cell cycle/circadian → rings, tissue → grids, differentiation → branches/pitchforks; intrinsic dimensionality of expression correlates with pluripotency across taxa.
- Notes **conflicting benchmark results**: current single-cell foundation models show unclear advantage on zero-shot and perturbation-prediction tasks (cites Ahlmann-Eltze 2025, Kedzierska, Csendes), unlike LLMs' clear scaling gains.

## Why it matters for our work
Directly relevant to Track C foundation-model selection and our gene-regulation strategy. It gives a principled lens for *why* a cell FM embedding might or might not carry a perturbation's up/down/none signal (Track A/B): the answer lives in whether the regulatory effect corresponds to movement along an informative low-dim manifold. The interpretability toolkit (linear probes, SAEs) suggests concrete ways to audit whether an embedding actually encodes the regulatory grammar we need, and the benchmark caveats reinforce our own finding that FM embeddings don't automatically beat simple baselines.

## Limitations / open questions
- Pure review — no benchmarks or reproducible metrics of its own.
- The cell↔token analogy breaks where cells differ most from words: biological context is multiscale/incomplete/indirect, cells can't be resampled without perturbing the system, and a cell's "meaning" changes irreversibly (differentiation, senescence) — demanding temporally-aware, causal, multimodal embeddings that current FMs lack.
- Leaves open what a good benchmark for "parsing indirect regulatory logic" looks like.
