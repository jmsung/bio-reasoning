---
title: Tahoe-100M adds nothing to Track A — 3% drug-MoA coverage caps it; even a perfect oracle is seed noise
type: findings
status: measured
cites:
  - source/2025-zhang-tahoe-100m.md
  - findings/direction-transfers-de-doesnt.md
  - findings/de-unlearnable-oracle-ceiling.md
  - findings/housekeeping-transfer-hypothesis.md
  - findings/neighbor-retrieval-direction-lever.md
---

[[../home]] | [[../index]]

# Tahoe-100M adds nothing to Track A

**Status: measured — `research/tahoe-100m-transfer`, 2026-07-18.** Tahoe-100M was the one
untried *allowed* external dataset. It is a **feasibility-bounded clean negative**: the only
leak-free channel it can build covers **3.1% of Track A perts**, and even a **perfect,
leakage-allowed oracle** on that 3% lifts the dual-OOD mean-AUROC by only **+0.0079 ± 0.0030**
— an *upper bound* that already sits in the seed-noise band, so the real (double-mismatched)
channel cannot clear the +0.005 bar. This is the [[direction-transfers-de-doesnt]] /
[[de-unlearnable-oracle-ceiling]] wall confirmed for a third external source, and it needed
**no bulk download** (the 100M-cell matrix and the ~92 GB pseudobulk DE were never pulled).

## The honest prior (stated, then tested)

Tahoe-100M is a ~100M-cell **drug-perturbation** atlas: ~1,100 small molecules × 50 **cancer**
cell lines ([[2025-zhang-tahoe-100m]]). Track A is **genetic CRISPRi knockdown** in **mouse
macrophages**. So Tahoe is a **double modality mismatch** — drug inhibition ≠ genetic knockdown,
cancer lines ≠ primary macrophages — the same class of gap that made native-mouse Traxler KO150
transfer null (Δ−0.005) and PerturbQA transfer null. The prior was LOW; measured anyway because
it is allowed data and was untried.

## What is even accessible (feasibility — data side: OK)

The raw 100M-cell matrix is not needed. Tahoe ships derived metadata cheaply on HuggingFace:
`drug_metadata.parquet` (~40 KB — drug → target/MoA), and a precomputed
`pseudobulk_differential_expression` (DESeq2 `log2FoldChange`/`padj` per drug × cell line),
**partitioned one drug per shard** (1026 shards ≈ 92 GB total). So a drug-MoA channel is
*buildable* without the cell matrix — the data side is not the blocker.

## The only leak-free channel, and why it can't matter (feasibility — mapping side: blocked)

The only way Tahoe touches our `(pert_gene X, readout_gene Y) → {up, down, none}` task is the
**drug-MoA channel**: a Tahoe drug that *inhibits* X proxies "knocking down X", so Tahoe's
drug-induced DE of Y proxies the (X → Y) response. A pert X is scorable **iff some Tahoe drug
targets X**. Measured overlap (`scripts/tahoe_transfer_probe.py`, upper-cased ortholog match):

| | value |
|---|---|
| Tahoe drug-target genes (264 drugs) | 280 |
| Track A perts covered (train) | **12 / 386 (3.1%)** — Arpc2, Hdac3, Hsp90ab1, Ikzf1, Jak1, Kras, Mapk14, Mapkapk2, Mtor, Myc, Tyk2, Xpo1 |
| Track A **test** perts covered | **3 / 96 (3.1%)** — Map3k8, Nfkb1, Syk |
| dual-OOD val rows covered / seed | ~37–43 / ~1,200 (**~3%**) |

The mechanism is structural: our CRISPRi panel is dominated by **housekeeping / structural /
chromatin** genes (Arpc2/3/4, Actl6a, ribosomal, Atp6v*, Mediator, splicing) that have **no
selective small-molecule inhibitor** in Tahoe's oncology drug set — only the ~12 druggable
kinase/mTOR/HDAC/XPO1-type targets overlap. Coverage cannot be engineered up; it is a property
of the two panels.

**Cell-context mismatch is total, not partial.** [[housekeeping-transfer-hypothesis]] flagged
"weight myeloid-lineage Tahoe lines most heavily" as a lead. Checking `cell_line_metadata.parquet`
closes it: Tahoe's panel is **entirely solid-tumor** (Lung 27, Bowel 25, Pancreas 11, Skin 10,
Breast 7, …) with **zero** myeloid / monocytic / hematopoietic lines (no THP-1, U937, HL-60,
K562). There is no macrophage-adjacent context in Tahoe to up-weight — the mismatch is complete,
not a matter of line selection.

## The measurement — a perfect-oracle upper bound (no download needed)

The team's rule is "gate on the **dual-OOD fusion delta**, never a standalone overlap AUROC"
(the selection-inflation trap, [[direction-transfers-de-doesnt]]). Rather than download shards
to build the *real* (noisy, mismatched) channel, we measured the **best case any Tahoe drug-MoA
channel could ever reach**: a leakage-allowed oracle that emits the **true** DE and **true**
direction on every covered row and `NaN` elsewhere, fused into the incumbent (two-stage GO×DIR
+ neighbour-DIR), on the honest dual-OOD `holdout_split`, 5 seeds. Mirrors the
[[de-unlearnable-oracle-ceiling]] method: a low ceiling for a *cheating* channel is a hard
negative for the real one.

| seed | val covered | base mean | +perfect-oracle mean | Δmean |
|---|---|---|---|---|
| 0 | 37/1276 | 0.566 | 0.573 | +0.0070 |
| 1 | 36/1155 | 0.592 | 0.596 | +0.0041 |
| 2 | 37/1135 | 0.587 | 0.594 | +0.0068 |
| 3 | 42/1127 | 0.625 | 0.633 | +0.0087 |
| 4 | 43/1309 | 0.548 | 0.561 | +0.0131 |
| **mean** | | | | **+0.0079 ± 0.0030** |

Incumbent DIR sits at 0.56–0.72 across seeds (the [[neighbor-retrieval-direction-lever]] 0.651
stack); the oracle barely nudges it because it only touches ~3% of rows. **+0.0079 is an
unachievable ceiling** — it hands the channel the answer key. The real drug-MoA channel does
strictly worse (drug ≠ knockdown, cancer ≠ macrophage, plus the overlap selection inflation
that collapsed PerturbQA's 0.72 to ~0.53 on OOD).

## Verdict — clean negative, lane not opened

**Do not open the Tahoe lane.** The coverage ceiling (3% of perts) structurally caps any lift to
seed noise, and even a perfect oracle (+0.0079) lands at the +0.005 bar that a *real* channel
must clear — so the real channel is below it. This is strictly weaker than the
already-closed **PerturbQA** lane, which had **22× the coverage** (66%), **native human CRISPRi**
(no drug≠KD or cancer≠macrophage gap), the exact task format, and *still* gave +0.0075 OOD-val
(one-seed noise, CFA 1/3) and a confirmed **real-LB Δ+0.001** (`docs/perturb-seq-lane-decision.md`).
Tahoe adds two more mismatches at a twentieth of the coverage; it cannot beat a lane that already
scored ~0 on the real board. No Track A submission is generated. The ~92 GB pseudobulk pull is
**not** justified — its only use would be a standalone overlap AUROC, which the team's own rule
forbids gating on.

**What would change this:** nothing on offer. Tahoe reinforces (at best) **direction**, already
~0.65-capped ([[dir-ceiling-equal-weight-fusion]]), and cannot touch the **DE** axis that bounds
the score (oracle wall 0.555, [[de-unlearnable-oracle-ceiling]]). The higher-EV rank-1 bet
remains the model-based DE crack (token-logprob self-consistency), not more perturbation data.

## Reproduce

```
uv run --with pyarrow python scripts/fetch_tahoe_drug_targets.py   # ~40 KB drug metadata only
uv run python scripts/tahoe_transfer_probe.py                      # coverage + perfect-oracle bound
```

Channel + oracle: `bio_reasoning.features.tahoe_transfer`. Fully offline after the metadata fetch.

## See also

[[direction-transfers-de-doesnt]] · [[de-unlearnable-oracle-ceiling]] ·
[[housekeeping-transfer-hypothesis]] (the transferable-slice lead this closes for Tahoe) ·
[[neighbor-retrieval-direction-lever]] · [[2025-zhang-tahoe-100m]]
