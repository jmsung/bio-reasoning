"""Trial-loop: propose Track A prompt/config variants, score them on the
dual-OOD ``holdout_split`` fitness gate, reflect, and archive the best."""

from bio_reasoning.trial_loop.archive import (
    archive,
    leaderboard,
    load_trials,
    render_leaderboard,
    write_trials,
)
from bio_reasoning.trial_loop.loop import (
    make_agent_row_predictor,
    make_prompt_row_predictor,
    predict_variant,
    retrieve_examples,
    run_loop,
    run_variant,
    sample_examples,
)
from bio_reasoning.trial_loop.reflect import Proposer, best_trial, make_grid_proposer, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant

__all__ = [
    "Variant",
    "TrialRecord",
    "predict_variant",
    "run_variant",
    "run_loop",
    "sample_examples",
    "retrieve_examples",
    "make_prompt_row_predictor",
    "make_agent_row_predictor",
    "reflect",
    "best_trial",
    "make_grid_proposer",
    "Proposer",
    "archive",
    "leaderboard",
    "render_leaderboard",
    "load_trials",
    "write_trials",
]
