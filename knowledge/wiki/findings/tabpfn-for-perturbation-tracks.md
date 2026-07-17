---
title: TabPFN / tabular foundation models for Track A and B
status: draft
cites:
  - source/2026-bioreasoning-challenge-overview.md
  - findings/track-a-eda.md
  - methods/pbio-agent-for-tracks.md
  - domains/bio-multiomics/source/2026-palla-tabular-foundation-models-perturbation.md
---

# TabPFN / tabular foundation models for Track A and B

[[../home]] | [[../index]]

**Status: draft — combiner framing measured (negative, below); primary-predictor
framing not yet built.**

Can a general-purpose **tabular foundation model** (TabPFN / TabICL — Prior-Fitted
Networks that do zero-shot in-context inference, no training) serve as the
prediction engine for our challenge? Bottom line: **yes for Track A** (a strong,
near-zero-effort baseline that should beat the 0.529 prior floor), and **yes as a
tool for Track B** (a fast numeric prior the agent consults) — but it does *not*
solve the hard part (OOD-both-axes generalization), and in Track B it must be an
*anchor, not the answer*.

## Why it's a real candidate (not just a hunch)

The direct evidence is [[2026-palla-tabular-foundation-models-perturbation]] —
Palla et al., *Tabular Foundation Models Are Competitive Cellular Perturbation
Predictors Across Biological Scales* (CZ Biohub, 2026; bioRxiv 10.64898/2026.06.28.735106).
TabPFN/TabICL **match or beat every specialized single-cell model** (scGPT,
scLAMBDA, PRESAGE, Prophet) at perturbation-response prediction across four
benchmarks, with *no biology-specific pretraining* — a PFN backbone ranked #1 on
all of them. The paper's thesis: **strong posterior-predictive regression + good
featurization matter more than hand-crafted biological inductive biases.**

TabPFN's practical draw fits this project's "don't hand-tune, let the system do
it" philosophy: one forward pass, frozen backbone, calibrated probabilities, fast.

## Track A — strong direct fit

Track A is already a tabular problem: featurize each `(pert, target_gene)` pair →
predict `{up, down, none}`, scored by AUROC. TabPFN is a drop-in replacement for
the hand-set `PRIORS` dict in `src/bio_reasoning/models/track_a_prior.py`:

- Features must be **transferable**, never identity — the split is doubly
  disjoint (0 overlap on *both* perts and target genes; [[track-a-eda]]). Use
  pert features (GO / pathway / embedding), gene features (baseline expr, GO,
  network centrality), maybe pair features.
- TabPFN's calibrated class probabilities map *directly* onto the AUROC metric
  (which needs a score, not a hard label).
- Validate on the existing `doubly_disjoint_folds`; target is to beat the
  **0.529** Track A prior floor (PR #9).

## Track B — useful as a tool, with a caveat

Track B is *"design tools and multi-agent architectures around a fixed LLM; no
fine-tuning of the base model"* ([[2026-bioreasoning-challenge-overview]]). Key
facts that make TabPFN legitimate here:

- **A and B share the same data byte-for-byte and the same split** — they differ
  only in modeling constraints. So a `tabpfn_predict(pert, gene)` tool is a fair,
  on-thesis Track B tool.
- TabPFN is **not the base LLM and isn't fine-tuned** (frozen, in-context) → it
  passes the "fixed LLM, no fine-tuning" clause.
- It's cheap against the B budget (≤100 distinct tools, ≤250 calls/row, 16k
  prompt tokens): local compute, doesn't burn prompt tokens; one distinct tool.

**The caveat is the whole question for B.** Because A and B are the *same task*,
whatever TabPFN scores in A is your **Track B floor**. If the agent just calls
TabPFN and echoes it, you've spent LLM tokens to reproduce the A score — no gain,
and arguably against the track's intent (it measures *reasoning*). TabPFN's value
in B is as an **anchor**: it supplies the base rate, and the agent earns its keep
by spending its reasoning/retrieval budget exactly where TabPFN is weakest — the
OOD-both-axes cases — using literature / pathway / network evidence to *adjust*
the prior. This complements the reasoning-first design in
[[pbio-agent-for-tracks]] (TabPFN is a candidate answer to its "which tools give
the best signal-per-call" open question).

## Honest caveats

- **OOD-both-axes is the hard regime.** TabPFN's strongest wins lean on
  in-context support from *related* rows; when both perts and genes are novel,
  you're in the paper's hardest setting (genome-wide CD4+ T-cells), where TabPFN
  was *the only model positively correlated with truth but only modestly*
  (+0.108 cosine top-20 DE). Expect "beats the floor / great cheap baseline," not
  "solves OOD."
- **Featurization is the real lever**, per the paper itself. GIGO — TabPFN won't
  invent transferable signal that the features don't encode.
- **Scale limits.** TabPFN v2 is happiest ≲10k rows / ≲500 features (train is
  7,705 rows — fine); subsample / ensemble if features balloon. The paper's
  diversity-aware (farthest-point) support selection recovered near-full signal
  from ~25% of perturbations.
- **Output basis matters** for the regression framing (NMF > PCA by +0.117 in the
  paper); less relevant if we frame Track A as direct 3-class classification.

## To verify before committing

- Confirm on the Kaggle **Track B** rules page that arbitrary offline/precomputed
  models are allowed as tools (the "fixed LLM, no fine-tuning" clause implies yes,
  but `docs/kaggle-rules.md` is currently silent on Track B tool scope).

## Measured: TabPFN-as-combiner is a dead frame (`feat/tabpfn-functional-features`)

TabPFN trained as a *learned combiner* over the three DIRECTION channels (GO /
neighbour / embedding) — leak-free, out-of-fold features on the dual-OOD holdout —
scored **DIR-AUROC 0.613 ± 0.039**, *below* neighbour-DIR (0.651) and equal-weight
fusion (0.642) on identical val rows. It does not clear the ~0.65 hand-fused
ceiling. Consistent with the paper's own thesis above: **featurization is the
lever, not combiner form** — swapping equal-weight rank-fusion for a nonlinear
TabPFN head over 3 saturated channels (~250 OOD rows) invents no new signal.

Corollary for **derivatives** (TabICLv2, TabDPT, TabForestPFN, LimiX, TabPFN v2.5):
they differ in *scale* and *priors*, not in ability to conjure signal a 3-feature /
250-row combiner lacks — so as a **combiner swap** they are near-zero EV. The open
lane is the *other* use: a tabular FM as the **primary predictor over rich pair
features** (below), where a retrieval-augmented derivative (TabDPT) is the
interesting candidate — but it still meets the OOD-both-axes wall (Palla: only
modestly positive in the hardest genome-wide setting). Deps note: pin
`tabpfn>=2.1,<2.2` (v8+ adds a `TABPFN_TOKEN` license gate that breaks offline
runs); TabICL is Apache-open.

## Next step

Cheap experiment: `feat/tabpfn-track-a` — featurize pairs → TabPFN classifier →
`prediction_up/down` → validate on `doubly_disjoint_folds` vs the 0.529 floor. If
it clears the floor at near-zero effort, it becomes both a strong Track A baseline
*and* the anchor tool for a Track B agent. (This is framing #2 — primary predictor
over rich features — and remains untried; the combiner framing above is closed.)
