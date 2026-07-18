---
title: The 0.586→0.693 Track A gap is not a reachable signal — transductive tricks are ≈0 on OOD; the public recipe doesn't reproduce
type: findings
status: measured
cites:
  - findings/competitor-landscape.md
  - findings/de-unlearnable-on-dual-ood.md
  - findings/direction-transfers-de-doesnt.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/track-a-eda.md
---

[[../home]] | [[../index]]

# The 0.586→0.693 Track A gap is not a reachable signal

**Status: measured (2026-07-17, `analysis/field-gap-probe`,
`scripts/field_gap_probe.py`). Offline, no-spend.**

Our honest dual-OOD Track A ceiling is **~0.586** real-LB (neighbour-DIR fusion;
[[neighbor-retrieval-direction-lever]]). The public leaderboard top is **~0.693**.
This probe asks whether the +0.107 gap is (a) **transductive tricks** that inflate
on this test, (b) an **easier real test**, or (c) **unreproducible/inflated** public
scores. Verdict: **(c), with a small already-priced-in (b); (a) contributes ≈0.000.**

## Bottom line

The two transductive tricks flagged in the public notebooks
([[competitor-landscape]]) — avikdas's **train+test-union char vocab** and
jek1wantaufik's **id-in-text** — move mean-AUROC by **≈0.000** on an honest OOD
split. They are *mechanically incapable* of lifting an OOD score, and the real test
**is** exact-identity OOD, so they cannot inflate the leaders' real-LB either. The
gap is not a trick we're failing to copy; the disclosed public recipe simply does
not reproduce 0.693 (a faithful char-ngram two-stage got real-LB **0.552**, probe
#39). Decision A (accept the honest ceiling + bank the negative result) is
**reinforced** — there is no measurable reachable signal in the public field.

## Measurement 1 — transductive-vocab delta ≈ 0 (5-seed dual-OOD holdout)

Char-ngram two-stage (`P(DE)·P(up|DE)`, LogisticRegression heads) built four ways;
heads always fit on **train** labels, val labels only score. Mean±sd over 5 seeds:

| config | AUROC_de | AUROC_dir | mean | Δ vs honest |
|---|---|---|---|---|
| honest (train vocab) | 0.5112 | 0.5331 | **0.5222** ± 0.021 | — |
| transductive (train+val vocab) | 0.5165 | 0.5273 | 0.5219 ± 0.020 | **−0.0002** |
| honest + id-in-text | 0.5106 | 0.5377 | 0.5241 ± 0.019 | +0.0020 |
| transductive + id-in-text | 0.5166 | 0.5310 | 0.5238 ± 0.018 | +0.0016 |

Every delta is inside seed noise (sd ≈ 0.02). **Mechanism:** a val-only n-gram gets
its own vocabulary column, but that column is **all-zero across the train design
matrix**, so a train-fit head (linear, NB, or tree) assigns it ~0 weight — the
union vocab cannot change OOD predictions. id-in-text is likewise inert on OOD:
the id string (`pert_gene`) shares no exact match across the zero-overlap split, and
its char n-grams are near-redundant with the pert+gene axes. **These tricks are
leaderboard-plumbing, not signal — and here they don't even plumb.**

## Measurement 2 — how OOD is the real test? (reconciles probe #39)

Real `test.csv` vs full `train.csv`: **0.0% exact identity overlap** on *both* the
pert and gene axes (confirms the doubly-disjoint design, [[track-a-eda]]) — but
heavy **family/prefix** structure the char model legitimately rides:

| axis | prefix-2 | prefix-3 | family-stem | exact | nearest-train trigram-Jaccard >0.3 |
|---|---|---|---|---|---|
| real test — gene | 93.2% | 61.8% | 49.8% | 0.0% | 42.5% (median J 0.286) |
| real test — pert | 74.0% | 51.0% | 44.8% | 0.0% | 35.4% (median J 0.250) |
| **our holdout — gene** | 77.1% | 40.7% | 35.2% | 0.0% | **22.9%** (median J 0.182) |

The real test is **~2× more string-transferable** than our dual-OOD holdout (42.5%
vs 22.9% of genes have a close train neighbour). That is exactly the effect probe
#39 measured as a **+0.02–0.06** LB↔OOD-val gap (char-ngram real-LB 0.552 vs
OOD-val 0.492–0.531): our split holds families out a touch more aggressively, so our
*offline* number understates the *real-LB* number by a little. **But this is already
priced in** — our 0.586 ceiling is itself a real-LB number, measured on that same
easier test. The 0.586↔0.693 gap is between two scores on the **identical** test
set, so "easier real test" cannot explain it.

## Verdict — (c), reinforcing decision A

- **(a) transductive tricks: ruled out, ≈0.000.** Mechanically inert on OOD; the
  real test is OOD; measured Δ within noise.
- **(b) easier real test: real but already banked (~+0.02–0.06).** Explains only the
  gap between our *offline val* and our *real-LB*, both already below 0.586. It does
  **not** re-open the 0.586↔0.693 gap (same test set).
- **(c) unreproducible/inflated: the residual, ~+0.10.** The 6 public notebooks
  print **no** scores ([[competitor-landscape]]); a faithful char-ngram two-stage
  reaches real-LB **0.552** (probe #39), *below* our 0.585. Either the leaders use
  substantially more engineered features than a standard char-TFIDF (undisclosed,
  hence not a "trick we're missing"), or the 0.693 is inflated/misattributed.

**No reachable public signal is being left on the table.** The only paths that could
move our real-LB are (i) better *own* string/family engineering — but our
neighbour-fusion 0.585 already beats naive char 0.552, so the marginal room is thin —
or (ii) the untaken **external-knowledge-as-LLM-retrieval** lane (cf. cellshift.bio's
Track B 0.752, [[competitor-landscape]]), which is a new bet, not a gap-closer.
This validates banking the honest ceiling. See also [[de-unlearnable-on-dual-ood]]:
the DE axis is unlearnable on honest OOD, which caps the reachable mean regardless.

## Reproduce

```bash
uv run --group eval python scripts/field_gap_probe.py
```
