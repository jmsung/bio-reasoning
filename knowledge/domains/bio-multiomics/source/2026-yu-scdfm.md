<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: "scDFM: Distributional Flow Matching Model for Robust Single-Cell Perturbation Prediction"
authors: [Yu et al.]
year: 2026
doi: 10.48550/arXiv.2602.07103
source_url: https://arxiv.org/abs/2602.07103
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# scDFM: Distributional Flow Matching Model for Robust Single-Cell Perturbation Prediction

**Authors:** Chenglei Yu, Chuanrui Wang, Bangyan Liao, Tailin Wu
**Year:** 2026
**Venue:** ICLR 2026 (poster) · arXiv:2602.07103

## Abstract
scDFM predicts single-cell transcriptional responses to perturbations. Its motivating premise is that single-cell measurements are noisy and sparse, and that perturbations induce *population-level* shifts rather than deterministic changes in individual cells — so there is no natural one-to-one correspondence between a control cell and "its" perturbed counterpart. Instead of regressing a mean response, scDFM uses conditional flow matching to learn the full distribution of perturbed-cell states conditioned on control states, aligning the two populations with a maximum mean discrepancy (MMD) objective. A Perturbation-Aware Differential (PAD) Transformer backbone injects gene-interaction-graph structure and differential attention. The model outperforms strong baselines across genetic and drug perturbation benchmarks and generalizes to unseen and combinatorial perturbations.

## Key contributions
- **Distributional (not point) prediction:** models the entire conditional distribution of perturbed cells via conditional flow matching, avoiding the flawed assumption of paired control↔perturbed cells.
- **Population-level alignment:** an MMD objective matches perturbed and control populations at the distribution level rather than per cell.
- **PAD-Transformer backbone:** a Perturbation-Aware Differential Transformer that uses gene interaction graphs and differential attention to capture context-specific expression changes.

## Methods
The core idea is conditional flow matching: a continuous-time generative flow is trained to transport samples from the control-state distribution to the perturbed-state distribution conditioned on the applied perturbation. Because it learns a distribution rather than a mean, it captures the spread, multimodality, and population shift a perturbation produces — not just the average effect. An MMD term provides a distribution-level alignment signal (kernel two-sample discrepancy between predicted and true perturbed populations). The PAD-Transformer conditions predictions on gene-gene interaction structure and uses differential attention to emphasize genes that actually change under perturbation.

## Key results
- Consistently outperforms the strongest baselines across genetic and drug perturbation benchmarks.
- **19.6% relative MSE reduction** vs. the strongest baseline in combinatorial (multi-perturbation) settings.
- Generalizes to unseen and combinatorial perturbations.

(Note: the abstract does not enumerate the specific benchmark datasets or report distributional metrics beyond MSE; consult the full PDF for the complete evaluation table.)

## Why it matters for our work
Our task is to predict, for a (perturbation gene, target gene) pair under macrophage CRISPRi, whether the target goes up / down / none — a directional, effectively population-level readout. scDFM's central claim is directly relevant: a perturbation shifts the *population* of cells, and point-loss / mean-regression models (which most Track C baselines resemble) systematically miss the shape and magnitude of that shift when the response is heterogeneous or multimodal. If macrophage CRISPRi responses are noisy and only a subpopulation of cells responds, a mean predictor can wash out a real up/down effect toward "none." Modeling the full response distribution (or at least distributional summaries) is a plausible reason simple mean-based predictors underperform, and the MMD-alignment idea offers a concrete, borrowable training signal even if we don't adopt full flow matching. Track C relevance: an open-weights or from-scratch model that predicts distributional shift, then thresholds it into up/down/none, is a candidate architecture.

## Limitations / open questions
- The abstract does not disclose benchmark identifiers, ablations, or distributional evaluation metrics — need the full paper to assess rigor.
- Flow-matching + MMD adds training and sampling cost vs. a single-forward-pass mean regressor; unclear how it scales to genome-wide perturbation screens.
- Unclear whether the method was tested on CRISPRi in immune/macrophage contexts specifically, or how well the distribution→directional-label reduction our task needs works in practice.
- Generalization is claimed for "unseen and combinatorial" perturbations, but the strength of unseen-*gene* (not just unseen-combination) generalization — the hardest case for our task — is not established from the abstract alone.
