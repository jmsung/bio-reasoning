---
source_url: https://doi.org/10.3390/genes16121439
source_type: papers
title: "What Do Single-Cell Models Already Know About Perturbations?"
author: Andreas Bjerregaard et al.
retrieved: 2026-07-16
doi: 10.3390/genes16121439
---

# What Do Single-Cell Models Already Know About Perturbations?

**Authors:** Andreas Bjerregaard, Iñigo Prada-Luengo, Vivek Das, Anders Krogh
**Year:** 2025
**Venue:** Genes (MDPI)

## Abstract
Single-cell generative models learn latent "virtual cell" representations, but how much perturbation knowledge they already encode is unclear. The authors train β-variational autoencoders (β-VAEs) with a negative-binomial output on three scRNA-seq datasets spanning genetic, chemical, and temporal perturbations, then infer perturbations post hoc by differentiating decoder gene outputs with respect to latent variables — yielding vector fields ("perturbation flow maps") of infinitesimal expression change. They also probe a publicly released scVI decoder pretrained on the CELL×GENE Discover Census (~5.7 M mouse cells), scoring genes by alignment between local gradients and an empirical healthy-to-disease axis, with an LLM-based pathway evaluation. The core claim: trained decoders already contain rich perturbation-relevant structure accessible by automatic differentiation, with no perturbation labels or bespoke architectures.

## Key contributions
- A **model-agnostic gradient probe**: differentiate any single-cell decoder's output w.r.t. its latent to turn it into a simulator of infinitesimal perturbations — no supervision, no architecture changes, ~a few lines of code.
- Extension to **arbitrary perturbation types** (treatment, dosage, developmental time) via lightweight auxiliary output heads trained on as little as 10% of labels.
- A **label-free alignment score** ranking decoder outputs by cosine similarity between their gradient field and an observed perturbation axis (Eq. 3–5).
- An **LLM-in-the-loop pathway evaluation** (GPT-5-mini, reasoning + web search, triple-run + adjudication) to judge disease relevance of enriched gene sets.

## Methods
β-VAEs with a negative-binomial decoder (encoder 512→256, latent dim 32 or 2; β annealed toward ~0, i.e. near-autoencoder) are trained per dataset on UMI counts of highly variable genes. Perturbation is simulated by stepping the latent along the gradient of a chosen gene output, z_{t+1} = z_t + δ∇y_i(z_t); negative δ = knockdown, positive = overexpression. Gradients are sampled across latent space and projected via PCA or UMAP for visualization. Genes are scored by average cosine alignment between their gradient and the mean healthy→disease latent displacement; the top 200 by |score| feed WebGestalt overrepresentation analysis against WikiPathways.

## Key results
- **Irf8 knockout (genetic):** negative Irf8 gradients move wild-type microglia and CP-BAM populations toward the knockout population, recovering known Irf8 microglial-identity biology.
- **Cardiotoxin muscle injury (chemical):** a binary treatment head trained on only 10% of labels reaches **99.0% held-out accuracy**; gradient flows point strictly from control to injured states.
- **C. elegans embryogenesis (temporal):** a time-regression head on 10% of labels yields gradients aligned with observed embryo age while preserving cell-type subclusters.
- **Pretrained scVI Census (zero-shot):** with no finetuning or perturbation labels, gradient flows on 10,000 islet cells reproduce T2D-consistent directions — Ins1/Pcsk1 in β-cells point diabetic→normal, Gcg/Pcsk2 in α-cells point normal→diabetic.
- Gradient-based enrichment found multiple significant WikiPathways (FDR ≤ 0.05) where an average-expression baseline found **none**, and its pathways scored higher for T2D relevance under the LLM assessment.

## Why it matters for our work
This paper is direct evidence for the BioReasoning premise that pretrained single-cell foundation models (Track C) already encode perturbation-response structure that can be read out without task-specific training. The gradient direction (positive vs. negative δ, or diabetic↔normal alignment) maps onto our Track A/B **up / down / none** direction prediction: a decoder gradient's sign against a disease or perturbation axis is a candidate label-free signal for whether a gene moves expression up or down. The LLM-in-the-loop pathway adjudication also mirrors our agentic-scoring approach and suggests a reusable pattern for grounding gene/pathway rankings.

## Limitations / open questions
- Gradients are **infinitesimal and local** (first-order) — they simulate small steps, not large finite perturbations or combinatorial effects.
- Auxiliary heads still require some labeled data, and results are validated qualitatively (flow-map inspection, LLM judgment) rather than by held-out quantitative perturbation-prediction benchmarks.
- The alignment score depends on the chosen evaluation set Z and a mean-displacement axis; optimal-transport or gradient-magnitude weighting are proposed but untested.
- Small VAEs on three datasets; scale/generalization of the probe across model families and larger perturbation atlases remains open.
