---
title: The self-improvement loop — a P9-style triple-verify search over the live LLM DE lane
status: built (harness landed; no live run yet)
cites:
  - findings/marginal-de-caps-at-degree.md
  - findings/direction-transfers-de-doesnt.md
  - findings/curated-edges-fail-de-axis.md
  - findings/contrastive-de-core-assessment.md
  - findings/track-a-eda.md
  - methods/pbio-agent-for-tracks.md
---

[[../home]] | [[../index]]

# The self-improvement loop

**Status: built, not yet run live (2026-07-17, `feat/self-improvement-loop`).**
A 24/7 autonomous search harness that hunts for a differential-expression (DE)
signal in the *live LLM* lane — the only DE dimension the static/data route
([[marginal-de-caps-at-degree]], [[curated-edges-fail-de-axis]]) hasn't
exhausted. Built **on top of** the `trial_loop` package (PR #23), which already
supplied the loop skeleton, single-seed verifier, proposer, and ledger — this
branch added only the net-new surface below (`src/bio_reasoning/trial_loop/`).

## Why a loop, and why only this lane

The static-feature DE route is a **locked basin** (~0.586 LB; 7 dead pairwise +
marginal channels). Per the P9 pattern, escaping a locked basin needs a *new
dimension*, not more search in the old space. The one untried dimension is the
**LLM-internal DE signal** (gpt-oss votes/text self-consistency). So the loop's
proposer is **structurally barred** from the static basin: `ruled_out.py` holds a
curated `RULED_OUT` frozenset (each key cited to the finding that killed it) and
`de_variants.py::make_de_proposer` filters it before every walk — the loop can
never re-propose a channel the KB already ruled out.

The **search policy** over that barred space is now pluggable
(`proposers.py::select_proposer`, runner flag `--proposer {grid,bandit,llm}`): the
default **grid** walk pulls each variant once; **bandit** (`bandit.py`) resamples by
UCB1 reward so a one-seed phantom regresses before it's trusted; **llm**
(`llm_proposer.py`) lets gpt-oss read the reward history and propose the next config,
falling back to the bandit on any invalid/ruled-out output. All three share the same
`Proposer` seam and inherit the `ruled_out` denylist — bandit/llm never self-converge,
so pair them with `--max-trials` / `--budget-usd`. Why resample at all:
[[../findings/resampling-beats-try-each-once-under-noise]] — the grid's one-pull-per-arm can be
permanently fooled by a single lucky sample (the one-seed phantom), the bandit resamples so the
estimate regresses before it's trusted.

## The 3-tier verification structure (P9-templated)

The core lesson we import from P9: **your fast evaluator lies** — a cheap
evaluator reports improvements that don't exist, and trusting it is catastrophic.
That is exactly our recurring **one-seed-noise phantom lift** (the ~+0.007 "win"
that evaporates on a reseed, seen ~5×). The fix is tiered verification:

| Tier | What | Cost |
|---|---|---|
| 1 — drives search | OOD-val on one fixed cached eval subset | seconds/iter |
| 2 — **triple-verify gate** | candidate must beat baseline on **all 3 seeds/splits by > the measured noise band** | local, per candidate |
| 2b — **external real-label fold** (optional) | an OOD-survivor must *also* beat baseline on a held-out real-label fold — **Traxler KO150** native macrophage, the challenge's exact cell type — so the gain generalizes rather than overfitting challenge-train | local, only for OOD-survivors |
| 3 — real LB | the single Kaggle submission, human-gated, spent only on a tier-2 survivor | rare |

**External fold (`feat/traxler-real-label-fold`):** `gate.py::score_external_fold` +
`triple_verify(external_fold=…)` add tier 2b. Traxler pseudobulk log2FC → challenge
schema (`data.traxler_labels`, |log2FC|≥1.0 → up/down/none; 742 DE). Additive
(`external_fold=None` → unchanged); scored only for OOD-survivors (expensive). Also a
leak-free Traxler exemplar pool for retrieval variants. KO→CRISPRi transfers direction,
not magnitude ([[direction-transfers-de-doesnt]]) — so it is a *validation* substrate.

**Disanalogy vs P9:** P9's exact tier (SymPy) is local and provably correct and
gates *every* candidate. Our real oracle (Kaggle LB) is rate-limited, remote, and
the scarce thing we conserve — so it *cannot* gate every candidate. Triple-verify
is the honest *local substitute*: `gate.py::triple_verify` measures the baseline
seed-to-seed noise band, then accepts iff the candidate beats baseline on every
split-seed by more than that band. It reduces false positives; it does not
eliminate them. It also exposes a **feasibility ratio** (min margin / band) = the
P9 gate-feasibility signal that drives loop-until-dry.

## Backend + signal decisions (both measured, not assumed)

- **Backend = OpenRouter `openai/gpt-oss-120b`.** The *real* competition model, so
  no proxy/transfer risk; leaderboard-valid (the constraint is the open weights,
  not whose box runs them); self-contained and 24/7, with **no Bing-endpoint
  dependency** in the hot loop. Same OpenAI-compatible client + one key reaches
  claude-*/gpt-* too (orchestration/ensemble diversity — designed, not yet built).
- **Signal = votes/text self-consistency, NOT logprobs.** A live probe (2026-07-17)
  showed OpenRouter routes gpt-oss to providers (WandB) that return **no logprobs**;
  pinning a logprob provider (Fireworks/Together) adds complexity. So: sample N at
  temp>0, aggregate discrete up/down/none into graded vote fractions
  (`votes_to_scores`, backend-agnostic). This retires the token-logprob variant that
  [[marginal-de-caps-at-degree]] named as the "only untried DE crack".
- **Practical gotcha:** gpt-oss-120b emits harmony/reasoning tokens first, so a
  small `max_tokens` cap returns empty content — budget generously.

## The prompt-wording axis (`feat/loop-prompt-wording-axis`)

Until this branch the Track A lane searched only *how* the prompt was assembled
(few-shot count, retrieval mode, sample count) — the **instruction wording** was pinned
to the mlgenx PerturbQA default, so the team's EDA never reached the model. The wording
is now a first-class searched axis (`trial_loop/prompt_variants.py`):

- **Named registry, not free-form.** `PROMPT_VARIANTS` maps a name → template; proposers
  select a name and it is validated (`is_valid_prompt`) exactly like `retrieval`. Names —
  not model-emitted strings — keep it token-capped and **leak-safe** (the Track A rule bars a
  prompt that contains the expected outputs). `default` is a `None` sentinel → the mlgenx
  path, so the historical grid and ids are byte-stable until a wording is opted in.
- **Composes with few-shot (no inert knob).** Every non-default template carries an
  `{examples_block}` slot; `loop._format` renders exemplars into it, so `n_few_shot > 0` +
  a knowledge wording shows both — dodging the same silent-inert-knob trap the retrieval
  key_fn hit (below) and the tool lane calls out.
- **Knowledge shipped:** `direction_prior` injects the housekeeping-up / immune-down
  tendency ([[../findings/track-a-eda]] §4, [[../findings/direction-transfers-de-doesnt]]);
  `go_context` asks the model to state the pert's functional class + the target's function
  before deciding ([[../findings/track-a-eda]] "Implications for modeling"). Both are
  grounded in measured EDA, never a test label.
- **Wired end-to-end:** crossed into `de_variant_grid(prompts=…)`, selectable by the
  `llm_proposer` (`prompt` field), and advertised in the optimizer schema
  (`scripts/self_improve_loop.py`). This is the first real prompt-*optimization* surface —
  the axis the strategy note flags as the shared foundation that lifts Track A directly and
  seeds the Track B agent's base prompt.

## Gotcha caught in review — thread the retrieval key_fn

The DE variant space includes a `go_category` few-shot **retrieval** knob. It was
**inert** until `example_key_fn` was threaded through from the proposer into the
predictor: without the key_fn wired, every retrieval variant collapsed to the same
examples, so that whole axis silently did nothing. Now regression-guarded. **General
lesson:** a variant knob that selects *which* context to retrieve is only real if the
retrieval key function is actually plumbed to the inference call — otherwise the
search space is smaller than it looks.

## Safety invariant

The loop **never auto-submits**. `submission.py` builds a schema-valid Track A frame
from a survivor Variant, but a test locks the invariant that no loop/runner code path
executes a submission (no kaggle/subprocess/os.system) — the runner only *prints* the
human-gated next step. Tier 3 is always a human decision.

## Honest EV

- **Best case:** the LLM DE signal exposes something static methods can't → breaks
  0.586. Real, because it is an untested *new dimension*.
- **Likely:** converges ~chance/~0.586 and produces a rigorous negative-result
  finding for the report. The static lane has **no** best case — hence barring it.

## See also

[[marginal-de-caps-at-degree]] · [[direction-transfers-de-doesnt]] ·
[[curated-edges-fail-de-axis]] · [[contrastive-de-core-assessment]] ·
[[pbio-agent-for-tracks]]
