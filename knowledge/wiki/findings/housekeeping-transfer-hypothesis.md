---
title: Housekeeping-perturbation transferability — augmentation lead
cites:
  - findings/track-a-eda.md
  - source/2025-zhang-tahoe-100m.md
  - source/2025-wu-perturbqa.md
---

# Housekeeping-perturbation transferability (augmentation lead)

**Hypothesis (Joo):** perturbations of *housekeeping* genes produce responses
that are largely **cell-type-invariant**, whereas immune / lineage-specific
perturbations are context-dependent. If true, the housekeeping subset is the
most **transferable** slice for cross-dataset augmentation (e.g. borrowing from
Tahoe-100M or PerturbQA's CRISPRi datasets into our macrophage Track A task),
despite the domain gaps.

## Why we think this

- Our Track A EDA found perturbation *category* drives direction: housekeeping
  perturbations skew targets **up** (~70%), immune perturbations skew **down**
  (~60%) — i.e. the housekeeping effect looks like a broad, possibly generic
  program ([[track-a-eda]]).
- Biological prior: housekeeping machinery (translation, proteasome, splicing,
  cell cycle) is shared across cell types, so knocking it down should perturb
  core processes similarly everywhere; immune / lineage programs are
  context-specific.

## Testable predictions

1. On our Track A data, housekeeping-perturbation rows show more consistent
   direction across target modules than immune-perturbation rows (lower entropy).
2. Across datasets (Tahoe, PerturbQA's 5 CRISPRi sets), housekeeping-gene
   perturbation signatures correlate more across cell types than immune-gene ones.
3. Augmenting with only the housekeeping-perturbation slice of external data
   improves Track A more than augmenting with the immune-perturbation slice.

## Implications for augmentation (roadmap #2)

- Prefer the **housekeeping subset** of external perturbation data for
  augmentation / pretraining.
- Weight **myeloid-lineage cell lines** (closest to macrophages) most heavily
  when borrowing from cancer-line atlases like Tahoe — *if* such lines exist
  there (to verify: Tahoe `cell_line_metadata`).
- Caveat: Tahoe is chemical perturbation (drugs), not genetic; mapping
  drug → gene-knockdown effects is itself an open problem
  ([[2025-zhang-tahoe-100m]]).

## Next steps

- [ ] Test prediction 1 on Track A data (we have it locally).
- [x] Enumerate Tahoe cell lines; flag myeloid / monocytic lines — **done, none exist.**
  Tahoe's panel is entirely solid-tumor (Lung/Bowel/Pancreas/Skin/Breast/…); **zero** myeloid
  lines, so there is no macrophage-adjacent context to up-weight. Combined with the drug-MoA
  channel covering only 3.1% of Track A perts, the Tahoe augmentation lead is a
  **feasibility-bounded clean negative** — see [[tahoe-100m-transfer]].
