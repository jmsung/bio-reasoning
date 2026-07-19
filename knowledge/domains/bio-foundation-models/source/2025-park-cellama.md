---
source_url: https://doi.org/10.1002/advs.202513210
source_type: papers
title: "CELLama: Foundation Model for Single Cell and Spatial Transcriptomics by Cell Embedding Leveraging Language Model Abilities"
author: Jeongbin Park et al.
retrieved: 2026-07-16
doi: 10.1002/advs.202513210
---

# CELLama: Foundation Model for Single Cell and Spatial Transcriptomics by Cell Embedding Leveraging Language Model Abilities

**Authors:** Jeongbin Park, Sumin Kim, Jiwon Kim, Dongjoo Lee, Sungwoo Bae, Haenara Shin, Daeseung Lee, Hongyoon Choi
**Year:** 2025
**Venue:** Advanced Science (Portrai, Inc. / Seoul National University Hospital)

## Abstract
CELLama (Cell Embedding Leverage Language Model Abilities) is a framework that turns single-cell RNA-seq (scRNA-seq) and spatial transcriptomics (ST) data into natural-language "sentences" — a rank-ordered list of each cell's top-expressed genes plus optional metadata (tissue, condition, spatial niche) — and embeds those sentences with an off-the-shelf sentence transformer. The result is a universal cell-embedding space that supports cell typing, cross-dataset integration, and spatial-context analysis without dataset-specific pipelines, using a large cell atlas as reference.

## Key contributions
- Reframes single-cell foundation modeling as an NLP problem: cell → sentence → sentence-transformer embedding, avoiding training a bespoke transformer from scratch.
- Shows a massively pretrained general sentence transformer ("all-MiniLM-L12-v2", 384-D) already has enough biological intuition for zero-shot cell typing when gene input is constrained (top-k ≈ 16–24).
- Uniquely folds metadata and spatial niche context directly into the embedding via sentence construction — something scGPT/Geneformer cannot do natively.

## Methods
Each cell's expression is converted to a ranked gene list; the top-k genes form a sentence, optionally appended with metadata phrases (e.g., "tissue type of this cell is lung"). Sentences are embedded with a pretrained sentence transformer; cell types are assigned by nearest-neighbor (KNN) search against a reference embedding — so metrics measure embedding fidelity, not a trained classifier. An optional fine-tuning step generates ~160k sentence pairs labeled by PCA-based cosine similarity (set to zero when metadata differs) and adjusts embeddings via a cosine-distance loss. For ST, niche information (nearest neighboring cell types) is added to sentences to enable spatial subtyping.

## Key results
- On Tabula Sapiens (5 tissues, 57 cell types), CELLama with tissue metadata exceeded scGPT on accuracy, precision, and recall in zero-shot cell typing; without metadata it was comparable to scGPT.
- Geneformer failed zero-shot; after training it reached 77.7% vs CELLama's 78.7% accuracy, but with much lower precision/recall. SingleR trailed at 54.2%.
- Pancreas cross-platform mapping (9 batches) onto the Tabula Sapiens reference achieved 98% / 88% recall for alpha / beta cells; scGPT mislabeled rare types (beta 28%, delta <1%).
- Fine-tuned CELLama on COVID-19 lung data beat both original CELLama and scGPT: accuracy 86.7% vs 85.9% vs 86.7%; precision 61.0% / 54.3% / 54.5%; recall 59.5% / 52.4% / 49.7%.
- Runtime is comparable to scGPT/Geneformer, while C2S, AIDO.Cell, UCE, TranscriptFormer, SingleR, and scVI were markedly slower.

## Why it matters for our work
CELLama is a Track C candidate style-point: a metadata-aware, open-weights, cheap foundation model (a 384-D MiniLM sentence encoder) that runs at scGPT-comparable speed without GPU-scale pretraining. Its "cell → sentence" trick is directly relevant to any LLM-as-computational-engine framing of the BioReasoning Challenge, since it shows general language models capture biological structure from gene-rank text alone. The metadata/niche flexibility is a lever for context-conditioned prediction. Caveat for Track A/B up/down/none perturbation prediction: the authors explicitly note CELLama has no generative/decoder layer, so it is not suited to perturbation-effect or gene-regulatory-network inference — its value here is representation and cell typing, not directional response prediction.

## Limitations / open questions
- Not a pure zero-shot model — it needs a reference atlas for similarity-based mapping; no decoder, so no perturbation/GRN prediction.
- Using only top-k genes discards quantitative expression; performance is sensitive to top-k and metadata choice, especially on limited ST gene panels where rare subtypes are missed.
- Metadata-driven clustering is a double-edged sword: wrong or missing metadata can create artificial clusters ("stress test"), requiring stringent metadata QC.
