# Architecture

System design for the team's pipeline(s) — data flow, components, and the
boundaries between them.

**Status:** placeholder. To be filled as the design lands.

This document will own:

- The high-level data flow from raw Perturb-seq → features → model → submission.
- Component boundaries (data pipeline, inference runner, evaluation, submission).
- Per-track architectural notes (A: prompt engineering, B: agent + tools, C: FT).
- Cross-cutting concerns (config, logging, reproducibility).

Until then, see [`roadmap.md`](roadmap.md) item 5 ("Draft track-specific
approach plans") for the work that will produce the first real draft.

## Trial-loop harness (Tracks A & B)

`src/bio_reasoning/trial_loop/` is a propose → run → reflect → archive loop that
scores candidate `Variant`s against the leak-free **dual-OOD validation split**
(`bio_reasoning.eval.split.holdout_split`) using the shared
`mean(AUROC_de, AUROC_dir)` metric. `scripts/trial_loop.py` is the CLI entry point.

- **Track A** (`--track a`): prompt-only. Variants vary the prompt template and
  few-shot exemplars (`random` sampling or `go_category` retrieval). Inference goes
  through `utils/openai_compat.post_chat_completion` against gpt-oss-120b (OpenRouter).
- **Track B** (`--track b`): reuses the *identical* split/score/reflect/archive
  harness via an injected `RowPredictor`, driving the DSPy ReAct agent
  (`track_b_agentic.build_react_agent`) one run per val row, with lookup tools
  restricted to the split's train partition for leak-freedom. Runs are resilient
  (per-call retry/fallback) and resumable (per-row cache).
- **Fitness gate**: the OOD-val mean; honest floor ≈ the evidence prior (0.533).
  A trustworthy number needs the full val partition — small/naive CV is a mirage.
  Trials + leaderboard + best variant land in `outputs/trial-loop/` (gitignored).

The same fitness surface for both tracks makes "does the agent beat the prompt?" a
direct control. Our official agent is named `jsagent` (both tracks).

## DE-detector fusion harness (Track A)

The Track A metric averages a DE-detection AUROC with a direction AUROC, and the
DE axis is at chance for every learned head on the dual-OOD split (no shared
pert/gene identity with train). `src/bio_reasoning/fuse/` is the harness for
combining *candidate DE channels* — each an incomparable 1-D score array — by
**rank fusion** (`fuse`, `rank_normalize`), gated by **CFA**
(Correlation-Filtered Admission, `cfa_gate`): a channel is admitted only if it is
both strong (standalone DE-AUROC ≥ `min_auroc`) and diverse (|Spearman| vs the
current fusion ≤ `max_corr`), so redundant signal is rejected before it costs a
Kaggle submission.

The first candidate channel was a CollecTRI signed TF-regulon feature
(`src/bio_reasoning/features/tf_regulon.py`), motivated as identity-free
mechanism (a regulon edge fires for an unseen pert). `scripts/tf_regulon_coverage.py`
measured its ceiling first: on the dual-OOD val split the direct-edge coverage is
only ~0.4%, so the DE channel was **ruled out** — the coverage gate failed before
any fusion. It stands as a tested feature and a validated pattern (measure
coverage before spending a submission), not a working DE detector. The featurizer
and coverage report are pure functions of a cached edge table
(`data/external/collectri_mouse.csv`); only rebuilding that cache needs the
`network` dep group (`decoupler`).
