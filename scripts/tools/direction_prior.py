"""
direction_prior -- The Track A evidence-grounded prior, exposed as an agent tool.

Classifies the *perturbed* gene into a functional category (housekeeping /
immune / other) from its GO biological-process terms, then returns the
category's graded direction prior: P(up | DE), a DE-confidence, and the
resulting ``pred_up`` / ``pred_down`` scores. This is the no-LLM baseline
that set the 0.529 floor (``models/track_a_prior``, ``features/gene_function``);
giving the agent the same signal lets it ground its A/B/C call in that prior.

GO terms are fetched from mygene.info (mouse) and cached to disk, so repeated
runs are offline. Never keyed on gene identity (test perts are disjoint) --
only on functional category.
"""

from __future__ import annotations

from pathlib import Path

from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.models import track_a_prior

# Shared with the Track A prior baseline so we hit its warm GO cache.
_CACHE = Path(__file__).resolve().parents[2] / "data" / "interim" / "pert_go_category.json"

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "direction_prior",
        "description": (
            "Return the evidence-grounded direction prior for a perturbation. "
            "Classifies the perturbed gene into a functional category "
            "(housekeeping / immune / other) from its GO biological-process "
            "terms and reports P(up | differentially expressed), a "
            "DE-confidence, and the resulting up/down scores. This is the "
            "no-LLM baseline that sets the score floor -- use it to anchor "
            "your answer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pert": {
                    "type": "string",
                    "description": "Perturbed (knocked-down) gene symbol, e.g. 'Rpl13'.",
                },
            },
            "required": ["pert"],
        },
    },
}


def _prior_for(pert: str, cache_path: str | Path) -> str:
    """Core logic, with an injectable cache path (offline-testable)."""
    category = annotate_perts([pert], cache_path)[pert]
    u, d = track_a_prior.PRIORS[category]
    up, down = track_a_prior.predict([pert], {pert: category})
    up_v, down_v = float(up[0]), float(down[0])

    lean = "up" if u > 0.5 else "down" if u < 0.5 else "neither"
    return (
        f"Direction prior for perturbation '{pert}':\n"
        f"  functional category: {category}\n"
        f"  P(up | DE) = {u:.2f}  (leans {lean} when differentially expressed)\n"
        f"  DE-confidence = {d:.2f}  (how likely this category perturbs the target at all)\n"
        f"  => pred_up = {up_v:.3f}, pred_down = {down_v:.3f}  "
        f"(pred_none = {1.0 - up_v - down_v:.3f})\n"
        f"  Note: hypothesis-grade category prior; weigh against mechanistic and "
        f"network evidence before deciding."
    )


def direction_prior(pert: str) -> str:
    """Return the evidence-grounded direction prior for a perturbation gene.
    Classifies the perturbed gene into a functional category (housekeeping /
    immune / other) from its GO biological-process terms and reports
    P(up | differentially expressed), a DE-confidence, and the resulting
    up/down scores. This is the no-LLM baseline that sets the score floor --
    use it to anchor your A/B/C answer, then adjust with mechanistic and
    network evidence."""
    return _prior_for(pert, _CACHE)
