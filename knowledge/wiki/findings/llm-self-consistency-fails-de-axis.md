---
title: LLM self-consistency does not crack the DE axis — near-chance, like every other channel
status: draft
cites:
  - findings/curated-edges-fail-de-axis.md
  - findings/direction-transfers-de-doesnt.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/track-a-eda.md
  - domains/ai-reasoning/source/2026-yuan-plausibility-not-prediction-llm-perturbation.md
---

# LLM self-consistency does not crack the DE axis — near-chance, like every other channel

[[../home]] | [[../index]]

**Status: draft — kill-test from the `feat/de-logprob-self-consistency` branch, 2026-07-17.
Measured a model-based self-consistency channel on the dual-OOD val split; DE stays at chance.**

Bottom line: sampling an LLM K times per `(perturbation, target-gene)` pair and
aggregating the up/down/none votes into a graded score — the "self-consistency"
hypothesis for the hard DE axis — lands **AUROC_de = 0.495 (dead chance)** while
**AUROC_dir = 0.571 (learnable)**. This is the exact axis-asymmetry the project
keeps rediscovering: DE resists, direction transfers. The LLM channel joins the six
curated / retrieval channels that already failed DE ([[curated-edges-fail-de-axis]],
[[neighbor-retrieval-direction-lever]]).

## The test

- **Signal:** `models/de_logprob.py` `votes_to_scores` — sample-and-vote self-consistency
  (Wang et al. 2022). K samples per pair → vote fractions `(p_up, p_down, p_none)`; the
  Track A rank metric consumes DE = `p_up + p_down`, DIR = `p_up/(p_up+p_down)`.
- **Harness:** `scripts/de_logprob_probe.py` — dual-OOD `holdout_split` → K samples/row →
  official `eval.track_a_score.evaluate`.
- **Config:** 150 dual-OOD val rows × 3 samples, Claude sonnet-4.5 (temperature 1.0),
  direct up/down/none prompt.

## Result

| Axis | AUROC | Read |
|---|---|---|
| DE  | **0.495** | dead chance (= 0.500) — hypothesis dead |
| DIR | 0.571 | learnable, consistent with prior direction channels |
| mean | 0.533 | ~ the evidence-prior floor |

## Why it was predictable (and predicted)

The consult-KB-first gate flagged this *before* the build: DE is near-chance under
dual-OOD **by construction** — `none` negatives are count-matched per gene, DE-rate is
flat across perturbations, functional association predicts DE only weakly ([[track-a-eda]]).
And LLMs specifically carry a **systematic over-DE bias** — Yuan 2026 measured a
representative LLM predicting "responds" for 92% of queries at a 29% true rate
("Plausibility Is Not Prediction"). Self-consistency
averages *variance*; it cannot remove a *systematic bias*, and a confident-but-near-chance
signal still scores AUROC_de ≈ 0.5 on a rank metric.

## Caveat + open thread

Run on the **Claude dev-fallback**, not the leaderboard-valid gpt-oss-120b (Bing's DGX was
unreachable). The DE-near-chance thesis is model-agnostic (non-LLM channels failed too), so
the negative is strong — but a gpt-oss confirmation is a cheap re-run
(`BIOREASONING_LLM_PROVIDER=ollama … scripts/de_logprob_probe.py`). Yuan's CORE result
suggested the *contrastive* framing (compare against related perturbations' known outcomes) as
the one LLM-DE approach with evidence — but that route is **also already killed**: CORE-Voting
measured **0.498** on our dual-OOD split ([[contrastive-de-core-assessment]]). So both
single-pair *and* contrastive LLM-DE are ruled out here; do not re-propose either.

## What to do

Stop spending DE effort on single-pair LLM scoring. Returns live on the **direction** axis
([[direction-transfers-de-doesnt]]) or an external Perturb-seq data lane. Reusable apparatus
(`de_logprob.py`, `de_logprob_probe.py`) is kept for a contrastive-DE or gpt-oss re-run.
