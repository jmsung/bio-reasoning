"""Trial-loop: propose Track A prompt/config variants, score them on the
dual-OOD ``holdout_split`` fitness gate, reflect, and archive the best."""

from bio_reasoning.trial_loop.agent_variants import (
    AGENT_TOOL_SUBSETS,
    agent_variant_grid,
    make_agent_proposer,
)
from bio_reasoning.trial_loop.archive import (
    archive,
    compare_agentic_vs_prompt,
    leaderboard,
    load_trials,
    render_agentic_vs_prompt,
    render_leaderboard,
    write_trials,
)
from bio_reasoning.trial_loop.bandit import make_bandit_proposer
from bio_reasoning.trial_loop.de_variants import de_variant_grid, make_de_proposer
from bio_reasoning.trial_loop.gate import (
    GateResult,
    measure_noise_band,
    score_across_seeds,
    triple_verify,
)
from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.llm_proposer import make_llm_proposer
from bio_reasoning.trial_loop.loop import (
    make_agent_row_predictor,
    make_configurable_agent_row_predictor,
    make_prompt_row_predictor,
    predict_variant,
    retrieve_examples,
    run_loop,
    run_variant,
    sample_examples,
    with_self_critique,
)
from bio_reasoning.trial_loop.reflect import Proposer, best_trial, make_grid_proposer, reflect
from bio_reasoning.trial_loop.ruled_out import RULED_OUT, is_ruled_out
from bio_reasoning.trial_loop.submission import build_track_a_submission
from bio_reasoning.trial_loop.tools import (
    ToolBackend,
    make_cache_backend,
    make_tools,
    traxler_direction_lookup,
)
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
    "make_openrouter_infer_fn",
    "triple_verify",
    "GateResult",
    "measure_noise_band",
    "score_across_seeds",
    "de_variant_grid",
    "make_de_proposer",
    "make_bandit_proposer",
    "make_llm_proposer",
    "AGENT_TOOL_SUBSETS",
    "agent_variant_grid",
    "make_agent_proposer",
    "make_configurable_agent_row_predictor",
    "with_self_critique",
    "compare_agentic_vs_prompt",
    "render_agentic_vs_prompt",
    "RULED_OUT",
    "is_ruled_out",
    "build_track_a_submission",
    "ToolBackend",
    "make_tools",
    "make_cache_backend",
    "traxler_direction_lookup",
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
