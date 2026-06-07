---
source_url: https://genentech.github.io/BioReasoningChallenge/
source_type: web
title: BioReasoning Challenge 2026
author: Genentech BioReasoning Challenge organizers
retrieved: 2026-06-06
---

# BioReasoning Challenge 2026

**Source:** genentech.github.io · 2026-06-06
**Authors:** Carl Edwards, Ehsan Hajiramezanali, Takamasa Kudo, Jack Kamm,
Hugues Van Assel, Xiner Li, Edward De Brouwer, Jan-Christian Hütter,
Gabriele Scalia, Sara Mostafavi (Genentech); Romain Lopez (NYU);
Aviv Regev (Genentech EVP). Contact: edwards.carl@gene.com.

## TL;DR

Can LLMs and agentic systems predict cellular perturbation outcomes?
Given a knocked-down gene X, predict whether target gene Y goes up,
down, or unchanged in primary mouse bone marrow-derived macrophages
(BMDMs) post-LPS stimulation. Three tracks compare prompt-only (A),
agentic tool-use (B), and fine-tuning (C) paradigms — all using
GPT-OSS-120B or open models <10B.

## Key claims

- Perturb-seq predictions are a meaningful benchmark for "biological
  reasoning": combining knowledge + causal intuition + structured inference.
- Three distinct AI paradigms are tested independently per track —
  identical task, divergent constraint set.
- Evaluation uses micro AUROC averaged across two sub-tasks: (1)
  differential expression detection, (2) direction of change.
- Top-5 manual expert review prevents metric hacking.

## Data

- **Cell type:** primary mouse BMDMs from Cas9-transgenic mice
- **Perturbation:** pooled CRISPR knockout library targeting inflammatory
  signaling + macrophage-relevant genes; 4 guides pooled per gene
- **Trigger:** bacterial LPS stimulation, sc-RNA-seq at 9h post
- **Scope:** 482 perturbations × 2,206 target genes
- **Splits:** 386/48/48 perturbations · 1,570/331/305 target genes (train/val/test)
- **DEG definition:** FDR < 0.05 AND |shrunken log₂FC| ≥ log₂(1.5);
  perturbations with <9 DEGs excluded. Median 193 DEGs per true perturbation.
- **Allowed augmentation:** public datasets PerturbQA, Tahoe-100M
  (permissively licensed perturbation data)

## Tracks

| | Track A — Prompt | Track B — Agentic | Track C — Fine-tune |
|---|---|---|---|
| Model | GPT-OSS-120B fixed | GPT-OSS-120B fixed | open <10B params |
| Tools | none | up to 100 tools, 250 calls | none |
| Tokens | 4,096 prompt | 16,384 prompt | n/a |
| Samples | 3 per question (seeds 42, 43, 44) | — | — |
| Fine-tuning | forbidden | forbidden | any technique (SFT, LoRA, RL) |
| Web/external LLMs at inference | no | no | no |
| Traces required | — | yes (auditability) | — |

All tracks: temperature = 1.0, top_p = 1.0 enforced; prompts cannot reveal
expected outputs.

## Submission

1. Text file with test predictions (continuous probability OR binary)
2. Metadata: reasoning traces, token usage, tool usage, model info
3. Task inputs: tool definitions (Track B) or prompt files

Public leaderboard on a public test subset; final ranking from private
test. Top-5 solutions undergo manual expert review.

## Prizes

- Per-track: $350 / $150 / $100 (1st / 2nd / 3rd)
- Most novel submission: $200
- Co-authorship invitation on the resulting manuscript for top teams.

## Open questions

- Exact deadline dates — not on the overview page; check Kaggle competitions.
- Kaggle-specific leaderboard scoring details and submission file format
  schema — fetch from the Kaggle competition pages separately.
- Whether Tahoe-100M counts against any token/data budget in Track A.
