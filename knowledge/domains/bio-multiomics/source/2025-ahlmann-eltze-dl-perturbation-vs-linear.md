<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines
authors: [Ahlmann-Eltze et al.]
year: 2025
doi: 10.1038/s41592-025-02772-6
source_url: https://www.nature.com/articles/s41592-025-02772-6
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Deep-learning-based gene perturbation effect prediction does not yet outperform simple linear baselines

**Authors:** Constantin Ahlmann-Eltze, Wolfgang Huber, Simon Anders
**Year:** 2025
**Venue:** Nature Methods (Vol. 22, Issue 8) — DOI: 10.1038/s41592-025-02772-6

## Abstract
The authors ask whether deep-learning (DL) foundation models pretrained on large single-cell transcriptomics corpora can predict the transcriptional effects of genetic perturbations better than deliberately simplistic baselines. Across four CRISPR perturbation datasets, no tested DL or foundation model outperformed simple linear / additive baselines — often at a fraction of the compute cost. The paper is a benchmarking cautionary tale: it argues that current single-cell representations do not yet capture the cell-state dependencies needed for perturbation prediction, and that rigorous baseline comparison is essential before claiming DL superiority.

## Key contributions
- Head-to-head benchmark of 5 foundation models (scGPT, scFoundation, scBERT, Geneformer, UCE) + 2 specialized DL models (GEARS, CPA) against simple linear baselines.
- Shows simple baselines match or beat all DL/FM models on both single (unseen) and double perturbations.
- Documents large GPU/memory cost of DL models for zero performance gain (Extended Data Fig. 10).
- Adds to the 2024–2025 consensus that simple baselines are surprisingly strong for perturbation prediction.

## Methods
- **DL/FM models:** scGPT, scFoundation, scBERT, Geneformer, UCE (foundation); GEARS, CPA (specialized).
- **Linear baselines:** "no change" (predict control), "additive" (sum of single log-fold-changes for doubles), a linear regression on gene/perturbation embeddings, and a "mean" (training-average) baseline.
- **Datasets:** Norman et al. (100 single + 124 double CRISPRa in K562, 19,264 genes); Replogle et al. (two CRISPRi datasets, K562 + RPE1); Adamson et al. (multiplexed CRISPR, K562). Predominantly cancer cell lines.
- **Splits:** Doubles — train on 100 singles + 62/124 doubles, test on remaining 62 (5 random splits). Singles — predict effects of completely unseen perturbation genes (two train/test splits per dataset).
- **Metrics:** L₂ distance on top-1,000 expressed genes; Pearson-delta (fold-change) correlation; TPR vs. false-discovery proportion for genetic interactions.

## Key results
- **Doubles:** All models had prediction error substantially higher than the simple additive baseline. No DL model beat the "no change" baseline at detecting genetic interactions; models predicted mostly buffering interactions and almost never correctly predicted synergy (repeated false HBG2/HBZ hemoglobin-pair calls).
- **Singles / unseen perturbations:** None of the DL models consistently outperformed the mean prediction or the linear model. A linear model using scFoundation/scGPT gene embeddings matched or beat those models' own decoders. Best overall was a linear model with perturbation embeddings pretrained on a related cell line.
- **Cost:** DL models required large GPU time/memory for no accuracy gain.

## Why it matters for our work
This is a MUST-READ baseline-caution paper. Our task predicts, for a (perturbation gene, target gene) pair, whether the target goes up / down / none — in macrophage CRISPRi, evaluated on a **zero-overlap split** where test perturbations are unseen. That is exactly this paper's *hardest* setting (single, unseen perturbations), where **no DL/FM model beat the mean or a linear model**. Two direct implications:
- **Set the bar with a linear/majority baseline first.** With `none` at ~55% majority, a trivial "predict none" model already scores high; our LLM/agent reasoning (Track A/B) and any fine-tune (Track C) must clearly clear a linear + majority baseline before the effort is justified. Do not report DL/FM numbers without this comparison.
- **Foundation-model embeddings are not a free win.** Pretrained scGPT/scFoundation embeddings did not translate to better perturbation prediction than a linear readout on unseen genes — temper expectations for Track C fine-tuning and treat FM features as one input to test, not a guaranteed uplift.

## Limitations / open questions
- Only four datasets, mostly cancer cell lines — generalization to macrophages / primary / in-vivo cells untested (directly relevant to our macrophage setting).
- No exclusion of failed perturbations (guides that didn't move the target); QC could shift results.
- Transcriptomics-only; may not generalize to other modalities.
- Models run largely at default parameters (though original authors were consulted).
- Open: why do FMs pretrained on millions of cells fail to capture cell-state dependence for perturbation effects, and can curation/QC close the gap?
