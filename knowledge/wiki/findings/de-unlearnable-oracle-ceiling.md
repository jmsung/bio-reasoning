---
title: DE is unlearnable from identity/marginals — a leakage-allowed oracle caps at 0.555 (≈chance) on OOD
type: findings
status: measured
cites:
  - findings/track-a-error-structure.md
  - findings/marginal-de-caps-at-degree.md
  - findings/direction-transfers-de-doesnt.md
  - findings/curated-edges-fail-de-axis.md
  - findings/contrastive-de-core-assessment.md
---

[[../home]] | [[../index]]

# DE is unlearnable from identity/marginals — the oracle ceiling is ≈chance

**Status: measured** — from `analysis/de-ceiling-probe`
(`scripts/de_ceiling_probe.py`, `eval/de_ceiling.py`, 8 dual-OOD seeds).

[[track-a-error-structure]] showed the incumbent's AUROC_de sits at chance in *every*
perturbation category — uniformly absent, not a weak-average-with-a-good-subpopulation.
That raised the prior question this probe answers before any further DE engineering:
**is DE learnable at all from gene/pert identity and marginal structure?** The answer is
a rigorous **no** — and getting there exposed a leakage trap worth remembering.

## The probe: a leakage-allowed oracle upper bound

Give a head the one thing an honest model never gets — each gene's and pert's *true* DE
propensity — and see whether it can rank none-vs-DE on the dual-OOD val split. Because the
oracle can only do better than any leak-free model, its AUROC_de is a hard **upper bound**:
a low oracle ceiling is a hard negative result. Features (`ORACLE_FEATURES`): per-gene and
per-pert DE-rate, plus label-free structural counts (gene/pert multiplicity).

## The trap: the naive oracle scores 0.960 — and it is a mirage

Computing per-gene/pert DE-rate as a **full-data leave-one-out** rate and fitting a head
gives **AUROC_de 0.960**. It is not real. The tell: `gene_de_rate` alone scores **0.108**
(far *below* chance — anti-correlated), and a logistic head simply flips the sign. The
mechanism is intra-val label leakage: `holdout_split` places all of a gene's rows in val
*together*, so a leave-one-out rate leaks each val row's own label into its gene-mates. For
a gene that appears twice (the median multiplicity here is 2), the LOO rate of one row *is*
the other row's label. **The real test set holds out every gene and pert** (zero labeled
rows for a test identity), so this signal cannot exist at inference time. 0.960 is an
artifact of letting val rows see each other.

## The honest oracle: 0.555 ± 0.036 ≈ chance

The honest encoding derives each rate from the **train partition only**; an identity unseen
in train scores the prior. On a dual-OOD split *every* val identity is unseen by
construction, so the rate channels collapse to the prior — and that collapse **is** the
finding: identity does not transfer.

| honest channel (8 dual-OOD seeds) | AUROC_de |
|---|---|
| gene_de_rate | 0.500 ± 0.000 *(identity unseen OOD → prior)* |
| pert_de_rate | 0.500 ± 0.000 |
| gene_count | 0.585 ± 0.015 |
| pert_count | 0.437 ± 0.006 |
| **fitted_head (honest upper bound)** | **0.555 ± 0.036** |
| leaked_head *(mirage, unachievable at test)* | 0.960 ± 0.008 |

The only above-chance channel is `gene_count` (0.585) — a **label-free structural count**
(how often a gene is probed), not a DE mechanism, and it converges with the STRING-degree
proxy that [[marginal-de-caps-at-degree]] already found caps at ~0.536. Per-pert DE
propensity is flat (all 386 perts sit within ±0.06 of the global 0.447 rate).

## Verdict — NO-GO on the identity/marginal DE bet

DE is **effectively unlearnable from gene/pert identity and marginals on OOD**: the honest
oracle ceiling (0.555) is barely above chance and « the field's 0.693, and what little it
has is a structural-count correlate, not a usable DE signal. This closes the identity/
marginal lane the same way the static, curated-edge, self-consistency, and contrastive
routes were closed ([[marginal-de-caps-at-degree]], [[curated-edges-fail-de-axis]],
[[llm-self-consistency-fails-de-axis]], [[contrastive-de-core-assessment]]). Combined with
[[track-a-error-structure]], the DE axis is now negative from every offline direction we can
probe. **The only remaining rank-1 DE lever is model-based token-logprob** (Bing-gated); if
that fails, the DE-at-chance decomposition here + the error-structure EDA are a publishable
negative result.

## Method notes / caveats

- The honest/leaked split is the load-bearing distinction: any probe that lets a held-out
  identity's own co-occurring labels inform its features will manufacture a phantom ceiling.
  General rule for OOD ceiling probes: derive identity-conditioned features from **train
  only**, never full-data leave-one-out, when the split holds the identity out.
- The multi-seed spread is diagnostic: honest rate channels are 0.500 ± 0.000 (structurally
  pinned), while a noise-driven feature would show ≈0.50 with *wide* variance.
- `gene_count`/`pert_count` are mild structural leakage (full-data multiplicity) but carry
  no labels; treated as a benign, transferable stat. Even so they cap at 0.585.
- Reproduce: `uv run python scripts/de_ceiling_probe.py --seeds 0 1 2 3 4 5 6 7`.
