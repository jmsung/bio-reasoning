---
source_url: https://doi.org/10.1038/s41592-025-02707-1
source_type: papers
title: "A visual–omics foundation model to bridge histopathology with spatial transcriptomics"
author: Weiqing Chen et al.
retrieved: 2026-07-16
doi: 10.1038/s41592-025-02707-1
---

# A visual–omics foundation model to bridge histopathology with spatial transcriptomics

**Authors:** Weiqing Chen, Pengzhi Zhang, Tu N. Tran, Yiwei Xiao, Shengyu Li, Vrutant V. Shah, Hao Cheng, Kristopher W. Brannan, Keith Youker, Li Lai, Longhou Fang, Yu Yang, Nhat-Tu Le, Jun-ichi Abe, Shu-Hsia Chen, Qin Ma, Ken Chen, Qianqian Song, John P. Cooke, Guangyu Wang
**Year:** 2025
**Venue:** Nature Methods

## Abstract
OmiCLIP is a visual–omics foundation model that links H&E histopathology images and spatial transcriptomics (ST) in a shared embedding space. Transcriptomic profiles are turned into "sentences" by concatenating the top-expressed gene symbols per tissue patch, then a CLIP-style contrastive objective aligns image and gene-sentence encoders. The model is trained on ST-bank, a curated corpus of 2.2 million paired tissue-image / transcriptome patches across 32 organs from Visium data. On top of OmiCLIP the authors build **Loki**, a platform with five functions: tissue alignment, tissue annotation (via bulk RNA-seq or marker genes), cell-type decomposition, image↔transcriptomics retrieval, and ST gene-expression prediction from H&E. Across 22 SOTA baselines, 5 simulations, 19 public and 4 in-house datasets, Loki shows consistent accuracy and robustness.

## Key contributions
- First contrastive visual–omics foundation model pairing H&E images with transcriptomics (extends the PLIP/CONCH visual–language line to omics).
- "Gene-sentence" trick: represent a spot's transcriptome as a text string of top genes, letting a CLIP text encoder ingest expression.
- ST-bank: 2.2M paired image–transcriptome patches across 32 organs.
- Loki: one embedding space powering five downstream tasks, mostly zero-shot / lightweight fine-tuning.

## Methods
OmiCLIP embeds patch-level H&E images and gene-symbol sentences into a shared 768-dim space via contrastive learning. Loki Align uses adapted coherent point drift (CPD) on the embeddings to register ST-to-ST, image-to-image, and image-to-ST sections. Loki Annotate scores cosine similarity between image embeddings and bulk-RNA-seq or marker-gene sentence embeddings, taking the highest-similarity label. Loki Decompose plugs OmiCLIP embeddings into Tangram's optimization to deconvolute cell types from either image patches or ST spots using an scRNA-seq reference. Loki PredEx predicts gene expression as a similarity-weighted sum over reference ST spots. Retrieval is evaluated with Recall@K.

## Key results
- **Annotation (marker genes, zero-shot):** Loki F1 0.59–0.96 across CRC7K, WSSS4LUAD, LC25000, PatchCamelyon vs OpenAI CLIP 0.03–0.34. With only 0.5% of labels, median F1 0.89 on kidney cancer (vs CLIP 0.81); median F1 0.82 with 0.1% of labels on another set.
- **Cell-type decomposition:** Loki in ST mode and image mode ranked top two (impact scores 1.32 and 1.11), beating Tangram, Seurat, CARD, CytoSPACE, Cell2location, SpatialDWLS, RCTD (0.87 to −1.82). Swapping in single-cell FM embeddings (scGPT, scFoundation, GeneFormer) ranked only 6th, 8th, 9th.
- **Retrieval:** Loki Recall@10% 0.21–0.30 on brain/heart/kidney/breast — ~2.3–3.2× higher than OpenAI CLIP and PLIP; ~3× on the held-out test set.

## Why it matters for our work
OmiCLIP is a Track C candidate foundation model that reframes gene expression as *text* (top-gene sentences) so a language/contrastive encoder can consume it — directly relevant to our LLM-as-computational-engine thesis and to representing expression as tokens. Its finding that dedicated single-cell FMs (scGPT, scFoundation, GeneFormer) underperformed a CLIP-style paired encoder on decomposition is a useful caution when picking embeddings. Less directly tied to Track A/B up/down/none perturbation prediction, but the gene-sentence tokenization and cross-modal alignment are transferable ideas.

## Limitations / open questions
- Trained only on Visium (spot-level, ~55µm) H&E pairs; single-cell/subcellular resolution and non-H&E stains are untested.
- Gene-sentence encoding discards quantitative expression magnitude (rank/presence only).
- Downstream tasks reuse existing tools (Tangram, CPD) on the embeddings rather than end-to-end models; PredEx is nearest-neighbor-style, not generative.
- Benchmarks are largely cancer/organ-atlas tissues; generalization to perturbation or dynamic settings is unclear.
