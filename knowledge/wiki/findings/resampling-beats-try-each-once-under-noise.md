---
title: Under a noisy evaluator, a resampling policy beats a try-each-once grid — the grid can be permanently fooled by one lucky sample
status: measured
cites:
  - methods/self-improvement-loop.md
  - findings/direction-transfers-de-doesnt.md
  - findings/dir-ceiling-equal-weight-fusion.md
---

# Under a noisy evaluator, a resampling policy beats a try-each-once grid

[[../home]] | [[../index]]

**Status: measured (unit test) — `feat/loop-rl-proposer`, 2026-07-17.** A search-methodology
lesson that generalizes past the self-improvement loop: whenever the per-candidate score is
**noisy**, the policy that decides *which candidate to sample next* matters as much as the
candidate space.

## The trap

The default loop proposer (`de_variants.make_de_proposer`) is a **grid walk**: it pulls every
variant **exactly once**, takes the observed reward at face value, and never resamples. That
inherits the loop's recurring failure mode directly — the **one-seed-noise phantom** (a ~+0.007
"win" that evaporates on a reseed, seen ~5× across the project;
[[direction-transfers-de-doesnt]], [[dir-ceiling-equal-weight-fusion]]). With one pull per arm,
a single lucky sample can crown the wrong variant and the grid **can never correct it** — there
is no second look. The more arms, the more likely at least one gets a lucky draw, so the grid's
"best" is biased toward whichever arm was luckiest, not best.

## The fix

A **UCB1 bandit** (`bandit.py::make_bandit_proposer`) over the same arms **resamples** promising
variants: reward = the gate's per-candidate mean-AUROC, next arm = `mean + c·sqrt(ln(total)/n)`.
A phantom high-reward arm gets pulled again, its estimate **regresses toward its true reward**
before it's trusted, and budget flows to genuine contenders instead of being spent exhausting the
grid. A unit test (`tests/test_trial_loop_bandit.py`) makes this concrete: on a reward surface
where arm B's *first* sample is lucky, a try-each-once grid picks B; the bandit resamples and
picks the true-best A.

## Why it matters here (and the caveats)

- This is the same insight the **triple-verify gate** encodes at the accept step (beat baseline
  on all 3 seeds by > the noise band). The bandit applies it at the **propose** step — cheaper,
  earlier, and continuous. They are complementary, not redundant.
- **Cost, not free lunch:** resampling spends more evaluations per arm, so the bandit only wins
  when evaluation noise is large enough that a single sample is untrustworthy — which is exactly
  our regime. On a cheap/exact evaluator, the grid's one-pull-per-arm is strictly more efficient.
- **No self-convergence stop:** unlike the grid, a bandit never runs out of arms to pull, so it
  must be bounded by `--max-trials` / `--budget-usd`. All policies still inherit the `ruled_out`
  denylist so none can wander into a dead static basin.
- **Only proven on synthetic reward so far** — the live A/B (grid vs bandit vs llm,
  trials/budget-to-best on the real gpt-oss env) is user-gated on $ and not yet run.

## See also

[[../methods/self-improvement-loop]] (pluggable-proposer seam, `--proposer {grid,bandit,llm}`) ·
[[direction-transfers-de-doesnt]] · [[dir-ceiling-equal-weight-fusion]]
