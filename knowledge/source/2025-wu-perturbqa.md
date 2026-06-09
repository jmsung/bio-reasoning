---
source_url: https://arxiv.org/abs/2502.21290
source_type: papers
title: "PerturbQA: Contextualizing biological perturbation experiments through language"
author: Wu et al. (Genentech)
retrieved: 2026-06-08
---

# Contextualizing biological perturbation experiments through language (PerturbQA + SUMMER)

**Authors:** Menghua Wu, Russell Littman, Jacob Levine, Lin Qiu, Tommaso
Biancalani, David Richmond, Jan-Christian Huetter
**Year:** 2025
**Venue:** ICLR 2025

## Abstract

LLMs as a medium for representing biological relationships and rationalizing
perturbation outcomes. Introduces PerturbQA — a benchmark for structured
reasoning over perturbation experiments framed as language — and SUMMER, a
domain-informed LLM framework that matches or exceeds SOTA.

## Key contributions

- **PerturbQA benchmark**, framed as language tasks over perturbation experiments.
- **Three tasks:** (1) differential-expression prediction for *unseen*
  perturbations, (2) direction of change (up/down), (3) gene-set enrichment.
- **Format:** (cell type, perturbation, gene) -> {up, down, unperturbed},
  built from 5 CRISPRi scRNA-seq datasets.
- **SUMMER** (SUMMarize, retrievE, answeR): simple domain-informed LLM pipeline.
- Finding: existing ML (e.g. GEARS) and naive LLM prompting perform poorly.

## Methods

SUMMER summarizes biological knowledge about the genes, retrieves related
context, then answers the up/down/none question — an LLM pipeline grounded in
domain knowledge rather than end-to-end black box.

## Key results

- Current ML/statistical methods and naive LLM prompting perform poorly on PerturbQA.
- SUMMER matches or exceeds SOTA. (specific metrics not captured — see full text)

## Why it matters for our work

**This is the blueprint.** PerturbQA's task is essentially identical to
BioReasoning Track A/B (pert, gene -> up/down/none), and several authors are at
Genentech, which runs this challenge. SUMMER's summarize -> retrieve -> answer
recipe is a directly applicable Track A/B strategy, and the headline lesson —
*naive prompting fails; domain-grounded retrieval + reasoning wins* — is a strong
prior for our approach design (roadmap #5/#7). Connects to our EDA, which also
found direction (up/down) more learnable than the DE-vs-none split ([[track-a-eda]]).

## Limitations / open questions

- Specific metrics and the 5 source datasets not captured here — read full text.
- SUMMER retrieves external biological knowledge — which sources, and are they
  allowed under Track A "prompt-only" rules? (verify vs docs/kaggle-rules.md)
- Does our macrophage dataset overlap with PerturbQA's 5 datasets? (possible
  shared signal or leakage to check)
