"""UCB bandit policy proposer — a reward-learning alternative to the grid walk.

The grid proposer (``de_variants.make_de_proposer``) pulls every variant exactly
once and never learns from the reward it observes — so it inherits the loop's core
weakness: a single noisy sample can crown the wrong variant (the same one-seed
phantom the triple-verify gate exists to catch). A UCB bandit instead **resamples**
promising variants, letting a variant's estimate regress to its true reward before
it's trusted, and spends budget on contenders rather than exhausting the whole grid.

Same ``Proposer = (reflection, history) -> Variant | None`` seam — the driver, gate,
archive, and inference are untouched. Reward defaults to the gate's per-candidate
mean-AUROC (``TrialRecord.metrics["mean"]``); no new reward model. Ruled-out static
channels are filtered out ([[ruled_out]]) so the policy can't wander into dead basins.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from bio_reasoning.trial_loop.reflect import Proposer
from bio_reasoning.trial_loop.ruled_out import is_ruled_out
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def _default_reward(rec: TrialRecord) -> float:
    return float(rec.metrics.get("mean", 0.0))


def make_bandit_proposer(
    candidates: list[Variant],
    reward_fn: Callable[[TrialRecord], float] | None = None,
    c: float = 1.4,
    max_pulls: int | None = None,
    seed: int = 0,
) -> Proposer:
    """UCB1 policy over ``candidates`` (arms), keyed on ``variant.id``.

    Each call reads the trial ``history``, aggregates the per-arm reward
    (``reward_fn``, default the gate mean), and returns the next arm to pull:
    any never-pulled live arm first (optimistic, in list order), then the UCB1
    argmax ``mean + c·sqrt(ln(total)/n)``. ``max_pulls`` returns ``None`` once the
    total pull budget is spent (the loop's stop signal); otherwise the driver's
    dry/budget/max-trials stops bound the run. ``seed`` is accepted for signature
    parity with stochastic policies (UCB1 is deterministic); it is unused here.
    """
    live = [v for v in candidates if not is_ruled_out(v.id)]
    reward = reward_fn or _default_reward

    def _propose(reflection: str, history: list[TrialRecord]) -> Variant | None:
        rewards: dict[str, list[float]] = {}
        for rec in history:
            rewards.setdefault(rec.variant.id, []).append(reward(rec))
        total = sum(len(v) for v in rewards.values())
        if max_pulls is not None and total >= max_pulls:
            return None
        for v in live:  # optimistic: try each live arm once before exploiting
            if v.id not in rewards:
                return v
        if not live:
            return None

        def _ucb(v: Variant) -> float:
            r = rewards[v.id]
            n = len(r)
            return sum(r) / n + c * math.sqrt(math.log(total) / n)

        return max(live, key=_ucb)

    return _propose
