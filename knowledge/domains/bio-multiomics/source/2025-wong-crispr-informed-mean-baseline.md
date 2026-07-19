---
source_url: https://doi.org/10.1093/bioinformatics/btaf317
source_type: papers
title: "Simple controls exceed best deep learning algorithms and reveal foundation model effectiveness for predicting genetic perturbations"
author: Wong et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btaf317
---

# Simple controls exceed best deep learning algorithms and reveal foundation model effectiveness for predicting genetic perturbations

**Authors:** Daniel R Wong, Abby S Hill, Rob Moccia (Pfizer Worldwide R&D, Machine Learning and Computational Sciences)
**Year:** 2025
**Venue:** Bioinformatics (10.1093/bioinformatics/btaf317)

## Abstract
Predicting the post-perturbation transcriptome is a central pharmaceutical
task, and transformer foundation models emerged as the presumed gold standard.
Wong et al. show that a trivial statistical baseline — the "CRISPR-informed
mean" — matches or beats both SOTA deep learning methods (GEARS and scGPT) and
other simple neural baselines across three Perturb-seq datasets. Through
weight- and architecture-ablation controls they further show that neither the
pre-trained foundation weights nor the transformer self-attention give scGPT any
measurable advantage on this task. They also release a corrected version of the
widely-used GEARS Adamson dataset (mislabeled control cells) and argue for
mandatory statistical controls in perturbation-prediction benchmarks.

## Key contributions
- A **CRISPR-informed mean** baseline: predict the training-set mean expression per gene, but set the target gene to 0 (CRISPRi) or 2× mean (CRISPRa).
- Three generalizable "controls" for any transformer foundation model: withhold foundation weights before fine-tuning, strip the transformer block, remove self-attention.
- A **Corrected Adamson dataset** fixing perturbed cells mislabeled as controls in the GEARS release (from GEO GSE90546).

## Methods
Evaluated on GEARS Adamson (Corrected Adamson UPR), Norman, and Replogle K562
Essential Perturb-seq datasets (all K562; Adamson/Replogle CRISPRi single-target,
Norman CRISPRa multi-target), with disjoint train/val/test perturbation splits.
Metrics were the four Pearson variants from GEARS/scGPT — Pearson, Pearson DE
(top-20 DE genes), Pearson Delta (PD), Pearson DE Delta (PDED) — plus Wu et al.'s
rank metric. Ten independently trained models per method (n=30 across three
datasets); GEARS and scGPT trained with authors' default hyperparameters on an
H100. Ablations selectively loaded/withheld scGPT's Human-CP foundation weights,
and a transformer-free "Simple Affine" clone isolated the attention contribution.

## Key results
- For **PD**, the plain mean model beat GEARS (Δmean=0.07, p=0.01) and scGPT (Δmean=0.10, p=1.6e-4) on all three datasets.
- The **CRISPR-informed mean** beat GEARS (PD Δ=0.08, p=9.3e-4) and scGPT (PD Δ=0.11, p=8.1e-6) on all datasets, and beat all three Wu et al. neural baselines.
- On the **rank** metric it was 4.7–213.9× better than GEARS and 3.9–155.4× better than scGPT.
- **No pre-training benefit:** fully fine-tuned scGPT vs random-init scGPT differed by only PD Δ=0.004 (p=0.89), PDED Δ=0.01 (p=0.75).
- **No attention benefit:** withholding the transformer block gave PD Δ=0.006 (p=0.80); the transformer-free Simple Affine matched scGPT (PD Δ=0.02, p=0.49) while training ~19–20× faster and being ~1.6× smaller.

## Why it matters for our work
This is the strongest cautionary paper for BioReasoning Track A/B up/down/none
prediction: it demonstrates that on standard Perturb-seq benchmarks a
biologically-informed mean beats SOTA foundation models, because CRISPR
perturbations induce subtle, near-identical transcriptome shifts (high Pearson
between target=T and target≠T cells) — so a strong statistical baseline is hard
to beat and mandatory as a control. For Track C foundation-model bets, the
weight- and attention-ablation controls give us a ready recipe to test whether a
model's pre-training actually transfers, rather than trusting leaderboard deltas.
It reinforces our own finding (Track B LB 0.488) that small CV and headline
metrics mislead: always benchmark against a CRISPR-informed mean first.

## Limitations / open questions
- CRISPR-informed mean needs a known target and dataset-specific means — useless in zero-shot, unknown-target, or small-molecule drug-discovery settings; it cannot model gene-gene interactions.
- Restricted to K562 CRISPRi/CRISPRa Perturb-seq; generalization to other cell lines/organisms/modalities untested.
- Authors note Perturb-seq may simply lack the data scale for transformers to shine — a data-size, not architecture, ceiling.
- Current Pearson/MSE metrics may not capture downstream pharmaceutical usefulness; better biologically-grounded metrics remain open.
