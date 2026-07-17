---
source_url: https://doi.org/10.1038/s41467-025-59926-5
source_type: papers
title: "CellFM: a large-scale foundation model pre-trained on transcriptomics of 100 million human cells"
author: Zeng et al. (senior: Yuedong Yang)
retrieved: 2026-07-16
doi: 10.1038/s41467-025-59926-5
---

# CellFM: a large-scale foundation model pre-trained on transcriptomics of 100 million human cells

**Authors:** Yuansong Zeng, Jiancong Xie, Ningyuan Shangguan, Zhuoyi Wei, Wenbing Li, Yun Su, Shuangyu Yang, Chengyang Zhang, Jinbo Zhang, Nan Fang, Hongyu Zhang, Yutong Lu, Huiying Zhao, Jue Fan, Weijiang Yu, Yuedong Yang
**Year:** 2025
**Venue:** Nature Communications (10.1038/s41467-025-59926-5)

## Abstract
CellFM is a single-cell foundation model with 800M parameters pre-trained on ~100 million human cells — twice the data and 8x the parameters of the largest prior single-species model. To keep training tractable at that scale, it uses ERetNet, a modified RetNet (linear-complexity Transformer variant) implemented in Huawei's MindSpore. As a value-projection model, it recovers embeddings of masked genes from linear projections of their expression values. It reports state-of-the-art results on cell-type annotation, perturbation prediction, gene-function prediction, and gene-gene relationship capture.

## Key contributions
- Curated and standardized ~100M human single-cell transcriptomes (from heterogeneous formats/repositories) into one unified training corpus.
- An 800M-parameter human-only scFM, the largest single-species model at publication; also released an 80M variant.
- ERetNet backbone: RetNet with a gated bilinear (SGLU) feedforward and DeepNorm normalization; Gated MHA cuts attention complexity from O(l²d) to O(l·d²/h). LoRA used for efficient fine-tuning.
- Public code + pre-trained weights.

## Methods
Genes are embedded from expression values, passed through ERetNet layers (Gated MHA + SGLU + LayerNorm) to learn gene-gene relationships and gene embeddings; masked-gene value recovery is the pretraining objective. Trained for 2 epochs (loss drops 8→<1 in epoch 1) on 4 Huawei Atlas800 servers (8 Ascend910 NPUs each). Downstream tasks are evaluated zero-shot or with LoRA fine-tuning; the 80M variant is used for annotation/batch-correction (compute-bound), the 800M for perturbation/gene-function.

## Key results
- Gene function prediction (zero-shot binary): +5.68% and +5.86% average accuracy over next-best UCE and scGPT; on GO multi-class, +1.6%/+1.94% average AUPR over GeneCompass and UCE.
- Perturbation (Adamson + Norman, via GEARS with CellFM embeddings): +1% PCC and +1.45% MSE over next-best scFoundation; +4.75% PCC / +7% MSE over vanilla GEARS.
- Reverse (in-silico CRISPR) perturbation on Norman: 81.8% correct in top-10, 18.1% higher than scGPT.
- Cell annotation (80M): 92.91% avg intra-dataset accuracy, +2.02% over scFoundation; +2.3% on cross-batch; distinguishes exhausted vs activated CD8+ T cells +6.5% over UCE.
- Gene-gene: for 9 perturbation genes, ~18 of top-20 attention-influenced genes matched ChIP-Atlas; recovered IL2/IL3/IL4 immune relationships.

## Why it matters for our work
CellFM is a strong Track-C candidate: a large open-weights human scFM whose gene embeddings and attention maps directly serve perturbation-response prediction — the up/down/none direction task at the heart of Tracks A/B. Its GEARS-plug-in setup (swap gene embeddings into a perturbation head) is a concrete recipe we can borrow. It also anchors the scaling argument (100M cells / 800M params) that our foundation-model comparison in `docs/foundation-models.md` weighs, though the MindSpore/Ascend stack is a portability caveat.

## Limitations / open questions
- Built on Huawei MindSpore + Ascend NPUs; no GRL support and non-trivial to port to PyTorch/GPU.
- Zero-shot 800M underperforms on annotation; gains need fine-tuning (LoRA), and the 80M variant is used where 800M is too costly.
- Perturbation gains over scFoundation are small (~1%); reverse-perturbation compared only to scGPT/GEARS (other scFMs lacked runnable code).
- Only 2 training epochs; scaling/convergence beyond that unexplored.
