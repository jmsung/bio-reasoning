"""Self-consistency aggregation of per-(pert, gene) DE answers into graded scores.

Two signals, both producing graded ``(p_up, p_down, p_none)`` floats the Track A
rank metric consumes (DE score = ``p_up + p_down``; dir score = ``p_up / (p_up + p_down)``):

- ``votes_to_scores`` — sample-and-vote self-consistency (Wang et al. 2022): sample
  the model K times, aggregate the answers into vote fractions. Needs only text output,
  so it works with the existing gpt-oss client.
- ``logprobs_to_scores`` — softmax over the answer-token logprobs (the "token-logprob"
  variant). Needs an endpoint that returns ``top_logprobs``; a candidate token absent
  from the returned set is floored, not crashed.

Context: the project's central finding is that the DE axis is near-chance under
dual-OOD (AUROC_de ~= 0.50; see the technical report and Yuan 2026 on LLM over-DE
bias). This module is the measurement apparatus for a kill-test, not a claim it works.
"""

from __future__ import annotations

import math

_VALID = ("up", "down", "none")
_MISSING_LOGPROB = -100.0  # floor for a candidate absent from top_logprobs


def _canon(answer: str) -> str | None:
    """Canonicalize a raw answer to one of up/down/none, or None if unparseable."""
    a = answer.strip().lower()
    return a if a in _VALID else None


def votes_to_scores(answers: list[str]) -> tuple[float, float, float]:
    """Aggregate sampled answers into ``(p_up, p_down, p_none)`` vote fractions.

    Unparseable answers drop out of the denominator. With no valid votes, returns
    ``(0.0, 0.0, 1.0)`` — treated as "none" (DE score 0), never a divide-by-zero.
    """
    counts = {k: 0 for k in _VALID}
    total = 0
    for raw in answers:
        c = _canon(raw)
        if c is not None:
            counts[c] += 1
            total += 1
    if total == 0:
        return 0.0, 0.0, 1.0
    return counts["up"] / total, counts["down"] / total, counts["none"] / total


def logprobs_to_scores(token_logprobs: dict[str, float]) -> tuple[float, float, float]:
    """Softmax over the up/down/none answer-token logprobs → ``(p_up, p_down, p_none)``.

    ``token_logprobs`` maps a candidate answer token to its log-probability (as returned
    in an OpenAI-compatible ``top_logprobs``). A candidate missing from the dict is
    floored to a very small probability rather than dropped.
    """
    lps = [token_logprobs.get(k, _MISSING_LOGPROB) for k in _VALID]
    m = max(lps)
    exps = [math.exp(lp - m) for lp in lps]
    z = sum(exps)
    p_up, p_down, p_none = (e / z for e in exps)
    return p_up, p_down, p_none
