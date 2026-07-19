---
source_url: https://doi.org/10.64898/2026.01.09.698608
source_type: papers
title: "STACK: In-Context Learning of Single-Cell Biology"
author: Dong et al.
retrieved: 2026-07-16
doi: 10.64898/2026.01.09.698608
---

# STACK: In-Context Learning of Single-Cell Biology

**Authors:** Mingze Dong, Abhinav Adduri, Dhruv Gautam, Christopher Carpenter, Rohan Shah, Chiara Ricci-Tam, Yuval Kluger, Dave P. Burke, Yusuf H. Roohani (Arc Institute; Yale; UC Berkeley; UPenn)
**Year:** 2026
**Venue:** bioRxiv preprint — doi:10.64898/2026.01.09.698608

## Abstract
STACK is a single-cell foundation model that, unlike prior models that embed each
cell independently, uses tabular attention over a *cell set* so each cell's
representation is informed by its context (the other cells in its sample). It is
pre-trained self-supervised on 149M uniformly preprocessed human cells (from
scBaseCount's 189M) with a masked-gene reconstruction objective, then post-trained
to do in-context learning (ICL): given a *prompt* population encoding a condition
(a perturbation, donor, disease) and a *query* population specifying a cell type,
it predicts the query's counterfactual expression under that condition — with no
task-specific fine-tuning. STACK improves zero-shot classification, integration,
and perturbation-effect prediction over zero-shot, fine-tuned, and
trained-from-scratch baselines, and is used to build PerturbSapiens, a virtual
whole-organism perturbed-cell atlas (28 tissues, 40 cell classes, 201 perturbations).

## Key contributions
- Context-aware "tabular transformer" block with both intra-cellular and inter-cellular multi-head attention over a cell set (inspired by TabPFN/TabICL).
- Trainable gene-module tokenization (100 tokens/cell), a first for scFMs; a rectangular-mask objective + Sliced-Wasserstein latent regularization enforcing linear identifiability.
- A self-distillation (EMA teacher) post-training recipe that turns the model into a conditional generative model for label-free "cell prompting" / ICL.
- PerturbSapiens, the first human whole-organism virtual atlas of perturbed cells.

## Methods
Pre-training reconstructs masked genes (mask ratio U(0.1,0.8)) over K=256-cell sets
via a negative-binomial decoder (scVI-style), with cells embedded as 100 gene-module
tokens. Post-training partitions each sample into prompt vs. target cells, replaces
targets with type-matched query cells from a different donor/condition, and trains
the student to reconstruct held-out targets — analogous to masked diffusion.
Generation is iterative, confidence-guided by an MLP classifier. Trained on a single
H100 in 2–3 days via a fast h5py dataloader (~1.6×10⁴ cells/s, >75× a comparable model).

## Key results
- STACK's zero-shot ICL ranks first in **28 of 31** perturbation/generation evaluations against strong baselines (State, DonorMean/scVI, closest-cell-type).
- On perturbation classification it is the only method to consistently beat scVI-trained-from-scratch, roughly **+100%** over the best alternative on Tahoe and Parse.
- Top scIB integration performer on all 4 observational datasets (+1.8% over State-SE); best in 21/25 Tabula Sapiens tissues — batch integration is emergent, not trained.
- Outperforms State across all evaluated perturbation metrics despite State training on both prompt and query data (State needs orders-of-magnitude more supervision).
- Generated IFN-γ, type-I-IFN, IL-13, IL-1β responses validated against independent in vitro epithelial stimulation datasets with cell-type specificity.

## Why it matters for our work
Directly relevant to **Track C foundation-model selection** and to Track A/B
perturbation prediction. STACK is concrete 2026 evidence that a well-designed scFM
*can* finally beat trained-from-scratch baselines (which prior FMs failed to —
cf. Kedzierska, Csendes) and can predict perturbation up/down effects zero-shot in
low-data, cross-experiment settings — exactly the regime where our agentic pipelines
operate. Its "cell prompting" (label-free counterfactual prediction from unlabeled
context) is a modeling paradigm worth watching for Track B direction prediction, and
PerturbSapiens is a candidate reference resource for perturbation-response priors.

## Limitations / open questions
- Human-only; multi-species use needs new tokenization for gene misalignment.
- Calibration for rare cell types and weak perturbation effects is unestablished (needs confidence filtering to work well).
- Secondary/time-dependent signaling (e.g. TNF-α) can flip predicted direction vs. in vitro ground truth, complicating interpretation.
- Post-trained mostly on in vivo immune cells — generalization to in vitro / non-immune lineages is uneven; open-weights/code availability not stated in text.
