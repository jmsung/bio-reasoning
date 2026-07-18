# BioReasoning Challenge 2026 — Progress Report

*Updated as branches land — the merge workflow proposes report-worthy additions per PR.*
*Last updated: 2026-07-18.*

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
| **Track A — neighbour-DIR fusion (v4)** | fuse the neighbour-retrieval direction (STRING-neighbour label borrowing, leak-free) into the two-stage GO submission via `fuse()`; DE kept, direction blended | **0.586** (Kaggle LB) | **standing Track A + overall best** — v4 base 0.585 (+0.024 over two-stage 0.561, past the 0.578 Track B); the `+external` PerturbQA real-LB read is **0.586** (+0.001 = noise, but the standing best); DE stayed ~chance across 4 channel families — the retrieval signal lives in *direction* |
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

## Update (feat/richer-marginal-de — landed)

Closed the "richer marginal features" lead from `feat/marginal-property-de`: does adding gene
**essentiality** to the marginal DE head push it past the 0.55 gate? **No.** DepMap ternary
essentiality (common-essential +1 / nonessential −1) adds nothing on top of STRING degree —
**+essentiality DE-AUROC 0.534 ± 0.006 vs degree-only 0.536 ± 0.007 (Δ −0.001)** across seeds 0–4
(the degree-only head reproduces the prior 0.536 exactly → harness validated). Mechanism:
common-essential genes are high-degree STRING hubs, so essentiality is **collinear with degree** —
a second connectivity-correlated marginal can't help. Verdict: **marginal DE is capped at ~0.536**;
with six pairwise channels at chance and two connectivity marginals capping identically, the
**static/data DE route is exhausted**. (The one lever still open at the time — model-based
token-logprob self-consistency — has since been tested and is also dead; see the DE close-out
below.) No submit (no lift; LB 0.585 stands). Filed:
`findings/marginal-de-caps-at-degree.md`.

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
   direction-first holds and DE-vs-none is a dead axis every way we have since
   tried it (retrieval, structural, and model-based — see the DE close-out below).
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

**Follow-up (`test/char-ngram-go-dir-ensemble`) — closes the loop:** fusing a
char-ngram channel into the GO two-stage + neighbour-DIR best *regresses* on
OOD-val (0.5663 → 0.5485 DE+DIR / 0.5532 DIR-only) and the CFA gate rejects it
(char DE-AUROC 0.487 < 0.55). The +0.06 understatement is about char's
*standalone* score, not its fusion value — rank-fusing a chance-level direction
channel dilutes the strong neighbour-DIR (0.631→0.604) regardless. **Char-ngram
is a dead lever in the fusion; the ~0.585 direction-fusion ceiling stands.** Not
submitted (no candidate; no quota spent) — and the last-remaining DE shot,
model-based logprob, has since been tested dead too (see the DE close-out below).

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
bottleneck**; direction (~0.58) is fine. The lever this update pointed to — a real DE-detector
for unseen `(pert, gene)` pairs via a **CollecTRI signed TF-regulon feature** (regulon membership
= DE, edge sign under CRISPRi = direction) — has **since been closed dead**: like every other
structural/retrieval DE channel it sat at chance on the dual-OOD split (see the DE close-out
below). These were dev variants, not submitted — all ≤ the live LB 0.578.

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

**Closed by `feat/weighted-direction-fuse`.** The fork above asked whether a *weighted*
or *learned* combiner clears 0.651 at all. Both were run on the same 5-seed dual-OOD split
(`scripts/weighted_direction_fuse.py`): **weighted rank-fusion** (up-weight neighbour-DIR,
GO/embedding at 1) peaks at **0.660** (w≈4) — +0.010 over neighbour-alone but **within seed
σ≈0.05, not robust** (a shallow interior optimum; the weak channels only tie-break neighbour's
~2% uncovered rows). A **leak-free out-of-fold learned stacker** (logistic + pairwise
interactions, `models/direction_stacker.py`) lands **0.641 ± 0.051** — *below* neighbour-alone
(−0.010). Neither robustly beats the single best channel → **~0.65 is the HARD direction
ceiling** (upgraded from the lower bound above); the weak channels carry no direction signal
neighbour-DIR lacks. With DE ~0.55, the honest mean-AUROC ceiling is **~0.60 &lt; the field's
unverified 0.693 — rank-1 by direction alone is off the table.** Dev-only on the OOD split;
**nothing submitted** (LB 0.597 stands). Next per the fork: submit neighbour-DIR's weighted
best (w≈4, ~0.66) **once**, read the real LB gap, then decide the Perturb-seq data lane.

## Update (feat/de-contrastive-core — landed)

A **kill-test of contrastive-LLM-DE** — Yuan et al. 2026 "Plausibility Is Not
Prediction" (CORE), the *one* LLM-DE framing with published evidence (it fixes
the single-pair over-DE bias with contrastive KG evidence). Every prior DE kill
here was a *feature/network* channel; this closes the **LLM/prompt-framing** DE
lane, the last one standing. The consult-KB-first gate did its job: Goal 1
pre-called the kill from the paper (CORE-Voting = our already-dead neighbour-
retrieval-DE; CORE's headline gains are bias-correction, and our AUROC metric is
bias-invariant), then Goal 4 measured it.

**CORE-Voting DE-AUROC 0.498 ± 0.006** (5 seeds, dual-OOD `holdout_split`, 99%
coverage) — **bit-for-bit the neighbour-retrieval-DE floor, KILL** (&lt; 0.55 gate).
On our zero-overlap, sparse-KG regime the contrastive-aggregation mechanism is
dead chance, exactly as the pre-build KB argument predicted. **CORE-Reasoning**
(LLM reasoning over the contrastive set) was **not run — endpoint-blocked** (Bing
logprobs, same wall as scoring-not-labeling); its prior is low (gains are
bias-correction, AUROC-invariant), so the roadmap is not gated on it. The CORE
machinery is kept so that one cell can run in a single script if a logprob
endpoint ever lands.

**This is the 7th DE approach at chance and the strategic close of the LLM-DE
lane team-wide:** prompt/framing cannot move DE-vs-none on this task. It
reinforces, with fresh evidence plus an external-paper cross-check, the standing
conclusion that **only new *measured* signal moves DE** → the **Perturb-seq data
lane** (Replogle / PerturbQA / Tahoe) was the last untested lane with theoretical
DE headroom (**now empirically closed — see the next Update**). Negative result, dev
measurement on the OOD split — **nothing submitted** (LB 0.597 stands). Full
argument + measurement:
[`knowledge/wiki/findings/contrastive-de-core-assessment.md`](../knowledge/wiki/findings/contrastive-de-core-assessment.md).

## Update (research/perturb-seq-transfer-probe — landed)

**The external Perturb-seq data lane — the only lane with headroom toward the
field's 0.693 — is empirically closed.** We ran the Stage-0 gate the
`dir-ceiling-probe` fork pointed to: do external *measured* CRISPRi DE/direction
labels (PerturbQA — curated Replogle K562/RPE1/HepG2/Jurkat) transfer to our
Track A labels above chance? Leakage-clean by construction (Track A is mouse
macrophage, PerturbQA is human — disjoint species *and* cell type).

**The overlap gate looked like a DE breakthrough, then the honest split killed
it.** On the 242 train-overlap pairs, external→Track-A scored **DE-AUROC 0.722 /
DIR-AUROC 0.951** (shuffle control 0.50 — real signal). The DE transfer is
*marginal, not pair-specific* (per-pert LOO 0.676, per-gene LOO 0.538 = chance) —
conserved pert-level responsiveness that even **beat our internal STRING-degree
marginal-DE proxy (0.536, `feat/marginal-property-de`)**. It was lookup-able for
64/96 (67%) of test perts. On paper, the first DE lever with real teeth.

**But the dual-OOD fusion test refuted it.** Fused into the GO+neighbour-DIR
baseline (0.5819) over seeds 0/1/2, the lift is **+0.0075 mean and entirely
one-seed noise** (seed1 +0.022; seeds 0/2 ≈ 0). On the covered OOD-val rows the
external DE-AUROC **collapses to ~0.53** (0.504 / 0.565 / 0.517), not 0.68 — the
0.72/0.95 were **selection-inflated**: the overlap is exactly the set of
robustly-DE, unambiguous *easy* pairs. The CFA orthogonality gate passes only
**1/3 seeds**, direction-only adds +0.002 (redundant with neighbour-DIR), and the
whole thing lands in the same ballpark as the internal marginal proxy (+0.008).

**Verdict: no-go, no submission, no quota spent — the ~0.585 direction-fusion
ceiling stands.** This exhausts the last lane with theoretical DE headroom: the
only remaining DE shot is model-based logprob (Bing-gated) — since tested and dead
too (see the DE close-out below). Its lasting value is
methodological — a textbook case of the recurring lesson that
**overlap/small-CV numbers inflate; only the honest dual-OOD split is truth** (a
+0.72 overlap gate → chance on OOD).

## Update (research/perturb-seq-real-lb-overlap — landed)

**The Perturb-seq data lane is now confirmed dead on the real board — the OOD-val
no-go held.** The transfer-probe closed the lane offline but left one question: was
our synthetic dual-OOD split *too hard*, hiding a lane the real Kaggle test would
reward? We spent the single real-LB read the go/no-go doc reserved. Two Track A
submissions differing only in the external channel — baseline `fuse([GO, neighbour])`
and `+external fuse([GO, neighbour, PerturbQA DE+DIR])` — over the real test
(PerturbQA covering 65.9% of rows).

**Result: baseline 0.585, +external 0.586, Δ+0.001.** The real board agrees with the
OOD-val gate (+0.0075 = noise): external adds nothing even at two-thirds coverage.
Submitting baseline and variant *together* isolated the channel as a clean delta,
rather than comparing against a historical best confounded by the generic-vs-weighted
fuse gap.

**The epistemic payoff exceeds the number:** it refutes the last escape hatch — "we
killed the lane on a too-hard synthetic split." The dual-OOD split is validated honest
by a real-frame measurement; rank-1's ~0.75 is **not** PerturbQA-retrieval DE. That left
exactly one untried DE lever at this point — model-based logprob self-consistency
(`feat/de-logprob-self-consistency`, Bing-gated) — which the next updates close.

## Update (research/traxler-native-macrophage-de — landed)

**Native mouse-macrophage DE close-out — the strongest DE kill of the whole
investigation.** Every external DE probe so far used the *wrong* species or cell type
(PerturbQA is human; STRING/GO are organism-agnostic). Traxler et al. is the one CRISPR KO
screen in **native mouse macrophages** — the exact biology of the Track A test — so it was
the last structural DE source with any theoretical right to transfer. We built a KO150
DE+DIR channel from it and spent one real-LB read.

**Result: `+Traxler` 0.581 vs baseline 0.586 = Δ −0.005** — it *regressed* on the real
board. Root cause: **structural coverage ≈ 0.** 82 of 96 test perturbations are
essential-housekeeping genes that are never knocked out in any macrophage screen (they'd
kill the cell), so the native screen simply has nothing to say about the pairs the test
actually asks about. Right species, right cell type, real board — and still dead. This is
the strongest DE kill we have.

**No other native screen exists to try.** LINCS was the remaining candidate and is ruled
out on the same coverage logic: **L1000 is human-only, and the mouse SigCom LINCS data is
non-macrophage.** There is no measured DE resource that covers our test perturbations in
the right context.

## Update (feat/de-logprob-self-consistency — landed)

**Model-based DE close-out — the last untried DE lever is dead too.** Every earlier update
deferred to "the only DE shot left is model-based logprob self-consistency (Bing-gated)."
It is now tested: **gpt-oss-120B CoT DE ≈ chance** — on an honest 100-row synthpert sample
the model called DE-vs-none correctly on **18/51** DE-positive rows, no better than a coin
flip, exactly like every retrieval and structural channel before it.

**DE-vs-none is now confirmed dead every way we can attack it — retrieval, structural, and
model-based.** There is no remaining DE lever, gated or otherwise. All future score gains
must come from the **direction** axis (capped ~0.65) or from a genuinely new signal source
we do not currently have. This retires the recurring "one lever still open" caveat that ran
through the prior updates.

## Update (self-improving loop program — #53–#57)

With every hand-built DE and direction lever exhausted, the strategy shifted from
hand-tuning individual channels to a **self-improving optimization loop** — let the system
search, per the project's "system thinking over micro-management" philosophy. The shared
environment and run styles landed across five PRs:

- **⓪ env + bandit (#53)** — shared trial environment + bandit over variant proposals.
- **① Traxler real-label fold (#54)** — folds the native-macrophage labels into the loop's
  fitness surface.
- **② rl/llm proposer (#55)** — an RL / LLM-driven variant proposer.
- **③ agentic tool-use (#56)** — agentic tool-use variant.
- The runner now exposes `--proposer` / `--agentic`.

**Retired before build:** **④ synthpert-distill** and **⑤ bakeoff** — Track C is not
registered, so fine-tuning is illegal in Tracks A/B; a distill/bakeoff lane has no legal
submission path.

**Deadlock fixed (#57):** the loop hung on a `urllib` keep-alive socket pileup (idle
kept-alive sockets accumulated until the endpoint stalled); forcing `Connection: close`
cleared it and the loop now runs end-to-end.

**Current blocker — throughput, not correctness.** The loop runs correctly but each trial
takes **~1.4–2.8 h**, so a night yields only **3–6 trials** — too slow to search
meaningfully. Two in-progress branches attack this cheaply first:
`feat/loop-prompt-wording-axis` (widen the proposal space) and `feat/loop-fast-verify`
(a cheap check before committing a full-scale run). **Heavy throughput optimization is
deliberately deferred** until a cheap read shows the loop is finding signal worth scaling —
no point parallelizing a search that has not yet proven it can improve on the standing best.

## Leaderboard sprint (2026-07-18)

A final pre-deadline sprint fired the **two highest-EV leaderboard levers still
standing** — a better *direction* key, and external biological knowledge delivered as a
*live LLM-agent retrieval* on the DE axis. **Both came back null**, and we closed the
sprint with **decision A: bank the honest result** (Track A **0.586**, Track B **0.597**).
No Kaggle quota was spent — both were killed offline on the trustworthy dual-OOD surface.

**Lever 1 — DepMap co-essentiality as a direction key (`feat/depmap-coessentiality-dir`, PR #71).**
The direction signal is a property of the neighbour *key* (STRING neighbour-DIR
0.651), so the only way past it is a *better* key. We built one from **DepMap
co-essentiality** — genes whose CRISPR-knockout fitness effects correlate across ~1,100
cell lines share a functional module — and dropped it into the identical label-borrowing
channel. It is a **weaker** key, not a better one: standalone **DIR-AUROC 0.547 ± 0.048**
(barely above chance) « STRING's 0.651, and fusing the two **drags the score down**
(0.637, Δ−0.014). Co-essentiality captures module *membership* but is a noisier proxy for
the up/down tendency than STRING's physical/annotation edges — the same pattern as the
other diverse-but-weak arms (embedding-DIR 0.574, GO-DIR 0.595). Clean negative, no submit;
the **~0.65 direction ceiling holds**.
[`findings/coessentiality-direction-key-negative.md`].

**Lever 2 — a Track B external-knowledge retrieval agent (`feat/track-b-retrieval-agent` /
`feat/track-b-full-read`, PRs #72, #74).** This was the one genuinely untried bet: a
**per-row LLM agent** (gpt-oss-120b) that reasons over *retrieved external biology* —
each pair's GO:BP terms and STRING partners, pulled live from mygene.info / string-db —
to call DE-vs-none. Because the agent sees knowledge the earlier leakage-allowed oracle
(0.555, [`findings/de-unlearnable-oracle-ceiling.md`]) never had, beating the DE ceiling
was possible *in principle*. It was also **calibrated to avoid the v1 abstention collapse**
— 0% abstention (vs the 72%-`0/0` that sank the original agent to LB 0.488).

*The dev read teased a breakthrough, then the trustworthy read killed it.* On a single
**150-row** dual-OOD holdout the agent scored **AUROC_de = 0.631** — *above* the 0.555
identity/marginal ceiling, and above the 0.555 DE wall. But the honest **1,500-row read
(3 × 500-row dual-OOD seeds)** regressed to **AUROC_de = 0.578 (95% CI [0.549, 0.607])**.
The CI **includes 0.555**, so DE is **not** genuinely cracked — per-seed DE swung
0.533 → 0.616, a ±0.04 band straddling chance, and the 0.631 was simply the high tail of a
wide small-sample distribution. Fused (agent-DE ⊕ neighbour-DIR) scored **0.604 ± 0.035**
vs the **0.597** incumbent — **statistical parity**, not a gain; the standalone agent (0.578)
sits *below* the incumbent. Verified **leak-free**: nothing in the pipeline is fitted on
labels (hardcoded direction prior, external label-free GO/STRING), and the split is dual-OOD
with `assert_leak_free` enforced. No submit.
[`findings/retrieval-agent-de-headline-was-noise.md`].

**The noise-vs-signal lesson, again.** Both levers reprise the project's most-repeated
methodological finding: **a rank-metric AUROC from a small dual-OOD sample lies.** 0.631 on
150 rows collapsed to 0.578 on 1,500; 0.72 overlap-gate transfers (the earlier PerturbQA
probe) collapsed to chance on the honest split; 0.675 on a 60-row CV became 0.488 on the real
board. The seed/subsample band on this split is ±0.04+, so **any "we beat the ceiling" claim
must clear ≥ 500 rows × multi-seed before it is believed.** The 150-row tease would have been
a false breakthrough had we submitted on it.

**Conclusion — external biological knowledge does not crack the DE axis.** Delivered as its
strongest possible form — a live LLM agent reasoning over retrieved GO/STRING biology, with
no leakage and no abstention penalty — external knowledge lands at **DE parity with the
incumbent, not above it**. This is the format-independent confirmation of the headline
negative: the ~0.555 identity/marginal DE ceiling ([`findings/de-unlearnable-oracle-ceiling.md`],
[`findings/de-unlearnable-on-dual-ood.md`]) holds whether DE is attacked by curated edges,
learned models, retrieval lookup, chain-of-thought, or now agentic external-knowledge
retrieval. **DE-vs-none is unlearnable on this dual-OOD task by every method we can bring.**
The project is at its **honest ceiling — Track A 0.586, Track B 0.597** — and the sprint's
value is epistemic: it closes the last open lever and hardens, rather than dents, the
central result. Synthesis: [`findings/external-knowledge-does-not-crack-de.md`].

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

## Plan

The hand-built lever hunt is complete: **DE-vs-none is dead every way** (retrieval,
structural, model-based) and the **direction axis is capped at ~0.65**, giving an honest
mean-AUROC ceiling of ~0.60 for the current signal set. Standing bests — **Track A 0.586,
Track B 0.597** — are the plateau of hand-tuning. The plan is therefore no longer "find the
next channel" but "let the system search":

- **Now — run the self-improving loop (#53–#57).** The shared env, bandit, RL/LLM proposer,
  and agentic tool-use variants are landed and the loop runs end-to-end (deadlock fixed in
  #57). It searches the Track A prompt and Track B agent/tool space against the dual-OOD
  fitness surface.
- **Immediate blocker — throughput.** ~1.4–2.8 h/trial → only 3–6 trials/night. In progress:
  `feat/loop-prompt-wording-axis` and `feat/loop-fast-verify` (cheap-check-before-scale).
  Heavy throughput/parallelism work is **deferred until a cheap read shows the loop is finding
  signal** — don't optimize a search that hasn't proven it can beat the standing best.
- **Submission discipline unchanged.** Spend a real-LB read only on a candidate that beats
  best-on-OOD-val; track the LB−val gap; select finals before the deadline.

## Risks & mitigations

- **Model access** → mitigated: the fixed `gpt-oss-120b` is reachable now via a hosted
  OpenAI-compatible endpoint; a local GPU box is a scale/backup path.
- **Validation ≠ leaderboard** → *realized* on Track B (0.675 CV → 0.488 LB). Mitigated going
  forward by the dual-OOD split that mirrors the real test structure; we track the LB−val gap on
  every submission and never trust CV alone.
- **Agent over-abstention** → *realized* (72% of rows `0/0` collapsed the LB to ~random).
  Addressed by a hard "never emit `0/0`, fall back to the prior" rule, a prior-blend floor, and a
  scoring-not-labeling reframe — validated on the OOD split.
