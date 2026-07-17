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

### Self-improvement loop

`scripts/self_improve_loop.py` runs the harness unattended: propose → triple-verify →
promote, until the proposer is exhausted, K non-improving rounds pass, or a spend cap
is hit. It has **two lanes** that share the gate + driver:

- **DE-votes** (default): a prompt-only `infer_fn` searched by a pluggable
  `--proposer {grid,bandit,llm}` (`trial_loop.proposers.select_proposer`): the default
  **grid** walk (`trial_loop.de_variants`) pulls each variant once, **bandit**
  (`trial_loop.bandit`) resamples promising variants by UCB1 reward, and **llm**
  (`trial_loop.llm_proposer`) lets gpt-oss read the reward history and propose the next
  config (bandit fallback on any invalid output). The lane is the gpt-oss DE-votes /
  self-consistency signal.
- **Agentic** (`--agentic`): searches Track B **tool configs** (`trial_loop.agent_variants`)
  — which real-data tools (`trial_loop.tools`: GO:BP, STRING partners, Traxler direction)
  a per-variant DSPy ReAct agent may call, crossed with the self-consistency sample count.
  Baseline is the tool-free agent, so the gate accepts a config only if real tools beat it.
  `trial_loop.archive.compare_agentic_vs_prompt` renders the honest agentic-vs-prompt A/B.

Both lanes denylist KB-ruled-out static channels (`trial_loop.ruled_out`) so budget is never
burned on a dead basin. The **triple-verify gate**
(`trial_loop.gate`) is the anti-false-positive filter: a candidate is promoted only if it
beats the running baseline on *every* independent OOD split by *more than* the seed-to-seed
noise band — conservative by design, preferring missed gains over phantom lifts. An optional
**external real-label fold** (Traxler native macrophages, built by `scripts/build_traxler_labels.py`
from `data.traxler_labels`) tightens this further: an OOD-survivor must *also* beat baseline on
that held-out in-domain fold, proving the gain generalizes to real labels rather than overfitting
the challenge-train distribution (scored only for OOD-survivors, since each fold eval is expensive).
Under `--agentic` this is leak-safe: whenever the Traxler fold is the eval, the agent drops the
Traxler-direction tool for the whole run so it can never read the labels it is validated against.
The pure
driver (`trial_loop.driver`) is file-free and unit-tested; the runner wires OpenRouter
inference (`trial_loop.inference`), the archive ledger, and the launchd / `claude -p` cadence.
The loop never submits — a gate survivor is bridged to a schema-valid frame
(`trial_loop.submission`) for a human-gated Kaggle submission.

#### Fast dev verification (`make verify`)

The full-val gate scores ~1276 rows × 6 seed-scorings per trial (~1.4–2.8 h), so a bug
(deadlock, auth-401, empty responses, empty-eval) or a no-signal verdict can burn a whole
night. `make verify` runs a **cheap DEV pipeline** that exercises a *real* trial end-to-end
in **minutes** — a dev/verify tool, **not** the trustworthy gate:

1. **Preflight** (`scripts/verify_loop.py` → `trial_loop.preflight`): one real smoke trial on
   a `--val-n` subsample, asserting the loop is genuinely working — **non-empty response
   content, `n_val>0`, a real (non-nan) mean, and a written archive**. Codifies the lesson
   that *liveness ≠ working* (an auth-401 and an empty-eval both once passed as "verified" off
   connection health; see the loop deadlock / throughput-verification finding).
   Exits non-zero — and stops the pipeline — on any degenerate mode.
2. **Signal read** (`scripts/self_improve_loop.py --val-n N`): a short subsample search that
   prints a `DEV SIGNAL READ` line — baseline vs best-variant mean and their Δ. On a
   subsample the triple-verify gate is **untrustworthy** (noise dominates), so this reports
   the raw baseline-vs-best delta as a fast go/no-go, ignoring accept/reject.

Interpretation: **signal** (a variant beats baseline) ⇒ escalate to a full-val run or the
throughput-opt work; **near-chance** (nothing beats baseline) ⇒ file a negative-result
finding rather than sink hours into a full run. The `--val-n` knob is DEV-ONLY and **never**
promotes a survivor — the full-val partition stays the only trustworthy gate. Tune with
`make verify VAL_N=120 MAX_TRIALS=8`.
