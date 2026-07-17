---
source_url: https://doi.org/10.1101/2024.12.04.626878
source_type: papers
title: "Modeling and predicting single-cell multi-gene perturbation responses with scLAMBDA"
author: Gefei Wang et al.
retrieved: 2026-07-16
doi: 10.1101/2024.12.04.626878
---

# Modeling and predicting single-cell multi-gene perturbation responses with scLAMBDA

**Authors:** Gefei Wang, Tianyu Liu, Jia Zhao, Youshu Cheng, Hongyu Zhao (Yale University)
**Year:** 2024
**Venue:** bioRxiv (preprint)

## Abstract
scLAMBDA is a deep generative framework that models and predicts single-cell transcriptional responses to genetic perturbations — both single-gene and combinatorial multi-gene — from CRISPR Perturb-seq data. It leverages gene embeddings from large language models (default: GenePT) to inject prior biological knowledge, and disentangles a basal cell state from a perturbation-specific "salient" representation. Across multiple Perturb-seq datasets it consistently beat state-of-the-art methods (GEARS, scGPT, GenePert) on prediction accuracy, generalized to unseen target genes and perturbations, and captured both mean expression shifts and single-cell heterogeneity — enabling downstream DE analysis and genetic-interaction exploration.

## Key contributions
- A VAE-based generative model that predicts post-perturbation expression for *novel/unseen* genes by conditioning on LLM-derived gene-name embeddings (`p`), removing GEARS' GO-graph and scGPT's measured-expression requirements.
- Disentanglement of basal state `z` from salient perturbation representation `s = E_perturb(p)` by minimizing mutual information via MINE.
- Adversarial training on perturbation embeddings (FGSM-style, ε = 0.001‖p‖) to prevent overfitting in the sparse, high-dimensional perturbation space and improve generalization.
- Two-gene perturbations handled by summing single-gene embeddings (p_ab = p_a + p_b); nonlinear decoder avoids the linear-model bias that affects GenePert.

## Methods
Each cell's expression `x ∈ R^g` is generated from a standard-normal basal latent `z` plus salient `s`, decoded jointly. Training optimizes an ELBO plus the MINE mutual-information penalty (λ_MI = 200) and adversarial augmentation of `p`. Trained on the top 5,000 highly variable genes, latent dim d = 30, batch 500, 200 epochs, Adam (lr 0.0005). Evaluation used Pearson correlation (PCC) of mean expression change and 2-Wasserstein distance (W2) of predicted vs. true cell distributions, with GEARS-style splits (75/25 train/test perturbations). Benchmarked against GEARS, scGPT, and GenePert.

## Key results
- **Adamson CRISPRi (K562, 86 genes):** scLAMBDA PCC = 0.786 (vs GenePert 0.775, GEARS 0.692, scGPT 0.661) and lowest W2 = 22.552; STT3A-knockdown DE detection AUC 0.969 (up) / 0.996 (down).
- **Replogle genome-scale CRISPRi (RPE1, 2,393 genes):** highest PCC = 0.564 (GenePert 0.547) and lowest W2 = 28.737 (scGPT 29.487).
- **Norman CRISPRa (K562, 104 single + 130 two-gene):** highest overall PCC = 0.664 (GenePert 0.635), lowest W2 = 13.228; two-gene PCC rose 0.593 → 0.718 → 0.850 as 0/1/2 target genes were seen in training.
- Basal representation captured cell-cycle phase; salient representation clustered transcriptionally similar perturbations more tightly than raw GenePT embeddings.
- GenePT and scGPT embeddings worked best; genome-sequence models (HyenaDNA, DNABERT-2) were suboptimal, and ablations confirmed MI regularization + adversarial training both help. Training was faster than all deep baselines (slower only than the ridge-regression GenePert).

## Why it matters for our work
scLAMBDA is directly on-topic for the BioReasoning perturbation-prediction tracks (Track A/B up/down/none direction prediction). Its central finding — that LLM-derived *gene-name* embeddings (GenePT) drive strong generalization to unseen genes, while genome-sequence foundation-model embeddings underperform — is a concrete signal for our Track C foundation-model choice and our gene-embedding-direction work. The salient/basal disentanglement and the two-gene = sum-of-embeddings trick are reusable design patterns for combinatorial prediction, and the paper reconfirms that simple linear baselines (GenePert) are hard to beat on mean-change PCC.

## Limitations / open questions
- Preprint (not peer-reviewed); benchmarks limited to three Perturb-seq datasets, all K562/RPE1.
- Performance is bounded by gene-embedding quality — a weak embedding degrades predictions.
- Two-gene combinatorial accuracy still depends heavily on how many constituent genes were seen in training.
- Only genetic (CRISPRi/a) perturbations shown; extension to chemical perturbations is future work.
