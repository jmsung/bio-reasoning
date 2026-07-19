---
title: Competitor landscape — the public field is LLM-free string-ML
status: draft
cites:
  - domains/ai-reasoning/source/2026-bioreasoning-challenge-overview.md
  - findings/track-a-eda.md
  - findings/track-b-abstention-failure.md
  - findings/tabpfn-for-perturbation-tracks.md
  - findings/curated-edges-fail-de-axis.md
---

# Competitor landscape — the public field is LLM-free string-ML

[[../home]] | [[../index]]

**Status: draft — snapshot of the public field as of 2026-07-15/16, from the live
Kaggle leaderboards + the 6 vote-leading public notebooks across Tracks A/B/C.**

Bottom line: **every vote-leading public notebook predicts from the gene-name
strings with classical ML and fakes the LLM scaffolding.** The "bioreasoning"
framing is essentially unenforced by the metric. The two transferable wins are the
**two-stage DE×DIR decomposition** (aligns a model to the exact scored quantities)
and **character / gene-family prefix structure** (the only mechanism that survives
the doubly-disjoint split; [[track-a-eda]]). The open lane nobody occupies: **real
external gene knowledge** (GO / STRING / pathway) fed to the LLM, and **TabPFN over
functional features** ([[tabpfn-for-perturbation-tracks]]). Caveat (both measured
later, both closed): external knowledge helps only as *LLM retrieval context*, **not**
as a direct curated-edge feature on the DE axis — those edges are too sparse/weak
([[curated-edges-fail-de-axis]]); and TabPFN over functional features (as combiner
*and* as primary predictor) is now measured dead — mean ≤ incumbent, DE on the 0.555
wall, DIR below neighbour-DIR ([[tabpfn-for-perturbation-tracks]]).

## Where the field stands (live leaderboards, 2026-07)

| Track | Top public LB | 2nd–3rd | **Us** |
|---|---|---|---|
| A (prompt-only) | **0.693** | 0.653 / 0.652 | 0.529 (evidence prior, PR #9) |
| B (agentic tool-use) | **0.752** (cellshift.bio) | 0.693 / 0.669 | 0.488 (abstention collapse, [[track-b-abstention-failure]]) |
| C (fine-tune <10B) | **0.693** | 0.658 / 0.645 | — (not entered) |

Two things changed vs our stale docs: (1) **Track B top (0.752) now clearly beats
Track A top (0.693)** — tools *are* pulling ahead; (2) we sit ~0.16–0.26 below the
front on a 0.5-baseline metric — large headroom.

### Measured refutation (2026-07-17, `test/real-test-difficulty-probe`)

We tested the "char-ngram → 0.693" story directly: a **proper char-ngram TF-IDF
two-stage** model scored **Kaggle Track A LB 0.552** — vs its own OOD-val 0.492
(holdout) / 0.531 (5-fold). Two conclusions:
- **The 0.693 char-ngram claim does NOT reproduce** for us — a correct
  implementation reaches only 0.552 on the real board, *below* our GO two-stage
  (0.561) and far below our neighbour-fusion best (0.585). Either the leaders'
  string features are substantially more engineered than a standard char-TFIDF, or
  the printed 0.693 is inflated/misattributed (the 6 notebooks print no scores).
- **Our dual-OOD split is roughly honest** — the LB↔OOD-val gap for char-ngram is
  only +0.02 to +0.06 (LB mildly higher). The real test is a touch easier than our
  hold-out-both-axes split, but **not the 0.17 that would explain 0.693**. We have
  *not* been badly sandbagging; the honest ~0.60–0.65 ceiling stands. Note the gap
  is larger for identity/family features (+0.06) than for our direction models
  (~0.004) — the real test rewards string identity slightly more than our split
  predicts, but not enough to change strategy. See
  [[direction-transfers-de-doesnt]].

## What the public notebooks actually do

Six public notebooks pulled via `uv run kaggle kernels pull` (the `kaggle` CLI is
on the project venv, not global). **None call gpt-oss-120b or any LLM** — every one
predicts from the `pert` / `gene` name strings, treated as character sequences, via
classical ML. The `model_name`, `reasoning_trace`, `tokens_used`, and `tools/`
artifacts are cosmetic scaffolding to pass each track's format check.

Two recipes recur across all three tracks:

- **jek1wantaufik (Track A/B/C ensembles): two-stage DE×DIR decomposition.** Model
  `P(differential)` and `P(up | differential)` as separate heads over **char
  TF-IDF n-grams** of the pair (plus a handful of string-stat features: lengths,
  digit/upper counts, shared-char / prefix / suffix matches), then recombine
  `up = DE·DIR`, `down = DE·(1−DIR)`. Heads are linear/tree ensembles
  (LogisticRegression, MultinomialNB, LinearSVC, RandomForest; **CatBoost** on the
  directional head in the Track A variant). This **directly optimises the metric's
  two AUROCs** — the single most transferable idea in the set.
- **avikdas (Track A/B/C "zero-overlap" series): one char-level Siamese
  BiLSTM + cross-attention** reskinned per track (relabeled "fine-tuned Qwen" for
  Track C, but no Qwen / HuggingFace / pretrained weights are ever loaded — a
  from-scratch 64-dim char LSTM). Predicts the 3-class softmax directly. The Track
  B "multi-agent" variant is a prefix→base-rate JSON lookup wrapped in a `for` loop
  over two trivial local tool files.

The one genuine biological insight, stated by avikdas: **test genes are unseen
names but from the same mouse gene families** (`Slc`, `Zfp`, …), so
**character/prefix structure is a proxy for gene family** → a legitimate
zero-overlap generalization bridge. jek1wantaufik exploits the same thing
implicitly via char n-grams + `same_prefix2`/`same_suffix2` features.

**Reference (public Kaggle notebooks, votes in parens):** Track A —
`avikdas567/siamese-attention-for-zero-overlap-perturbations` (14),
`jek1wantaufik/track-a-bioreasoning-ensemble` (15); Track B —
`avikdas567/multi-agent-tools-for-zero-overlap-perturbations` (13),
`jek1wantaufik/track-b-crispri-tfidf-ensemble` (7); Track C —
`avikdas567/sequence-attention-tuning-for-zero-overlap-genes` (14),
`jek1wantaufik/gene-perturbation-sparse-ensemble-classifier` (10).

## Caveats on reading these numbers

- **Vote count ≠ score.** None of the 6 notebooks captured execution outputs, so
  **no CV or LB number is printed in any of them.** They are popular *tutorials*,
  not confirmed top-scorers — they may be mid-table. The finding is that the
  field's *best-known shared solutions* are all classical-ML-in-disguise, not that
  they top the board.
- The **cellshift.bio Track B 0.752** is well above what char-string ML would
  plausibly reach on the harder agentic track — suggesting the *true* leaders use
  real external-knowledge tools, not string tricks. That is the lane we can take.
- Mild transductive shortcuts to avoid if we borrow code: train+test-union char
  vocab (avikdas) and `id`-in-text (jek1wantaufik A2) — harmless here, but not
  something to copy blindly.

## What this means for us — highest-leverage moves

1. **Adopt the two-stage DE×DIR decomposition** as the output structure for *all*
   our tracks (including the LLM ones). Model `P(DE)` and `P(up|DE)` separately and
   recombine. It matches the metric exactly and is a trivially bolt-on-able change
   to the evidence prior. Our 0.529 / 0.488 suggest we are **not** aligned to the
   two-axis structure — this is the cheapest, highest-confidence win.
2. **Build a char/prefix gene-family feature layer** as (a) a strong classical
   floor to beat and (b) a **retrieval key**: map an unseen test gene to its
   nearest *train* gene family and surface those neighbours' outcomes to the LLM
   ("attention over training examples" — an idea *none* of the 6 implement).
3. **Give the LLM what these notebooks refuse to: real external gene knowledge.**
   Since Track B allows tools and every competitor faked them, an *actually
   functional* tool (gene → GO terms / STRING neighbours / pathway membership /
   ortholog lookup) fed into gpt-oss reasoning is genuinely differentiated. String
   n-grams cannot know a gene is a transcription factor vs a transporter; our
   evidence prior already can.
4. **TabPFN over functional features, not strings.** ~~Nobody in the public field
   uses a tabular foundation model~~ — **measured and closed negative
   (`feat/tabpfn-predictor`):** a two-stage TabPFN over a dense functional
   pair-feature table lands mean 0.552 / 0.598 ≤ incumbent, DE on the 0.555 wall,
   DIR below neighbour-DIR every seed. Palla et al.'s SOTA claim does not transfer
   to our dual-OOD-both-axes regime; featurization, not backbone, is the wall
   ([[tabpfn-for-perturbation-tracks]]). Not a differentiator for us.
5. **Score against the right ceiling.** Before spending LLM budget, replicate a
   proper nearest-family classical baseline on our dual-OOD split. Our
   evidence-prior floor there is **0.533** on the held-out val (cf. 0.534 CV /
   0.529 LB; [[track-b-abstention-failure]] and the OOD-val harness). Measure the
   agentic system's *lift over string-ML*, not over 0.5.

## To verify

- **Track B tool legality** — whether an ML-model-backed tool (e.g. TabPFN) is
  permitted around the fixed base. `docs/kaggle-rules.md` Track B now records the
  constraints and the legality reasoning (a frozen tabular PFN is neither the
  fixed base LLM, a fine-tune of it, nor an external *LLM* → reads as legal); the
  one open item is confirming it on the JS-rendered Kaggle Rules tab.

## See also

[[de-unlearnable-on-dual-ood]] — why the "open lane" (external knowledge fed to the
LLM) does not rescue rank on the DE axis: the axis is unlearnable-by-design (oracle
ceiling 0.555 ≈ chance), so the field's headroom, if real, must live on direction /
an easier-than-dual-OOD split. · [[direction-transfers-de-doesnt]]
