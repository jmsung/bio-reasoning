---
title: Neighbour-retrieval fails the DE axis but is a robust direction lever (+0.027 mean)
status: measured
cites:
  - findings/curated-edges-fail-de-axis.md
  - findings/track-a-eda.md
  - findings/competitor-landscape.md
---

# Neighbour-retrieval fails the DE axis but is a robust direction lever (+0.027 mean)

[[../home]] | [[../index]]

**Status: measured — from the `feat/de-retrieval` branch, 2026-07-16.**

Bottom line: label-borrowing from STRING neighbours — for an unseen (pert, gene),
average the *measured labels* of TRAIN rows whose pert or gene is a STRING neighbour
— **does nothing for DE** (AUROC_de 0.498 ± 0.006, dead chance, 4th confirmation
that the DE axis resists pair-external signal; [[curated-edges-fail-de-axis]]) but
is a **robust direction lever**: neighbour `r` scores DIR-AUROC **0.651 ± 0.047**
(seeds 0–4, all ≥ 0.58) vs the current ~0.58, and fusing it into the two-stage GO
model lifts the OOD-val **mean +0.027 ± 0.009** (all 5 seeds positive), entirely on
AUROC_dir. Leak-free (val pert/gene held out; own pair excluded) and ~98–100%
coverage — retrieval solves the coverage problem the curated edges had.

## The retrieval KEY decides whether DIR transfers (family-retrieval, 2026-07-16)

Not every retrieval key inherits this DIR lever. `feat/family-retrieval-baseline`
tried the same label-borrowing idea with a **char/prefix gene-family key** (neighbours
= TRAIN rows sharing a `family_key` = symbol minus trailing numeric index, e.g. `Rpl*`,
`Ifit*`) instead of a labeled-pair graph neighbour. Result (multi-seed OOD-val,
`scripts/family_retrieval_eval.py`): DE-AUROC **0.502 ± 0.027** (chance — the 5th dead
DE channel) *and* DIR-AUROC **0.519 ± 0.061** (chance too), 42% coverage, CFA gate
rejects 0/5 seeds, fusing *lowers* the mean (fused 0.519 < incumbent char two-stage
0.522).

So the DIR lever is **not** a generic property of "borrow neighbour labels" — it is a
property of the **key**. Labeled-pair graph neighbours (STRING/GO) put biologically
co-regulated genes next to each other, so their up/down tendency transfers. A char/prefix
string-family key groups genes by *naming convention*, which does not track co-regulated
direction on real OOD symbols — it carries neither DE nor DIR. When designing a retrieval
channel, spend the design effort on the neighbour key, not the borrowing mechanism.

## Why it splits DE from direction

- **DE (does *this* pair respond at all) is pair-specific** — a neighbour pert/gene
  has its own DE pattern that does not transfer to whether *this* pair is DE. Every
  pair-external channel tried (curated edges, network proximity, neighbour labels)
  lands at chance on DE.
- **Direction (up vs down, given DE) *does* transfer** — related TFs/genes push in
  correlated directions, so a neighbour's up/down tendency is predictive. This is
  the signal the two-stage GO model only partially captures (~0.58); neighbour
  retrieval reads it more directly (~0.65).

## Measurement (dual-OOD `holdout_split`, seeds 0–4)

| | neighbour channel | current two-stage | fused |
|---|---|---|---|
| AUROC_de | 0.498 ± 0.006 | ~0.50–0.53 | unchanged |
| AUROC_dir | **0.651 ± 0.047** | ~0.58 | ~0.63–0.72 |
| mean | — | baseline | **+0.027 ± 0.009** |

Reproduce: `scripts/de_retrieval_dir_validation.py` (multi-seed DIR) and
`scripts/de_retrieval_head_to_head.py` (fusion vs two-stage). Channel:
`bio_reasoning.features.neighbor_retrieval`; validated through the `fuse()`/`cfa_gate()`
harness ([[curated-edges-fail-de-axis]] describes the harness).

## Caveats & next

- **Update (feat/track-b-neighbour-dir-parity):** neighbour-`r` is now wired into the
  live Track B floored pipeline (`scripts/track_b_de_dir_submission.py`). It did **not**
  shrink — OOD-val **0.5916** vs the floored base 0.5647 (+0.028) and the 0.5712 dir-blend
  best (+0.020); dir 0.570→0.624 at 98% coverage. So the 0.578 blend did *not* already
  capture the neighbour direction. Kaggle LB still pending (user/Bing-gated upload) — the
  OOD-val↔LB gap has held to ~0.004 historically, so the LB should confirm. Pure feature
  channel, no LLM/Bing dependency.
- DE remains the unsolved rank-1 bottleneck; the only untried DE family is model-based
  token-logprob self-consistency (needs a logprob endpoint).
