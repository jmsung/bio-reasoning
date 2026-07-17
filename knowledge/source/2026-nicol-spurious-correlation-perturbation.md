---
source_url: https://www.biorxiv.org/content/10.64898/2026.05.07.723486v1
source_type: papers
title: "Spurious correlation inflates performance in single-cell perturbation prediction"
author: Phillip B. Nicol et al.
retrieved: 2026-07-16
doi: 10.64898/2026.05.07.723486
---

# Spurious correlation inflates performance in single-cell perturbation prediction

**Authors:** Phillip B. Nicol, Shriya Shivakumar, Rafael A. Irizarry
**Year:** 2026
**Venue:** bioRxiv (preprint)

> Note: paperclip full text was unavailable at ingest (slab service down) and the
> bioRxiv page blocks automated fetch. This page is grounded in the paper's
> abstract as retrieved via web search; it deliberately avoids quoting specific
> numeric magnitudes that could not be verified against the full text.

## Abstract
As the number of computational methods for predicting the effects of genetic
perturbations on cellular gene-expression profiles has grown, so has the need for
rigorous evaluation metrics. Recent benchmarking studies score predictions using
the correlation (or cosine similarity) of differential expression measured
relative to a shared population of control cells. The authors show that these
metrics are systematically inflated by a statistical bias: the same control
population is reused to define both quantities being compared, inducing a spurious
correlation between them. Because of this bias, even non-informative methods can
appear to perform well, an effect that is most severe in datasets with a limited
number of control cells. Reanalyzing published datasets with a simple
control-splitting procedure that removes the shared-control dependence eliminates
much of the apparent signal, showing that a substantial fraction of previously
reported performance was an artifact of the evaluation rather than genuine
biological prediction.

## Key contributions
- Identifies a concrete statistical bias — reuse of a shared control population to
  define both predicted and observed differential expression — that inflates
  correlation/cosine-similarity benchmarks for single-cell perturbation models.
- Shows the inflation is strong enough that non-informative baselines look
  competitive, especially when control-cell counts are low.
- Proposes a simple, general fix: a control-splitting procedure that uses disjoint
  control cells for the two sides of the comparison, removing the spurious
  dependence.

## Methods
The core argument is a statistical analysis of the standard evaluation pipeline:
predicted and measured perturbation effects are both expressed as differential
expression against the same control population, so their correlation contains a
bias term that does not reflect predictive skill. To demonstrate the problem
empirically, the authors reanalyze published single-cell perturbation datasets and
benchmark results under (a) the conventional shared-control metric and (b) a
control-splitting procedure that partitions control cells so the reference used for
the prediction target is independent of the reference used to score it. Comparing
the two isolates how much reported performance is attributable to the bias versus
real signal.

## Key results
- Standard correlation/cosine-similarity benchmarks are systematically inflated by
  the shared-control bias, so even non-informative methods score well.
- The inflation grows as the number of control cells shrinks, making
  small-control-set datasets especially misleading.
- After bias-corrected control splitting, the apparent performance of published
  methods drops substantially, indicating that much of the credited "biological
  signal" was an evaluation artifact.

## Why it matters for our work
This is a direct methodological warning for the BioReasoning Challenge. Tracks A/B
score up/down/none direction predictions of perturbation effects, and any internal
CV we build on differential expression relative to controls is exposed to exactly
this bias — inflated correlation metrics that make weak or abstaining predictors
look strong. It reinforces our own hard-won lesson that small-CV rank/correlation
scores can be misleading (cf. the Track B LB-vs-CV gap): trust bias-corrected,
disjoint-control evaluation over headline correlation numbers, and be skeptical of
benchmarks where non-informative baselines are not reported. When we compare
perturbation predictors, we should split control cells so the scoring reference is
independent of the target reference.

## Limitations / open questions
- Full quantitative magnitudes (exact performance drops per dataset/method) could
  not be verified here because full text was inaccessible at ingest — re-ingest
  from paperclip when the slab service recovers to capture the numbers.
- The bias is framed for correlation/cosine metrics against shared controls; how
  it interacts with categorical direction (up/down/none) metrics used in Tracks A/B
  is not spelled out and warrants checking.
- Control-splitting reduces the effective number of control cells used per side,
  which may raise variance in low-cell datasets — a trade-off worth quantifying.
