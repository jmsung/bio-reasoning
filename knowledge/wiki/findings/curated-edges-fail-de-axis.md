---
title: Curated-edge databases are too sparse/weak to crack the DE axis — go model-based
status: draft
cites:
  - findings/direction-transfers-de-doesnt.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/competitor-landscape.md
  - findings/track-a-eda.md
  - findings/track-b-abstention-failure.md
  - source/2026-bioreasoning-challenge-overview.md
---

# Curated-edge databases are too sparse/weak to crack the DE axis — go model-based

[[../home]] | [[../index]]

**Status: draft — from the `feat/de-detector` branch investigation, 2026-07-16.
Three curated-network DE channels measured on the dual-OOD val split; all too weak.**

Bottom line: the Track A rank-1 bottleneck is **DE detection** (AUROC_de ~0.55,
near chance) while **direction is fine** (~0.58; [[track-a-eda]]). The intuitive
fix — a curated regulatory/interaction edge as a DE feature — **does not work for
this task**, because the competition asks about *arbitrary* (pert, gene) pairs and
curated databases only store a tiny, high-confidence slice of pairs. Direct-edge
membership lands at ~1–2% coverage, and even a graded network-proximity score
barely beats chance. **The DE axis needs a model-based channel (per-answer
log-probabilities, or neighbor-retrieval of labeled train pairs), not a lookup.**

## What we measured (OOD-val, seed 0, 1276 rows)

| Channel | Coverage | DE signal | Verdict |
|---|---|---|---|
| **CollecTRI** signed mouse TF-regulon (43,226 edges, 1,165 TFs; `decoupler.op.collectri`) | 12% of rows have a TF pert; **0.4%** are direct edges | n/a (too sparse to score) | killed by coverage gate |
| **STRING** 1-hop direct edges (taxid 10090, `interaction_partners`) | 100% of perts have partners; **1.6%** of pairs are direct edges (2.7% on DE-pos) | n/a | killed by coverage gate |
| **STRING** 2-hop shared-neighbor proximity | **38.9%** (42% on DE-pos) | **DE-AUROC 0.534** overall / **0.543** on covered rows | killed by signal gate (< 0.55) |

The 2-hop proximity did show a faint separation (mean proximity 2.50 for
DE-positive pairs vs 1.01 for `none`), but it never converts to rank quality — a
full random-walk (RWR/heat-diffusion) over a signal this weak will not clear the
0.55 bar, let alone lift the live 0.578 blend. We stopped before the ~121 MB bulk
STRING download on that basis.

**DE kill-count now 5.** Two more pair-external DE channels have since been
gate-rejected on the same OOD-val harness: neighbour-label retrieval (STRING graph
key, AUROC_de 0.498; [[neighbor-retrieval-direction-lever]]) and char/prefix
family-retrieval (`feat/family-retrieval-baseline`, AUROC_de 0.502 ± 0.027, 5th
confirmation). The family-retrieval channel is additionally the first retrieval key
to fail the *direction* axis too (DIR 0.519 vs the STRING-graph key's 0.651) — see
[[neighbor-retrieval-direction-lever]] "The retrieval KEY decides whether DIR
transfers". Every DE channel that is a lookup/borrow over pair-external structure
lands at chance; only model-based channels remain untried.

## Why curated edges fail here (the structural reason)

The scored task is: *given an arbitrary (perturbation, readout-gene) pair, is the
gene differentially expressed?* Curated databases (CollecTRI, STRING, any
GO/pathway edge list) only assert the small set of pairs that passed a curation
threshold. So for a randomly-drawn pair, "is this a known edge?" is **almost
always no** — regardless of whether the gene is actually DE. Coverage is capped at
~1–2% for direct edges, and the network neighborhood that *is* covered carries only
a weak DE signal. This is orthogonal to the OOD-split concern (curated edges are
identity-free and transfer fine); the problem is raw sparsity + weak signal, not
leakage.

## Implication — go model-based

The only DE channels that cover ~100% of rows AND could carry real signal are
model-based:

1. **Token-logprob + self-consistency** (highest expected value): read the
   renormalized softmax over the `{up, down, none}` answer tokens instead of parsing
   a verbal label — `s_de = 1 − P(none)`, `r = P(up)/(P(up)+P(down))` — and average
   over K samples. This de-ties the output at the root (the exact failure behind the
   LB-0.488 collapse; [[track-b-abstention-failure]]) and needs no external data.
   Requires an endpoint that exposes log-probabilities (Bing's DGX Ollama for
   leaderboard-valid runs).
2. **Neighbor-retrieval of labeled train pairs** (SUMMER/PerturbQA style, published
   no-FT SOTA DE ~0.58–0.61): for an unseen (p, g), retrieve seen train rows whose
   pert or gene is a network/GO neighbor, *with their measured labels*, as grounded
   few-shot. Works under the dual-OOD split because only a *neighbor* need be seen.

## Relation to the "external knowledge is the open lane" claim

This **nuances** [[competitor-landscape]], which named "real external gene knowledge
(GO / STRING / pathway) fed to the LLM" as the unoccupied lane. That still holds for
external knowledge used as *retrieval context for a reasoning model* (route 2 above).
It does **not** hold for external edges used as a *direct curated-edge feature* on
the DE axis — that lane is occupied by sparsity. The distinction: knowledge as LLM
input ≠ knowledge as a lookup feature.

## Durable artifact

The one reusable deliverable from the branch is a channel-agnostic validation
harness — `bio_reasoning.models.fuse` (`fuse()` rank-fusion + `cfa_gate()`: admit a
channel only if standalone DE-AUROC ≥ min AND low Spearman vs the current `s_de`).
Any future DE channel (logprob, retrieval) should be validated through it on
OOD-val before spending an LB submission. It is exactly the CFA gate that rejected
the STRING proximity channel here.
