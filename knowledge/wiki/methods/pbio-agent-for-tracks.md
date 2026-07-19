---
title: Adapting PBio-Agent (LINCSQA) to our Track A/B task
status: proposed
cites:
  - domains/ai-reasoning/source/2026-kim-pbio-agent.md
  - domains/ai-reasoning/source/2026-bioreasoning-challenge-overview.md
  - findings/track-a-eda.md
  - findings/housekeeping-transfer-hypothesis.md
  - findings/tabpfn-for-perturbation-tracks.md
  - domains/ai-reasoning/source/2025-wu-perturbqa.md
  - findings/track-b-abstention-failure.md
---

# Adapting PBio-Agent to our Track A/B task

**Status: proposed — not yet built or measured.**

PBio-Agent ([[2026-kim-pbio-agent]]) is a training-free multi-agent framework
that predicts gene-regulation direction under perturbation by reasoning over
biological knowledge graphs. Its design maps cleanly onto our challenge, which
this page works out.

## Our task (recap)

Predict `(pert_gene, target_gene) → {up, down, none}` in **macrophages**.
Zero train/test overlap on *both* the perturbation and target axes, so
memorization is worthless — external biological priors are the only signal.
`none` is the 55% majority class. Base model GPT-OSS-120B is fixed.
Track B: ≤100 tools, ≤250 calls/row, 16k prompt tokens, traces required, no
fine-tuning. Details: [[2026-bioreasoning-challenge-overview]].

## Why this method fits Track B specifically

The zero-overlap split is *designed* to reward reasoning that generalizes, not
distribution-learning. PBio-Agent's thesis — reason over a knowledge graph
rather than learn the label distribution — is exactly the bet that could make
Track B (agents + tools) pull ahead of Track A (prompt-only), which are
currently tied at ≈0.65 on the leaderboard.

## Component mapping

| PBio-Agent component | Our adaptation |
|---|---|
| **Context agent** (cell line / tissue) | Fixed to macrophages → job becomes "is `pert`/`target` expressed/active in macrophages? If not → lean `none`." |
| **Mechanism agent** (MoA) | Does `pert` plausibly regulate `target` via a known pathway? Tools: Reactome / KEGG / GO. |
| **Network agent** (STRING curriculum) | STRING / TF-target graph distance between `pert` and `target`. Direct regulatory edge → strong up/down prior; distant → `none`. |
| **Integration + GAT** | ⚠️ A *trained* GAT reads as fine-tuning — keep integration LLM-only for Track B; a GAT belongs in **Track C**. |
| **4 Judge agents** (consistency / logic / target-verifier / history-leakage) | Verification tools — and the lever for the `none` class (see adaptations). |
| **Difficulty curriculum** (confident → hard) | Transfers *within the test set*: `id = pert_gene`, so many rows share a `pert`. Predict confident direct-neighbor targets first, use them to condition ambiguous ones. |

## Three critical adaptations (where a naive port fails)

1. **The `none` class is the whole game.** PBio-Agent is binary up/down; a
   reasoning LLM is biased to "find an effect." Add an explicit **abstain
   policy**: emit up/down only when mechanistic *or* network evidence supports
   a direction, else `none`. A skeptic judge that enforces this directly
   attacks the 55% majority — likely worth more than agent-count sophistication.
2. **Within-test curriculum, not train-based.** Zero train overlap kills their
   STRING-relatedness-to-training-examples idea, but the same-perturbation
   grouping survives *inside* the test set — still usable for confident→hard
   ordering.
3. **Budget / traces.** 250 calls/row × 1,813 rows is real cost. Batch tool
   calls per perturbation (shared STRING / pathway lookups), cache the KG.
   Traces are required anyway — the agent design produces them for free.

## Connection to our existing leads

Our Track A EDA found perturbation *category* drives direction (housekeeping →
up ~70%, immune → down ~60%; [[track-a-eda]], [[housekeeping-transfer-hypothesis]]).
That is a coarse biological prior the Network/Mechanism agents can encode
directly — a cheap, testable feature to seed the reasoning.

## Track A spillover (cheap — do it alongside)

Collapse the three scientist personas into one structured single-call prompt
(context → mechanism → network → abstain-or-decide) plus self-consistency over
the 3 allowed samples. Same reasoning skeleton, no tools, 4k-token budget.
Serves as the control that Track B's agent must beat to justify its complexity.

## Open questions

- Which KG tools give the best signal-per-call: STRING, Reactome, KEGG, GO,
  a TF-target regulatory net (e.g. DoRothEA), or a macrophage-specific atlas?
  A frozen **TabPFN** numeric prior is another candidate tool here — as an
  anchor the reasoning adjusts, not the answer ([[tabpfn-for-perturbation-tracks]]).
- How to score per-prediction confidence for the curriculum ordering.
- Is any auxiliary trained model (GAT) worth pushing into a Track C variant,
  or does it stay a pure-reasoning play?
- Cost ceiling: how few tool calls per row still capture the signal.
