# Track A — Description of Approach

**From:** Joo · **For:** Jongmin (to structure into a plan)

> _Early approach notes (2026-07-14), since validated/extended by the findings: direction, functional (not identity) retrieval, and the dual-OOD holdout were **confirmed** and are central to the final method; the DE-confidence-from-prior-data and literature-crawl ideas were **tested and closed** (DE proven unlearnable, external-knowledge parity). See [`reports/technical-report.md`](../reports/technical-report.md) and [`knowledge/wiki/findings/`](../knowledge/wiki/findings/)._

Track A is the prompt-only track: a single model call per perturbation–gene
pair, no tools. Our proposal here is a **safe, evidence-grounded baseline** —
the floor that the agentic Track B method (see `track-b-approach.md`) has to
clear. The thinking and the constraints below come from our EDA + literature;
the actual benchmark structure is left to you.

## Two data findings that shape everything

1. **The metric is AUROC, not accuracy** (`mean(AUROC_de, AUROC_dir)`). A
   constant "predict none" scores ~0.5, not 55% — ranking, not thresholding.
   So every method must emit a **graded** up/down confidence. "Default to none"
   survives, but as *low DE-confidence by default, raised on evidence*.
2. **The two sub-scores behave differently.** DE-vs-none is the **hard axis**
   (per-perturbation DE-rate is essentially design-flat; pairwise signal ~0.52).
   Direction (up vs down) is the **tractable axis**: our EDA found a real,
   likely-conserved pattern — housekeeping-gene perturbations skew targets **up**
   (~70%), immune/inflammatory perturbations skew them **down** (~60%).

## Approach — evidence-grounded prior

A transparent, cheap scoring rule (no LLM required): default every pair to low
DE-confidence, and become confident only where prior data supports it.

- **Direction:** apply the conserved priors — housekeeping perturbation → up,
  immune/myeloid → down.
- **DE-confidence:** raise it when there's a **known perturbation effect** in
  prior data — housekeeping genes whose function is conserved across cell types
  (testable on Replogle K562 vs RPE1), or macrophage/myeloid-expressed genes
  with documented effects (Papalexi THP-1, Dixit mouse BMDMs).
- **Expand the evidence base:** actively crawl for relevant literature and
  datasets (papers reporting known perturbation effects, additional Perturb-seq
  / augmentation sources) and fold them into the wiki. The prior is only as good
  as the evidence it can draw on, so widening coverage directly improves it.
- **Key constraint:** the test perturbations and genes are **fully disjoint**
  from train, so any lookup must be by **functional similarity (GO / pathway /
  PPI), not gene identity** — identity matching returns nothing on the real
  test set.

In short: *pick none unless the biology gives a confident, conserved reason to
call a direction.*

## One methodological ask

However it's structured, local validation should **hold out entire
perturbations and genes**, not random rows — that's the only way it mirrors the
real disjoint test.
