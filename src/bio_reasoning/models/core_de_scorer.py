"""CORE DE scorers over contrastive references (Yuan 2026).

Two variants, both consuming the positive/negative reference set from
:func:`~bio_reasoning.features.contrastive_context.contrastive_references`:

- :func:`voting_pde` — ``P(DE)`` = fraction of references that are DE. **No LLM.** This
  is CORE-Voting; over our neighbour graph it *is* the neighbour-retrieval-DE ``s_de``,
  already ≈0.498 on the dual-OOD split (``findings/contrastive-de-core-assessment.md``).
- :func:`reasoning_pde` — an LLM reasons over the contrastive set → ``P(DE)`` via an
  injectable client's yes/no score (token-logprob). Mockable; the **real** run needs a
  logprob endpoint (Bing DGX / local), the same dependency as ``track-b-scoring-not-labeling``.
"""

from __future__ import annotations


def voting_pde(refs: dict[str, list]) -> float:
    """Return ``P(DE)`` = ``n_positive / (n_positive + n_negative)``; ``nan`` if no refs."""
    n_pos, n_neg = len(refs["positive"]), len(refs["negative"])
    n = n_pos + n_neg
    return float("nan") if n == 0 else n_pos / n


def _format_prompt(pert: str, gene: str, refs: dict[str, list], cap: int = 20) -> str:
    def _fmt(rows):
        return "; ".join(f"{p}->{g}:{lab}" for p, g, lab in rows[:cap]) or "(none)"

    return (
        f"Query: does perturbation {pert} differentially express target gene {gene}?\n"
        f"Related perturbations that DID respond (up/down): {_fmt(refs['positive'])}\n"
        f"Related perturbations that did NOT respond (none): {_fmt(refs['negative'])}\n"
        "By comparison to these related outcomes, answer yes or no."
    )


def reasoning_pde(pert: str, gene: str, refs: dict[str, list], client, model=None) -> float:
    """Return ``P(DE)`` from an LLM reasoning over the contrastive set.

    ``client.score_yes(prompt, model=...)`` returns ``P(yes)`` (e.g. a renormalized
    yes/no token logprob). Injectable so tests mock it; the real client requires a
    logprob-exposing endpoint.
    """
    return float(client.score_yes(_format_prompt(pert, gene, refs), model=model))
