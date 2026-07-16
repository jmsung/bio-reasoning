# BioReasoning Challenge 2026 — Progress Report

*Updated as branches land — the merge workflow proposes report-worthy additions per PR.*
*Last updated: 2026-07-16.*

## Goal

Predict how a genetic perturbation reshapes a target gene's expression in macrophages —
a 3-class call (`up` / `down` / `none`) for each `(perturbation, target-gene)` pair — and
test whether LLMs and agentic systems can serve as computational engines for it. The test
split is **dual-OOD**: perturbations *and* target genes are both disjoint from train, so
memorization is worthless and only transferable biological reasoning generalizes.

**Metric:** `mean(AUROC_de, AUROC_dir)` — predictions are graded (`prediction_up`,
`prediction_down`). `AUROC_de` ranks none-vs-DE by `up + down`; `AUROC_dir` ranks up-vs-down
by `up / (up + down)` over DE-positive rows. Accuracy does **not** apply.

## Where we stand

| Approach | Method | Score | Notes |
|---|---|---|---|
| Majority class | predict `none` (55.3%) | ≈ 0.553 | reference only (metric is AUROC, not accuracy) |
| **Track A — evidence prior** | functional-category direction prior (no LLM) | **0.529** (Kaggle LB; CV 0.534) | our real floor; ~0 CV↔LB gap; **direction carries the signal, DE-vs-none is nearly flat** |
| **Track B — agent harness (v1)** | multi-agent tool-use (direction-prior + GO-evidence tools) on `gpt-oss-120b` | local CV **0.675** → LB **0.488** | **did not transfer** — the agent abstained on ~72% of rows, submitting `0/0`; ties collapse the rank metric to ~random. Local CV was inflated ~0.19 over LB. |
| **Track B — floor-to-prior (v2)** | v1 predictions, every `(0,0)` tie floored to the graded prior (no re-inference) | **0.568** (Kaggle LB) | **first Track B above the floor** — removing the 72% ties recovers the 0.529 prior; the 506 agent-signal rows add **+0.039** on top. Reasoning helps once it can't delete the prior. |
| **Track A — two-stage GO (v2)** | learned `P(DE)·P(up\|DE)` heads over GO:BP term features for the perturbation *and* the target gene | **0.561** (Kaggle LB; OOD-val ~0.56) | **new Track A best** (+0.032 over the 0.529 prior); GO functional features carry it — our char-ngram / gene-name string features scored at chance (but see caveat: the public field reaches ~0.693 with gene-name n-grams, so name structure *is* exploitable — we haven't captured it) |
| **Track B — DIR-blend (v3)** | rank-blends the two-stage model's direction into the floored submission (w=0.7) | **0.578** (Kaggle LB; OOD-val 0.571) | **new Track B best** (+0.010 over the 0.568 floor-to-prior champion); the direction signal generalized to the full test set |
| Public leaderboard (top) | — | A ≈ 0.693 / B ≈ 0.752 | on the same AUROC scale — **we remain well below the field** |

**Two findings drive the plan:**
1. **The direction axis carries the signal; DE-vs-none is nearly flat** — split optimization
   effort across the two sub-metrics, don't chase the aggregate.
2. **Local CV badly over-states leaderboard performance** (Track B: 0.675 CV → 0.488 LB). The
   agent's over-abstention (emitting `0/0`) deletes the prior's signal and creates rank ties.
   The fix is twofold: **never emit `0/0`** (fall back to the direction prior on every would-be
   abstention, guaranteeing ≥ the 0.529 floor), and **score, don't label** (emit a continuous
   DE-likelihood — only order matters for AUROC). And measurement must move onto a **dual-OOD
   validation split** that reproduces the real train/test disjointness, so CV stops lying.

## Update (feat/ood-val-split — landed)

The dual-OOD validation split now exists — `holdout_split()` (perturbations *and* target
genes disjoint; val ~1,276 rows / train ~2,646) with a single `evaluate()` /
`evaluate_on_split()` entry point. Honest baselines re-scored on it: no-signal **0.500**,
evidence prior **0.533** (matches the 0.534 CV / 0.529 LB — the prior is CV-honest). We also
pinned *why* a naive CV inflates: a **fixed** predictor cannot leak across CV schemes, but a
**fold-fitted** one does — a per-pert memorizing baseline scores **0.552** under naive
random-row CV and collapses to **0.500** under dual-OOD. This is the mechanism behind Track B's
0.675 CV → 0.488 LB, and confirms the dual-OOD split (not naive CV) is the honest fitness
surface for anything trained or tuned.

## Update (floor-to-prior — landed)

The "never emit `0/0`" fix is in and measured. `floor_to_prior` replaces any `(0,0)`
tie with the perturbation's graded category prior; applied to the PR #13 submission
(1,307/1,813 = 72% of rows floored, 0 ties remain) it scores **Kaggle LB 0.568** — the
first Track B result above the 0.529 prior floor (+0.039), and +0.080 over the raw
agent's 0.488. It confirms the diagnosis: the prior is recovered by removing the ties,
and the agent's 506 signal-carrying rows add real lift on top. Full LB ladder now
measured: **hard A/B/C 0.507 → graded-but-over-abstaining 0.488 → floor-to-prior 0.568**.
**Confirmed on the honest split:** re-measured on the dual-OOD val (`--split holdout`,
1,276 rows) → mean **0.564** (de 0.557, dir 0.570) vs prior 0.533 (+0.031). The
**LB ↔ OOD-val gap is just 0.004**, so the lift is real, not a test-set artifact — and
the CV↔LB inflation that sank the raw agent (0.675→0.488) is gone once ties are floored.
Blend (`α·agent + (1−α)·prior`) was then tuned on this OOD-val surface and gave **no
gain** — best α=0.9 → 0.5654 vs floor-to-prior 0.5647 (noise). The agent's signal-rows
are already well-calibrated, so the Track B ceiling is set by **evidence quality**
(prior + tools), not post-hoc mixing. Real next levers: better knowledge tools and
scoring-not-labeling (continuous DE-likelihood).

## Update (kb/competitor-landscape — landed)

A survey of the public field (6 vote-leading Kaggle notebooks across A/B/C + live
leaderboards A **0.693** / B **0.752** / C **0.693**) reframes the competition:
**every public solution predicts from gene-name character n-grams with classical ML and
fakes the LLM scaffolding** — the "bioreasoning" framing is unenforced by the metric. The
two transferable wins are the **two-stage DE×DIR decomposition** (model `P(DE)` and
`P(up|DE)` separately, recombine — aligns to the metric's two AUROCs) and **char /
gene-family prefix structure** (the zero-overlap bridge). The lane nobody occupies — where
LLM+tools can genuinely differentiate — is **real external gene knowledge** (GO / STRING /
pathway) fed to the agent, plus **TabPFN over functional features** (SOTA per Palla 2026,
unused by the field). Spawned two priorities: the two-stage decomposition and
functional-knowledge Track B tools.

## Update (feat/two-stage-de-dir + test/verify-two-stage-lb — landed)

The two-stage **DE×DIR decomposition** from the competitor survey is built and
**verified on the leaderboard** — two new public-LB bests, both confirmed by the
dual-OOD split.

| Track | submission | OOD-val | **public LB** | baseline | Δ | gap |
|---|---|---|---|---|---|---|
| A | two-stage GO-term | ~0.56 | **0.561** | prior 0.529 | **+0.032** | ~0.00 |
| B | DIR-blend (w=0.7) | 0.571 | **0.578** | floor-to-prior 0.568 | **+0.010** | +0.007 (LB > OOD-val) |

**Track A** learns `P(DE)` and `P(up|DE)` heads separately over GO:BP term features
for *both* the perturbation and the **target gene** — the axis the direction prior
ignores — and recombines to the metric's two AUROCs. The functional features carry
it: our char-ngram / gene-name string features scored at chance on the dual-OOD
split. **Caveat worth chasing:** the public field reaches ~0.693 with gene-name
n-grams + classical ML, so name structure *is* strongly predictive — our n-gram
implementation simply failed to extract it, and at 0.561 we remain well below the
field. GO terms are a *complementary* functional lever, not a replacement for the
string signal we're still leaving on the table. **Track B** rank-blends the
two-stage model's direction into the floored champion (w=0.7), +0.010 on top of
floor-to-prior — a *different* lever from the earlier α·agent+prior blend (which
was exhausted); mixing in an orthogonal learned direction still lifts.

**The dual-OOD split was predictive for both.** Track A LB 0.561 ≈ OOD-val ~0.56
(gap ~0.00); Track B LB 0.578 *exceeded* OOD-val 0.571, so the single-split lift was
real, not seed noise (though σ≈0.05–0.06 on this split keeps the exact figures soft).
The CV-inflation trap that sank the raw agent (0.675→0.488) stayed absent — the
honest split now reliably predicts the leaderboard.

## Update (feat/trial-loop — landed)

An OOD-val **optimization harness** now drives both tracks on one leak-free fitness
surface: `scripts/trial_loop.py` proposes variants, scores each on `holdout_split` with
`evaluate` (mean AUROC), and archives a leaderboard. Track A (prompt) and Track B (agent)
share one injected `RowPredictor` seam, so "does the agent beat the prompt?" is a direct
control. The Track B agent runner was extracted from `track_b_agentic.py`'s `main()` and its
graded→A/B/C→prior abstention chain (the LB-0.488 bug) is now unit-tested.

Full 1,276-row OOD-val sweep (`gpt-oss-120b`):

| variant | OOD-val mean | note |
|---|---|---|
| zero-shot prompt (`fs0`) | **0.571** | Track A prompt ceiling |
| agent (`jsagent`) | 0.557 | does **not** beat zero-shot |
| few-shot — random / GO-retrieval | 0.53–0.55 | **few-shot hurts on dual-OOD** |
| evidence prior (floor) | 0.533 | reference |

Three findings: (1) **few-shot hurts** — random *and* GO-category-retrieval exemplars alike;
on a dual-OOD split the exemplars aren't analogous to unseen queries, so they add noise, not
signal. Zero-shot is the prompt ceiling. (2) The **vanilla agent doesn't beat zero-shot** —
it clears the floor and beats few-shot, but at ~$2.5/run vs ~$0.08 it doesn't yet earn its
cost. (3) These re-confirm on the harness that **AUROC_de ~0.55 (near chance) is the
bottleneck**; direction (~0.58) is fine. The next lever is a real DE-detector for unseen
`(pert, gene)` pairs — a vetted recon plan points to a **CollecTRI signed TF-regulon feature**
(regulon membership = DE, edge sign under CRISPRi = direction). These were dev variants, not
submitted — all ≤ the live LB 0.578.

## Update (feat/de-detector-fuse-harness — landed)

The DE-detector lever the trial-loop update pointed at was built and **measured before
submission — the coverage gate killed it**. Two artifacts landed:

- **`fuse()` rank-fusion harness + CFA diversity gate** (`src/bio_reasoning/fuse/`) — a
  reusable way to combine DE score channels by rank (scale-free, deterministic) behind a
  **Correlation-Filtered Admission** gate that admits a channel only if it is both strong
  (standalone DE-AUROC ≥ threshold) *and* diverse (low Spearman vs the current fusion). The
  offline validator every future DE channel runs through before it can cost a submission.
- **CollecTRI signed TF-regulon feature** (`src/bio_reasoning/features/tf_regulon.py`) —
  identity-free per-`(pert, gene)` DE edge indicator + signed direction under CRISPRi polarity.

The plan named regulon-edge coverage on OOD-val as the go/no-go. Measured (dual-OOD val,
1,276 rows; CollecTRI mouse = 43,226 edges / 1,165 TFs):

| metric | value |
|---|---|
| TF-pert coverage | 12.1% |
| regulon-edge rows | **0.4%** (~5 rows) |
| edge \| TF-pert | 3.2% |

At 0.4% direct-edge coverage the channel moves ~5 of 1,276 rows → no DE lift, so it never
reached fusion. **Finding: curated direct-edge networks are structurally too sparse for the DE
axis here** — the task scores *arbitrary* `(pert, gene)` pairs, and a curated DB stores only
~1–2% of them as direct edges. The DE bet moves to model-based / dense channels
(neighbor-retrieval, gene embeddings, network diffusion), all validated through the new harness.

## Approach

1. **Honest fitness signal first** — a dual-OOD validation split (perturbations + genes
   disjoint from the train portion) with a single `evaluate() → {auroc_de, auroc_dir, mean}`
   entry point. Every baseline (including the agent harness's 0.675) is re-scored here; a naive
   CV inflates.
2. **A self-improving trial loop** — a single-problem loop that proposes a candidate
   (a Track A prompt, then a Track B agent config), scores it on the OOD split, keeps per-trial
   execution traces, reflects on stagnation, and compounds an archive of what works. Fixed model
   throughout: `gpt-oss-120b` via a hosted OpenAI-compatible endpoint (leaderboard-legal — it is
   the competition's fixed model).
3. **Two tracks off one loop** — Track A optimizes the prompt of the fixed LLM; Track B
   optimizes tools + orchestration around it. Track B must beat the Track A result to justify
   its cost.
4. **Submission discipline** — spend the daily Kaggle budget only on candidates that beat the
   best-on-validation; track the public-LB − validation gap; select finals before the deadline.

## Plan (to 2026-07-22)

- **Done:** the dual-OOD validation split (the loop's fitness signal) is built — it closes
  the CV↔LB gap that inflated Track B by ~0.19. Honest floor on it: prior **0.533**.
- **First Track B fix (cheapest, highest value):** never emit `0/0` — fall back to the direction
  prior on every would-be abstention. This alone should recover ≥ 0.529 (the bar is "stop
  deleting the prior"). Then blend `α·agent + (1−α)·prior` (never-worse-than-prior by
  construction, α tuned on the OOD split).
- **Then:** stand up the trial loop against the OOD split; optimize Track A prompts, and evolve
  Track B toward **scoring, not labeling** (continuous DE-likelihood, killing the tie-mass
  failure at the root).
- **Close:** submission discipline → final selection.

## Risks & mitigations

- **Model access** → mitigated: the fixed `gpt-oss-120b` is reachable now via a hosted
  OpenAI-compatible endpoint; a local GPU box is a scale/backup path.
- **Validation ≠ leaderboard** → *realized* on Track B (0.675 CV → 0.488 LB). Mitigated going
  forward by the dual-OOD split that mirrors the real test structure; we track the LB−val gap on
  every submission and never trust CV alone.
- **Agent over-abstention** → *realized* (72% of rows `0/0` collapsed the LB to ~random).
  Addressed by a hard "never emit `0/0`, fall back to the prior" rule, a prior-blend floor, and a
  scoring-not-labeling reframe — validated on the OOD split.
