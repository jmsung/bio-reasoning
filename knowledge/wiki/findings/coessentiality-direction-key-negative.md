---
title: DepMap co-essentiality is a weaker direction key than STRING (0.547 standalone) — does not beat or add to the 0.651 incumbent
status: measured
cites:
  - findings/neighbor-retrieval-direction-lever.md
  - findings/dir-ceiling-equal-weight-fusion.md
  - findings/direction-transfers-de-doesnt.md
---

# DepMap co-essentiality is a weaker direction key than STRING (0.547 standalone) — does not beat or add to the 0.651 incumbent

[[../home]] | [[../index]]

**Status: measured — `feat/depmap-coessentiality-dir`, 2026-07-17. Clean negative.**

Bottom line: the direction lever is a property of the neighbour **key**
([[neighbor-retrieval-direction-lever]]), so the way to beat neighbour-DIR (STRING key,
DIR-AUROC **0.651**) is a *better* key. We built a **DepMap co-essentiality** key —
genes whose CRISPR knockout fitness effects correlate across DepMap's 1100 cell lines
(Public 23Q4 `CRISPRGeneEffect.csv`, figshare 43346616) are in the same functional
module — and dropped it into the identical label-borrowing direction channel. It is a
**weaker** key, not a better one: standalone DIR-AUROC **0.547 ± 0.048** (barely above
chance) vs STRING 0.651, and fusing it with STRING **lowers** the score (0.637 vs 0.651,
Δ−0.014). A clean negative: no submission spent.

## Measurement (`scripts/coessentiality_dir_eval.py`, 5-seed dual-OOD 0.4/0.4)

Universe 1925 mouse symbols; mouse→human by uppercasing (`Abi1`→`ABI1`), DepMap coverage
**82%** (97% of perts, 78% of genes — the readout `*Rik` genes are the gap). Default key:
top-25 positively-correlated partners per gene, min |r| 0.2, ≥50 co-screened lines.

| | standalone DIR-AUROC (covered) | fused w/ STRING (full DE rows) |
|---|---|---|
| STRING neighbour-DIR (incumbent) | **0.651 ± 0.047** | 0.651 (STRING alone) |
| co-essentiality-DIR | **0.547 ± 0.048** | — |
| STRING ⊕ co-essentiality | — | **0.637 ± 0.043** (Δ **−0.014**) |

Coverage 75% of val rows; Spearman corr vs STRING **+0.21** (some diversity). The STRING
number reproduces the incumbent 0.651 ± 0.047 *exactly*, so the harness is sound.

## Key-tightness sweep — a precision/coverage trade, still sub-incumbent

Tightening the co-essentiality threshold (fewer, higher-confidence edges) raises the
standalone signal but shrinks coverage, and never clears 0.651:

| key (top_k / min_corr) | edges | symbols w/ partner | standalone DIR |
|---|---|---|---|
| 50 / 0.10 | 71155 | 1564 | 0.529 ± 0.043 |
| 25 / 0.20 (default) | 7621 | 1056 | 0.547 ± 0.048 |
| 15 / 0.25 | 2411 | 607 | 0.568 ± 0.029 |
| 10 / 0.30 | 964 | 342 | **0.608 ± 0.042** |

The best (tightest) variant reaches 0.608 standalone and, fused with STRING, gives
**0.655 vs 0.651 (Δ+0.005)** — at the seed-noise floor (σ≈0.04–0.05) and only over a
low-coverage subset. Not a robust win.

## Why co-essentiality is a weaker direction key

Co-essentiality captures *functional-module membership* (do two genes' knockouts have
correlated fitness effects), which is real co-regulation but a **noisier proxy for the
up/down direction tendency** than STRING's physical/annotation co-regulation edges.
It behaves exactly like the other diverse-but-weak arms (embedding-DIR 0.574, GO-DIR
0.595): low correlation earns a fuse *slot*, but a channel too weak standalone cannot
survive equal-weight averaging — the same lesson as [[dir-ceiling-equal-weight-fusion]].
Two labeled-pair *graph* keys (STRING, GO) both carry direction; a *dependency-correlation*
key carries much less. The "better key" search is not exhausted, but co-essentiality is
ruled out.

## Implications

1. **Co-essentiality does not open a new DIR lane.** The 0.651 STRING neighbour key
   remains the single best DIR channel; no new signal to fuse. Consistent with the
   ~0.65 direction ceiling ([[dir-ceiling-equal-weight-fusion]]).
2. **Reusable machinery landed.** `bio_reasoning.features.coessentiality` builds a
   drop-in neighbour graph (`symbol → co-essential partners`) from any DepMap gene-effect
   matrix — available if a future *weighted* combiner wants a diverse low-corr arm, but
   the ceiling finding says the weak arms don't lift.
3. **Decision:** clean negative — do **not** submit. The 401 MB gene-effect matrix and
   partner cache are gitignored (local only); the feature + eval + this finding are the
   durable output.
