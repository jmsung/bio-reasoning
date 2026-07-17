# BioReasoning Challenge 2026 — Progress Report

*Updated as branches land — the merge workflow proposes report-worthy additions per PR.*
*Last updated: 2026-07-17.*

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
| **Track B — DIR-blend (v3)** | rank-blends the two-stage model's direction into the floored submission (w=0.7) | **0.578** (Kaggle LB; OOD-val 0.571) | new Track B best (+0.010 over the 0.568 floor-to-prior champion); the direction signal generalized to the full test set |
| **Track A — neighbour-DIR fusion (v4)** | fuse the neighbour-retrieval direction (STRING-neighbour label borrowing, leak-free) into the two-stage GO submission via `fuse()`; DE kept, direction blended | **0.585** (Kaggle LB) | **new Track A + overall best** (+0.024 over two-stage 0.561, past the 0.578 Track B); DE stayed ~chance across 4 channel families — the retrieval signal lives in *direction* |
| **Track B — neighbour-DIR fusion (v5)** | fuse the same neighbour-retrieval direction into the floored Track B submission via `fuse_neighbour_direction` — the #28 lever, different base | **0.597** (Kaggle LB; OOD-val 0.5916) | **new Track B best** (+0.019 over the 0.578 DIR-blend); direction 0.570→0.624 at 98% coverage, DE unchanged — the 0.578 blend had *not* already captured the neighbour direction; LB came in +0.005 above OOD-val |
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

## Update (feat/tabpfn-functional-features — landed)

Closed the "TabPFN over functional features" lane the competitor survey flagged
as open (Palla 2026) — for the *combiner* framing. Trained TabPFN as a learned
nonlinear combiner over the three DIRECTION channels (GO / neighbour / embedding)
on the dual-OOD holdout, leak-free (out-of-fold channel features, cross-fit over
doubly-disjoint inner folds).

**DIR-AUROC 0.613 ± 0.039 (5 seeds) < neighbour-DIR 0.651 / equal-weight fusion
0.642** on identical val rows — does **not** clear the ~0.65 hand-fused ceiling
(−0.037). A nonlinear learned head over the same saturated channels underperforms
the direct neighbour lookup; corroborates #37/#38 (direction saturates,
corr-diversity ≠ marginal lift). Goal 3 (submission) gated on clearing → skipped;
neighbour-DIR LB 0.585 stands. Nothing submitted.

**Strategic read:** the ~0.65 DIR ceiling is a **data/feature ceiling, not a
combiner-form ceiling**. TabPFN derivatives (TabICLv2 / TabDPT / TabForestPFN) are
near-zero EV as combiner swaps; the open TabPFN lane is framing #2 — a tabular FM
as a **primary predictor over rich pair features**, still untried. Full finding:
[`knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md`](../knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md).

## Update (test/real-test-difficulty-probe — landed)

A **measurement-only probe** answering the question that gates the whole rank-1
plan: *is the field's 0.693 real, or is our dual-OOD split simply too hard?* We
submitted the one model class we'd never put on the real board — a **proper
char-ngram TF-IDF two-stage** Track A model (the field's reported recipe) — and
read the LB↔offline gap.

**Kaggle Track A LB 0.552** (2026-07-17) vs its own **OOD-val 0.492** (holdout
seed 0) / **0.531** (5-fold) — an LB↔offline gap of just **+0.02 to +0.06**. Two
conclusions, both strategy-setting:

1. **Our dual-OOD split is roughly honest** (mildly conservative), *not* the
   0.17 inflation that "sandbagging" would require. The real test rewards string
   identity a touch more than our hold-out-both-axes split predicts, but nowhere
   near enough to explain 0.693. The honest **~0.60–0.65 mean-AUROC ceiling
   stands** — >0.8 is not reachable on a true version of this task, so
   direction-first holds and the only DE hope left is model-based (logprob,
   Bing-gated).
2. **The field's "char-ngram → 0.693" does NOT reproduce.** A correct
   implementation reaches only 0.552 on the real board — *below* our GO two-stage
   (0.561) and far below our neighbour-fusion best (0.585). Either the leaders'
   string features are substantially more engineered than a standard char-TFIDF,
   or the printed 0.693 is inflated/misattributed (the surveyed notebooks print
   no scores).

Negative result — a probe, **not a new best** (LB 0.585 stands; nothing
submitted for score). Its value is the calibration: the dual-OOD split is now
LB-validated on the *identity/DE* axis too, not just direction, closing the last
blind spot in our offline↔LB trust. Full refutation:
[`knowledge/wiki/findings/competitor-landscape.md`](../knowledge/wiki/findings/competitor-landscape.md)
(Measured refutation, 2026-07-17). Submission archived at
`mb/findings/solutions/track-a-char-ngram-probe-LB0.552.csv`.

## Update (feat/marginal-property-de — landed)

Tested the **last untried DE angle**: *marginal* per-symbol features (STRING connectivity
degree) instead of the 5 failed *pair-interaction* channels. Standalone DE-AUROC **0.536**
(fails the 0.55 gate) — but it's the **first DE channel above chance** (the pairwise ones were
flat 0.498–0.502), and fusing it into the two-stage lifts OOD-val mean **+0.008** (all seeds):
**the first DE-axis gain of the whole investigation.** Refines "DE is dead" → *pairwise* DE is
dead; *marginal* DE is faint-but-nonzero. Did not submit (+0.008 modest; LB 0.585 stands).
Methodological note: the fixed 0.55 standalone gate is too strict when the incumbent is chance —
a 0.536 channel still helped fused. Leads: richer marginal features (essentiality/expression) and
a stacked direction+marginal submission.

## Update (feat/de-dir-submission — landed)

Fused the neighbour-retrieval **direction** signal into the two-stage Track A submission.
**Kaggle LB 0.585** (2026-07-16) — +0.024 over the two-stage 0.561 and past the prior overall
best 0.578. The dual-OOD gate predicted +0.027; the board delivered +0.024 (gap ~0.003) — the
split is predictive for the direction axis too. Backstory: three curated-edge/network DE channels
were ruled out at ~chance (`feat/de-detector`), then neighbour-retrieval was revealed as a
**direction** lever, not a DE one (DIR-AUROC 0.651 vs the ~0.58 blend; `feat/de-retrieval`), now
LB-confirmed. DE-vs-none stayed near-chance across four channel families — direction is where the
external-signal gains are. Pure feature channel, no LLM/Bing dependency. Next: stack the same
direction fusion onto the Track B blend (0.578).

## Update (feat/track-b-neighbour-dir-parity — landed)

Ported the #28 neighbour-direction lever (Track A LB 0.585) to Track B — the free
follow-through flagged at the end of the last update. The now track-agnostic
`fuse_neighbour_direction` rank-fuses the STRING-neighbour direction into the floored
Track B submission (DE ranking + agent metadata untouched; only `up/(up+down)` moves).
**OOD-val 0.5916** — direction **0.570→0.624** at 98% coverage, DE unchanged
(0.559→0.560) — **+0.028 over the floored base (0.5647)** and **+0.020 over the prior
Track B best** (two-stage DIR-blend 0.5712 / LB 0.578). New Track B best offline. The
neighbour channel standalone confirms it's a pure direction lever (DIR-AUROC 0.651 ± 0.047
over 5 seeds; DE 0.498 = chance). Two things this settles: the 0.578 blend had *not*
already absorbed the neighbour direction (the lift didn't shrink on the live pipeline),
and "stronger learned direction" is the Track B lever that keeps paying — same as Track A.
**Kaggle LB 0.597** (2026-07-17) — a new Track B best, +0.019 over 0.578; OOD-val 0.5916
predicted it and the board came in **+0.005 higher**, so the dual-OOD split held once more.
Pure feature channel, no LLM/Bing dependency. Schema-valid submission (1,813 rows, 99.6%
coverage, 0 nulls) archived at `mb/findings/solutions/track-b-de-dir-LB0.597.csv`.

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

## Update (feat/gene-embedding-dir — landed)

A GenePert-style **gene-embedding DIRECTION channel** — the first DIR channel that is
both predictive *and* diverse. `text-embedding-3-small` (1536-d) embeds each symbol's
GO:BP text; a leak-free ridge (fit on **train DE rows only**, features `[pert_emb ⊕
gene_emb]`) predicts `P(up|DE)`. Multi-seed dual-OOD
(`scripts/gene_embedding_eval.py`):

| metric | value | vs incumbent |
|---|---|---|
| DIR-AUROC | **0.574 ± 0.027** | below neighbour-DIR 0.647 |
| corr vs neighbour-DIR | **0.19 ± 0.06** | nearly independent |
| coverage | **100%** | neighbour ~98%, char-family 42% |
| gate (DIR-AUROC ≥ 0.55 ∧ \|corr\| ≤ 0.5) | admitted **3/5 seeds** | — |

Weaker standalone than neighbour-DIR (0.647), but the **0.19 correlation** means it
carries *new* direction information — value is as a **fusion arm on the DIR bus**, not a
standalone winner. It's the second gate-passing DIR channel (with neighbour-DIR), so a
DIR portfolio the fuse harness can actually stack now exists — vs the five DE channel
families that all sat at chance. The **fused lift over 0.647 is unmeasured** (future
work). Two takeaways: (1) a channel earns a fuse slot on *low correlation*, not
standalone AUROC; (2) the key-vs-mechanism thesis extends to featurization — a *content*
key (LLM embedding of gene function) transfers direction where a *naming-convention* key
(char/prefix family) did not. Dev result on the OOD split, not submitted (0.574 &lt;
the live LB 0.597).

## Update (explore/dir-ceiling-probe — landed)

A measurement-only probe **bounding the fused-direction ceiling** on the dual-OOD
split — the number that gates the rank-1-vs-data-lane decision. Standalone DIR-AUROC:
neighbour-DIR **0.651 ± 0.047**, GO-DIR 0.595, embedding-DIR 0.574. Rank-fusing all
three (`fuse()`, equal-weight) over the full subset lattice:

| subset | DIR-AUROC |
|---|---|
| **neighbour** | **0.651** |
| GO + neighbour | 0.648 |
| neighbour + embedding | 0.644 |
| GO + neighbour + embedding | 0.642 |
| GO + embedding | 0.599 |
| GO | 0.595 |
| embedding | 0.574 |

**Equal-weight fusion of all three (0.642) sits *below* the single best channel,
neighbour-DIR alone (0.651)** — every arm added drags it (+GO −0.002, +embedding
−0.007, +both −0.009). Averaging unequal-quality rankers lands below the best ranker;
the 0.19-correlation embedding channel earns a fuse *slot* but is too weak (0.574) to
convert its independence into lift under equal weights. **Low correlation earns a slot;
only channel strength lifts the fusion.** This independently corroborates the
just-merged **#37 (`fuse-direction-channels`)**, which reached the same wall from the
production side — 3-way = 2-way = +0.027, "direction saturated at 2 channels; CFA
corr-diversity ≠ marginal lift."

**The strategic read:** the naive direction ceiling is **~0.65**; with DE pinned ~0.55
(#36 / marginal-DE), the honest **mean-AUROC ceiling of the current lane is ~0.60** —
below the field's *unverified* 0.693. Beating equal-weight requires a weighted combiner
that up-weights neighbour-DIR (cf. #31, w≈0.75), but headroom is small (the other
channels top out ~0.60). **Fork:** push neighbour-DIR to its weighted best, **submit
once and read the real LB gap**, then decide whether rank-1 needs a *new signal source*
(Perturb-seq expression data — Replogle / PerturbQA), not more direction channels.
Lower bound, equal-weight — this is a dev measurement on the OOD split, **not submitted**
(no submission generated; LB 0.597 stands). Full lattice + mechanism:
[`knowledge/wiki/findings/dir-ceiling-equal-weight-fusion.md`](../knowledge/wiki/findings/dir-ceiling-equal-weight-fusion.md).

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
