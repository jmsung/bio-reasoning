---
title: Track A EDA — data structure and predictive signal
cites:
  - domains/ai-reasoning/source/2026-bioreasoning-challenge-overview.md
  - https://mygene.info
  - https://biit.cs.ut.ee/gprofiler/
---

# Track A EDA — data structure and predictive signal

Exploratory analysis of the Track A training data (`train.csv`, 7,705 rows;
`test.csv`, 1,813 rows). Each row is a *perturbation → target* pair: gene
`pert` is knocked down (CRISPRi) in mouse macrophages and target `gene` is
labelled `up` / `down` / `none`. Bottom line: the task **cannot be solved by
memorization** (train/test gene sets are disjoint), the **DE-vs-none** split is
deliberately hard (weak pairwise signal), but the **direction** (up vs down)
carries real biological structure tied to perturbation function.

Figures and derived tables live in `outputs/track-a-eda/` (gitignored) — upload
to Drive `04-experiments/` to share. Reproduction scripts are not yet in-repo
(they depend on mygene.info + g:Profiler APIs and a 1.5 MB GO cache); porting
them is a tracked follow-up.

## 1. Shape and class balance

- **7,705** train rows = **386** perturbations × **1,570** target genes.
- **1,813** test rows = **96** perturbations × **636** target genes.
- No missing values.
- Class balance (train): **none 55.3% · up 30.6% · down 14.1%**.
  → majority-class ("always none") accuracy baseline ≈ **55%**; `down` is the
  rare, hardest class.

## 2. Zero train/test overlap (the structural constraint)

Every test perturbation **and** every test target gene is **absent from
training** (0/96 perts, 0/636 genes; holds after case/whitespace normalization).
A model cannot look up "what did this gene do before" — it **must generalize
from biological knowledge**. This is the strongest argument for an
LLM-reasoning approach (Track A) over table lookup.

## 3. DE vs none is deliberately hard

The `none` negatives are count-matched per gene (genes that *do* respond to
other perturbations), so gene identity alone can't separate DE from none.
Decomposing where signal lives (`fig10`, `fig11`, `de_vs_none_summary.txt`):

- **Per-perturbation DE-rate is flat** (mean 0.454, std 0.058) → fixed by
  the sampling design; the perturbation alone tells you little.
- **Per-target-gene DE-rate has spread** (mean 0.477, std 0.058) → a gene
  "responsiveness" signal exists, but its predictive value is a **leaky upper
  bound** (AUROC 0.595) because test genes are disjoint — not directly usable.
- **Pair functional association** (shared GO:BP terms between pert and target)
  predicts DE only weakly: **AUROC 0.524** (≈ chance; 0.55 would be usable).

→ The DE-vs-none half of the score is the hard part; there is no easy
tabular feature.

## 4. Direction (up vs down) has biological structure

This is the more exploitable signal. Among DE rows, up-fraction by
perturbation category × target module (`fig8`, `interaction_table.csv`):

| pert ↓ / target → | apoptotic_stress | immune_effector | other |
|---|---|---|---|
| **housekeeping** | 0.68 | 0.70 | 0.75 |
| **immune** | 0.60 | 0.58 | 0.66 |
| **other** | 0.68 | 0.60 | 0.76 |

- **Perturbation category drives direction more than target module**:
  knocking down a **housekeeping** gene skews targets **up** (~68–75%);
  knocking down an **immune** gene skews targets **down** (~58–66%).
- GO enrichment of up-leaning vs down-leaning target genes overlapped heavily
  (both dominated by biotic/immune-response terms, `fig6`/`fig7`), so the
  keyword-based "stress-up vs inflammatory-down" split is **hypothesis-grade**,
  not clean.

## 5. Train vs test perturbations differ functionally (possible shift)

Top GO:BP enrichment (`fig2`/`fig3`):

- **Train** perturbations enrich for transcription / cell-cycle / chromatin /
  stress-response regulators.
- **Test** perturbations enrich for hemopoiesis, leukocyte/mononuclear-cell
  differentiation, and vesicle-mediated transport.

Coarse housekeeping/immune/other proportions are similar across splits, but the
finer functional emphasis shifts. Worth accounting for when validating — a
model tuned on train-perturbation biology may face different test biology.

## Implications for modeling (Track A)

- Lean on **reasoning over gene function**, not memorized gene→outcome maps.
- Expect **DE-vs-none to be the bottleneck**; direction is more learnable.
- A prompt should surface the **perturbation's function** (especially
  immune vs housekeeping) and the **target's function**, since their
  interaction carries the directional signal.

## Method caveats

GO:BP annotations from **mygene.info**; over-representation from **g:Profiler**
(`organism=mmusculus`, GO:BP, g:SCS correction). The
housekeeping/immune/other and target-module labels are **keyword matching over
GO:BP term names** — reproducible but heuristic. Treat category-level claims as
hypothesis-grade. AUROCs that use a gene's own train statistics are leaky given
the disjoint test split and are reported only as upper bounds.
