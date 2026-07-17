---
title: Direction transfers, DE doesn't — the axis-asymmetry principle
type: findings
status: measured
cites:
  - findings/neighbor-retrieval-direction-lever.md
  - findings/curated-edges-fail-de-axis.md
  - findings/housekeeping-transfer-hypothesis.md
  - findings/track-a-eda.md
---

[[../home]] | [[../index]]

# Direction transfers, DE doesn't

**The single most consequential fact in the project, now corroborated by external
literature.** For a perturbation-response prediction where test perturbations and
target genes are both unseen (dual-OOD), the two metric axes behave oppositely:

- **DE-detection** (does this pair respond at all) is **pair-specific and does not
  transfer** — from features, from curated edges, from neighbour labels, or from
  external measured data. It sits near chance (AUROC ≈ 0.50).
- **Direction** (up vs down, given a response) **transfers** — because co-regulated
  genes push their targets in correlated directions, and the housekeeping-up /
  immune-down tendency is a broad, context-shared program. It is learnable and
  improvable (AUROC_dir ~0.53 → ~0.65).

Every leaderboard gain we've booked (Track A 0.529→0.585, Track B 0.488→0.597) is a
**direction** gain; the DE axis never moved off chance.

## Internal evidence (measured on our dual-OOD `holdout_split`)

- **Six independent DE channels all at chance**: CollecTRI TF-regulon (0.4% cov),
  STRING 1-hop (1.6%), STRING 2-hop (0.543), neighbour-label retrieval (0.498),
  char/prefix family retrieval (0.502), learned GO model (0.500)
  ([[curated-edges-fail-de-axis]], [[neighbor-retrieval-direction-lever]]).
- **The same neighbour-retrieval channel is a robust direction lever**: DIR-AUROC
  **0.651 ± 0.047** (5 seeds, all ≥ 0.58), fuses to **+0.027 ± 0.009** OOD-val mean,
  entirely on `AUROC_dir` ([[neighbor-retrieval-direction-lever]]).
- Pair GO-association predicts DE only at 0.524 ≈ chance ([[track-a-eda]]).

## External corroboration (2026-07 literature review)

The published field independently reproduces the asymmetry:

- **SUMMER / PerturbQA** (Wu et al. 2025, arXiv 2502.21290): the no-fine-tune SOTA
  scores DE-AUROC **0.58–0.61** but direction-AUROC **0.62–0.69** — direction is
  4–8 points easier — and its retrieval is *within*-dataset, not cross-dataset.
- **Ahlmann-Eltze et al. 2025** (*Nat. Methods*, DOI 10.1038/s41592-025-02772-6):
  on unseen perturbations, the method that *consistently beat every DL/foundation
  model* was a **linear model with perturbation embeddings pretrained on the *other*
  cell line** (Replogle K562↔RPE1) — i.e. cross-cell-type transfer works, but it
  works by moving the *response/direction*, and **generic atlas/foundation-model
  augmentation washed out** (scGPT/scFoundation/Geneformer/UCE ≈ random embeddings).
- **scPerturBench** (Wei et al. 2025, *Nat. Methods*): 27 methods × 29 datasets —
  all degrade sharply i.i.d.→o.o.d.; simple linear baselines stay competitive.
- **Cross-species bound**: Schroder et al. 2012 (PNAS) — ~**24% of LPS-regulated
  orthologs are divergently regulated** between human and mouse macrophages, and the
  divergent set is enriched for the *immune-effector* program, sparing the
  housekeeping core → the transferable slice is housekeeping/essential, consistent
  with [[housekeeping-transfer-hypothesis]].

### Measured on our task — PerturbQA → Track A (2026-07, `research/perturb-seq-transfer-probe`)

We directly tested external measured transfer, and it is a **textbook
selection-inflation trap**. On the 242 exact-pair overlap (PerturbQA human CRISPRi
→ Track A mouse), external labels scored **DE-AUROC 0.722 / DIR-AUROC 0.951**
(shuffle control 0.50 — real signal), and the DE part was *marginal pert-propensity*
(per-pert LOO 0.68, per-gene LOO 0.54 = chance) that even beat our internal
STRING-degree marginal-DE proxy (0.536). It looked like the first real DE lever.
**But it collapsed on the honest dual-OOD split**: fused into GO+neighbour-DIR the
lift is **+0.0075 mean and one-seed noise** (seed1 +0.022; seeds 0/2 ≈ 0), external
OOD DE-AUROC falls to **~0.53** (0.504/0.565/0.517), CFA passes **1/3** seeds, and
direction is redundant with neighbour-DIR (+0.002). The overlap is the robustly-DE
*easy* pairs. **Rule: gate on the dual-OOD fusion delta across seeds, never a
standalone overlap AUROC** — the 4th instance of this trap (field char-ngram
0.693→0.552; Track B CV 0.675→LB 0.488; internal marginal-DE overlap).

**Confirmed end-to-end on the real board (2026-07-17, `research/perturb-seq-real-lb-overlap`).**
The last escape hatch was "we killed the lane on a too-hard *synthetic* split." We spent the one
reserved real-LB read: submitted baseline `fuse([GO, neighbour])` **0.585** and `+ external
PerturbQA DE+DIR` **0.586** to the actual Track A board — **Δ+0.001** at 66% coverage. The real
leaderboard agrees with the OOD-val gate: external Perturb-seq moves nothing, and the **dual-OOD
split is honest**, not an over-hard artifact. The Perturb-seq data lane is now closed
*end-to-end* — offline and on the board.

## Why the asymmetry holds

DE for a *specific* unseen pair is dominated by **cell-state / context**, not by a
transferable gene-gene property — only ~41% of Replogle knockdowns produce any
measurable effect, and which pairs respond is context-specific. Direction, given a
response, is a **broad conserved program** (co-regulated genes move together;
housekeeping-up / immune-down). So any signal source — feature, edge, retrieval, or
*real external measurement* — lands on the direction axis, not the DE axis.

## Strategic implications

1. **Stop attacking DE with static/data methods** — features, curated edges,
   retrieval, and external Perturb-seq augmentation all fail it for the same reason.
   The only untried DE crack is **model-based**: token-logprob self-consistency over
   {up,down,none} (renormalized answer-token probabilities), which needs a logprob
   endpoint.
2. **External Perturb-seq data is not a silver bullet — now measured, not just
   predicted.** The PerturbQA→Track A test (above) gives *no* robust DE or direction
   lift on the dual-OOD split; the promising overlap transfer was selection-inflated.
   The lane is closed **end-to-end** — the real-LB read (0.585→0.586, Δ+0.001) confirms
   it on the actual board, not just offline.
3. **The honest model ceiling is ~0.60–0.65** (DIR maxed ~0.65–0.70 + DE pinned
   ~0.55), well below the field's *unverified* tops (**0.693 Track A / 0.752 Track
   B**). Rank 1 by an honest direction model is unlikely; it needs either the
   model-based DE crack or the field's tops sitting on an easier-than-dual-OOD split.

## See also

[[neighbor-retrieval-direction-lever]] · [[curated-edges-fail-de-axis]] ·
[[marginal-de-caps-at-degree]] · [[housekeeping-transfer-hypothesis]] ·
[[track-a-eda]] · [[track-b-abstention-failure]] · [[dir-ceiling-equal-weight-fusion]]
