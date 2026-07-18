---
title: DE is unlearnable on the honest dual-OOD split — a leakage-allowed oracle caps AUROC_de at chance
type: findings
status: measured
cites:
  - findings/direction-transfers-de-doesnt.md
  - findings/marginal-de-caps-at-degree.md
  - findings/curated-edges-fail-de-axis.md
  - findings/llm-self-consistency-fails-de-axis.md
  - findings/contrastive-de-core-assessment.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/track-a-error-structure.md
  - findings/competitor-landscape.md
  - findings/housekeeping-transfer-hypothesis.md
---

[[../home]] | [[../index]]

# DE is unlearnable on the honest dual-OOD split

**The publishable negative result of the project.** For the BioReasoning Challenge
Track A/B rank metric, the differential-expression axis — *does this unseen
`(perturbation, readout-gene)` pair respond at all* — is **not learnable on the
challenge's honest dual-OOD split**. `AUROC_de` sits at chance (≈ 0.50) for every
channel we tried, and — the capstone — **a leakage-allowed oracle that is permitted
to cheat still cannot rank DE above chance** (upper bound **0.555 ± 0.036**). The
sibling axis, *direction* (up vs down given a response), **does** transfer and is the
source of every leaderboard gain we booked. This axis decomposition is the scientific
point: on doubly-disjoint perturbations × genes, one axis is an intrinsic dead end and
the other is a live, improvable signal.

## The capstone — an oracle upper-bound on AUROC_de

Before this probe, "DE is dead" rested on many *learned* channels failing (below).
The obvious objection: maybe our features/models are just weak. The oracle removes
that objection by measuring the **best case any DE model could achieve**, giving the
head signal it is not allowed to have at test time and asking whether even *that*
ranks DE.

**Method** (`analysis/de-ceiling-probe`, PR #62, `scripts/de_ceiling_probe.py`,
fully offline — no endpoint, no Kaggle quota):

1. Build a **leakage-allowed** DE-feature head — deliberately labelled ORACLE, never
   a submission path — from train-forbidden signal: gene identity, per-gene /
   per-perturbation DE-rate (leave-one-out, self excluded, so it measures marginal
   propensity, not per-pair label copy), and full-data marginal statistics.
2. Fit and score `AUROC_de` on the **same dual-OOD `holdout_split`** the real pipeline
   uses (already shown honest — LB↔val gap only +0.02–0.06). An honest DE model can
   only do *worse* than this oracle, so a low oracle score is a hard negative result.
3. Ablate each leaked feature to name which, if any, carries signal.

**Result — the 0.960 in-sample number is a split-artifact, not headroom:**

| Oracle variant | AUROC_de | Read |
|---|---|---|
| Naive full-data LOO oracle | **0.960** | **MIRAGE** — on a dual-OOD split, the LOO DE-rate leaks each val label into its gene/pert-*mates*; unachievable at test, where real test identities are unseen |
| **Honest oracle** (rates derived from TRAIN only) | **0.555 ± 0.036** | ≈ chance — val identities unseen ⇒ every rate channel collapses to the prior 0.500 **by construction** |
| — best single ablated channel | gene_count **0.585** | a **label-free structural count** (rows per gene), *not* a DE mechanism |

The 0.960 → 0.555 collapse is the whole story: the only thing that made DE look
learnable in-sample was **gene-mate label leakage** across the OOD boundary. Remove
it — as any honest test does — and even a cheating oracle lands on the prior. The
lone non-chance residue (gene_count 0.585) is a counting artifact of how rows are
sampled, carrying no biological DE signal. **Verdict: DE is unlearnable-by-design
from identity and marginals on the dual-OOD split.** This confirms, from the ceiling
down, the error-structure EDA that found `AUROC_de` at chance in *every* perturbation
category ([[track-a-error-structure]]).

## The convergent evidence — every attack route is dead

The oracle is the capstone on a stack of independent negative results, each firing a
different attack at the DE axis and missing:

**Curated-edge / proximity / structural channels — ≈ chance (6+ channels)**
([[curated-edges-fail-de-axis]], [[neighbor-retrieval-direction-lever]]):
CollecTRI signed TF-regulon (0.4% coverage), STRING 1-hop edges (1.6%), STRING 2-hop
proximity (0.543), STRING-neighbour label retrieval (0.498), char/prefix family
retrieval (0.502), learned GO model (0.500). The structural reason: the task scores
*arbitrary* pairs, but curated databases assert only a ~1–2% high-confidence slice —
"is this a known edge?" is almost always "no" regardless of true DE.

**Marginal-property channel — capped at STRING degree ~0.536** ([[marginal-de-caps-at-degree]]):
the first *above-chance* DE signal, from per-symbol network connectivity, but it caps
at what STRING degree captures (+0.008 fused) and a second marginal (DepMap
essentiality) is redundant (collinear with degree). The static/data DE route is
exhausted, not merely untried.

**External measured-data / retrieval routes — dead end-to-end, on the real board**
([[direction-transfers-de-doesnt]], [[housekeeping-transfer-hypothesis]]):
- **PerturbQA human-ortholog transfer:** the 242-pair overlap looked like the first
  real DE lever (standalone DE-AUROC 0.722) but was a textbook selection-inflation
  trap — on the honest dual-OOD split the fused lift is +0.0075 (one-seed noise), and
  the real Track A leaderboard read is **Δ+0.001** at 66% coverage.
- **Native mouse-macrophage Traxler KO150 transfer:** real-LB **Δ−0.005**.
- **Structural coverage:** **82 of 96 test perturbations are essential-housekeeping
  genes never screened in any borrowable macrophage perturbation dataset** — coverage
  ≈ 0 *by construction*, so a lookup path cannot exist for most test rows.
- **LINCS ruled out** before any submission — L1000 is human-only; no mouse-macrophage
  perturbation coverage.

  **Rule that fell out of this lane:** gate on the dual-OOD *fusion delta across seeds*,
  never a standalone overlap AUROC — the trap recurred four times (field char-ngram
  0.693→0.552; Track B CV 0.675→LB 0.488; internal marginal-DE overlap; PerturbQA
  overlap 0.722→noise).

**Model-based / LLM routes — ≈ chance** ([[llm-self-consistency-fails-de-axis]],
[[contrastive-de-core-assessment]]): LLM sample-and-vote self-consistency over
{up, down, none} scores **AUROC_de 0.495** (dead chance) while the same samples give
`AUROC_dir 0.571` (learnable); the contrastive CORE-Voting framing scores **0.498**;
gpt-oss-120B chain-of-thought DE calls land ≈ chance (synthpert, 18/51 honest sample).
Both single-pair *and* contrastive LLM-DE are ruled out. This was *predicted* before
the build: LLMs carry a systematic over-DE bias (Yuan 2026 — a representative LLM
predicts "responds" 92% of the time at a 29% true rate), and self-consistency averages
*variance*, not *systematic bias*.

## The contrast that makes it a scientific result — DIRECTION transfers, DE doesn't

The negative result is only interesting because its sibling is *positive*. On the
identical dual-OOD split, the direction axis behaves oppositely
([[direction-transfers-de-doesnt]], [[neighbor-retrieval-direction-lever]]):

| Axis | Honest ceiling | On the real leaderboard |
|---|---|---|
| **DE** (responds at all) | ~0.555 (oracle) ≈ chance | never moved off chance; every external/model route Δ ≈ 0 |
| **Direction** (up vs down) | ~0.65 (neighbour-DIR 0.651 ± 0.047) | **Track A LB 0.586, Track B LB 0.597** — every gain is a direction gain |

**Why the asymmetry holds:** DE for a *specific* unseen pair is dominated by
cell-state / context (only ~41% of Replogle knockdowns produce any measurable effect,
and *which* pairs respond is context-specific — no transferable gene-gene property).
Direction, *given* a response, is a broad conserved program (co-regulated genes move
together; housekeeping-up / immune-down). So any signal source — feature, curated edge,
retrieval, external measurement, or LLM — lands on the *direction* axis, never the DE
axis. The field reproduces this independently: SUMMER/PerturbQA (Wu 2025) scores
direction 4–8 points above DE, and Ahlmann-Eltze 2025 (*Nat. Methods*) finds the only
method that beat every DL/foundation model was a linear model transferring the
*response* across cell lines.

## Strategic implication

The DE lane is **closed end-to-end** — offline, on the honest split, and on the real
board — with the oracle ceiling as the terminal proof: not "we didn't find a channel,"
but "even a cheating oracle can't rank it." No further DE shots are planned. The live
axis of work is **direction** (drive it toward its ~0.60–0.65 honest ceiling) and the
self-improving loop that spends effort there. Any future proposal to attack DE with a
static feature, curated edge, retrieval, external Perturb-seq table, or single-pair LLM
call should cite this page and *not* be re-run — the ceiling, not just the channels,
says no.

## See also

[[direction-transfers-de-doesnt]] · [[marginal-de-caps-at-degree]] ·
[[curated-edges-fail-de-axis]] · [[llm-self-consistency-fails-de-axis]] ·
[[contrastive-de-core-assessment]] · [[neighbor-retrieval-direction-lever]] ·
[[track-a-error-structure]] · [[competitor-landscape]] · [[housekeeping-transfer-hypothesis]]
