<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: "CisTransCell: Single-Cell Perturbation Prediction via Gene Function, Regulatory Control, and Cellular Context"
authors: [Wei Zhang et al.]
year: 2026
doi: 10.48550/arXiv.2606.13713
source_url: https://arxiv.org/abs/2606.13713
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# CisTransCell: Single-Cell Perturbation Prediction via Gene Function, Regulatory Control, and Cellular Context

**Authors:** Wei Zhang, Xun Jiang, Yuesi Xi, Ming Tang
**Year:** 2026
**Venue:** arXiv preprint (arXiv:2606.13713, q-bio.GN), submitted June 2026

## Abstract
CisTransCell predicts how single cells respond transcriptionally to genetic perturbations, with a focus on the zero-shot setting (perturbing genes unseen at training time). The central claim is that perturbation effects are not determined by a gene's expression state alone: they depend on the gene's regulatory interactions and on the cellular programs currently active in the target cell. The method augments each gene with two complementary priors — a coding-sequence prior (what the gene product does) and a cis-regulatory-sequence prior (how the gene is itself controlled) — and conditions the prediction on the current cell's expression state. This casts a perturbation as a cascade: gene function → regulatory control → downstream transcriptional change.

## Key contributions
- A cell-conditioned framework that decomposes perturbation prediction into three explicit axes: gene function, regulatory (cis/trans) control, and cellular context.
- Two sequence-derived priors per gene — a coding-sequence prior for product function and a cis-regulatory prior for how the gene is controlled — enabling generalization to genes never perturbed during training.
- A cascade formulation modeling perturbation response as function → regulation → transcriptomic output, rather than a flat expression-to-expression map.
- Reported strong zero-shot perturbation-prediction performance on benchmark single-cell datasets.

## Methods
Each gene is represented by (1) a coding-sequence prior encoding what the gene product does and (2) a cis-regulatory-sequence prior encoding how the gene is regulated. These sequence-derived priors are the mechanism for zero-shot transfer: an unseen perturbation gene still has coding and regulatory sequence, so it can be embedded and reasoned over without training-set expression history. The model then conditions on the target cell's current expression state (cellular context) so the same perturbation can yield different responses across cell states / active programs. Trans effects propagate through the regulatory structure to produce the predicted downstream transcriptional shift. (Exact encoder architectures and the context-integration mechanism are not fully legible in the released PDF; baselines named for comparison include GEARS, scGPT, scFoundation, and CPA.)

## Key results
- Reported to achieve strong zero-shot perturbation prediction on benchmark single-cell perturbation datasets, positioned against GEARS, scGPT, scFoundation, and CPA.
- Precise magnitudes (Pearson / MSE / accuracy) were not extractable from the released PDF; treat quantitative claims as unverified pending a clean read of the results tables.

## Why it matters for our work
Our task is to predict, for a (perturbation gene, target gene) pair under macrophage CRISPRi, whether the target goes up / down / none. CisTransCell's decomposition maps almost directly onto our two reasoning tracks:

- **Track B (mechanism / network reasoning):** its function → cis-regulation → trans-propagation cascade is exactly the causal chain we want an agent to reason over. The cis vs. trans split gives a principled scaffold — the perturbed gene's product function and its regulatory position determine which target edges fire — which we can lift into explicit mechanism prompts / graph edges for direction (up vs. down) calls.
- **Track C (architecture candidate):** the sequence-derived priors (coding + cis-regulatory) are a concrete way to embed genes for zero-shot generalization to perturbations not in the CRISPRi training screen — the core zero-shot requirement of the challenge. The cell-conditioning is directly relevant since we operate in a single fixed context (macrophage); we'd fix the context prior rather than vary it, and lean on the regulatory prior for target-specific direction.

Concretely: for each (pert, target) pair we can ask whether a regulatory (cis→trans) path exists and its sign, which is the up/down/none decision. CisTransCell is a candidate to adapt or benchmark against for Track C, and its cis/trans framing is a ready-made mechanism vocabulary for Track B.

## Limitations / open questions
- No limitations section was legible in the released PDF; the following are inferred.
- Assumes usable coding- and cis-regulatory-sequence priors exist for every perturbed gene — quality of these priors bounds zero-shot accuracy.
- Reported gains are qualitative here; exact metrics, datasets, and per-baseline deltas need verification from a clean read of the tables before we cite numbers.
- Unclear how well cell-conditioning transfers to a narrow, single-cell-type CRISPRi context (macrophage) versus the multi-context benchmarks it was likely trained on.
- Architecture specifics (encoders, how context is fused, trans-propagation mechanism) are not confirmed — blocks direct reimplementation without the source or a cleaner PDF.
