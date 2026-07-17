---
title: Direction transfers, DE doesn't — the axis-asymmetry principle
type: findings
status: draft
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
2. **External Perturb-seq data won't be a silver bullet** — it reinforces direction
   (already our strong axis → bounded marginal EV), not DE (see the
   `mb/notes/perturb-seq-data-lane.md` full investigation).
3. **The honest model ceiling is ~0.60–0.65** (DIR maxed ~0.65–0.70 + DE pinned
   ~0.55), ~0.10 below the field's *unverified* 0.75. Rank 1 by an honest direction
   model is unlikely; it needs either the model-based DE crack or the field's tops
   sitting on an easier-than-dual-OOD split.

## See also

[[neighbor-retrieval-direction-lever]] · [[curated-edges-fail-de-axis]] ·
[[housekeeping-transfer-hypothesis]] · [[track-a-eda]] · [[track-b-abstention-failure]]
