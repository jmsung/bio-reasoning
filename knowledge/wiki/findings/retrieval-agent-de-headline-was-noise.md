---
title: The retrieval agent's AUROC_de=0.631 was 150-row noise — it regresses to 0.577 (≈the 0.555 ceiling)
type: findings
status: measured
cites:
  - findings/de-unlearnable-oracle-ceiling.md
  - findings/de-unlearnable-on-dual-ood.md
  - findings/curated-edges-fail-de-axis.md
  - findings/neighbor-retrieval-direction-lever.md
---

[[../home]] | [[../index]]

# The retrieval agent's DE headline was small-sample noise

**Status: measured** — from `feat/track-b-full-read`
(`scripts/track_b_retrieval_agent.py --eval`, `scripts/track_b_retrieval_fuse_eval.py`),
3 dual-OOD seeds × 500 rows, gpt-oss-120b via OpenRouter.

The external-knowledge retrieval agent (PR #72) reported, on a **single 150-row** dual-OOD
holdout, **AUROC_de=0.631** — above the leakage-allowed oracle ceiling of 0.555
([[de-unlearnable-oracle-ceiling]]). Because the agent uses external GO/STRING retrieval the
oracle never had, beating 0.555 was possible *in principle*, so the number had to be resolved:
real signal or noise.

## Leakage audit: leak-free (no fitted component at all)

The pipeline has **nothing fitted on labels**. Per row it retrieves the pert's and target's
GO:BP terms (external mygene.info cache), a **hardcoded** 3-category direction prior
(`models.track_a_prior.PRIORS`, hand-set constants — not fit), and optional STRING partners
(external string-db). A frozen LLM reasons over that context. The eval split is dual-OOD with
`assert_leak_free` enforced (val perts *and* genes disjoint from train), and STRING/GO are
label-free external biology, so a val pair's own DE label cannot enter its context. Verdict:
**leak-free** — the DE signal, whatever its size, is honest.

## Trustworthy read: 0.631 regresses to 0.577 ≈ the ceiling

| dual-OOD seed (N=500) | AUROC_de | AUROC_dir | mean |
|---|---|---|---|
| 0 | 0.533 | 0.527 | 0.529 |
| 1 | 0.585 | 0.657 | 0.621 |
| 2 | 0.616 | 0.560 | 0.587 |
| **3-seed** | **0.578 ± 0.043** | **0.580 ± 0.068** | **0.579 ± 0.047** |
| pooled 1500-row bootstrap | 0.577, 95% CI **[0.549, 0.607]** | — | — |

The 0.631 headline **does not reproduce**: at N=500 the DE point drops to 0.577, and the 95% CI
**includes the 0.555 identity/marginal ceiling** (lower bound 0.549). Per-seed DE swings 0.533→0.616
— a ±0.04 band that straddles chance and the ceiling. So DE is at most **marginally** above 0.555
(+0.02, < 1 SEM), not decisively; the single-150-row 0.631 was the high tail of a wide small-sample
distribution. This is consistent with — not a break from — [[de-unlearnable-oracle-ceiling]] and
[[curated-edges-fail-de-axis]]: GO/STRING carries at most a whisper of transferable DE signal, far
below the field's 0.693. **No DE-wall breakthrough.**

## Fusion: agent DE ⊕ neighbour DIR ≈ incumbent (parity)

The agent is strong-nothing on DE but its DIR is seed-noisy (0.53–0.66). Fusing the incumbent
STRING-neighbour DIR ([[neighbor-retrieval-direction-lever]]) into the agent's DE magnitude
(`fuse_neighbour_direction`, metric math up=DE·r / down=DE·(1−r), DE ranking preserved) gives a
3-seed fused mean of **0.604 ± 0.035** (seeds 0.563 / 0.622 / 0.626) vs the **0.597** incumbent LB —
**statistical parity** (+0.007, within noise). Standalone agent (0.579) is *below* incumbent.

## Verdict

- **Leakage:** leak-free (no fitted component; dual-OOD asserted).
- **DE:** 0.631 was noise; trustworthy 0.577 [0.549, 0.607] — not decisively above 0.555.
- **Best candidate:** fused (agent DE ⊕ neighbour DIR) ≈ 0.60, parity with the 0.597 incumbent —
  not a clear improvement. The DE axis remains the unbroken rank-1 bottleneck.
- **Lesson (reinforced):** never trust a rank-metric AUROC from <200 dual-OOD rows — the seed/
  subsample band is ±0.04+. Gate any "we beat the ceiling" claim on ≥500 rows × multi-seed.
