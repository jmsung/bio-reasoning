"""Trial-loop: propose Track A prompt/config variants, score them on the
dual-OOD ``holdout_split`` fitness gate, reflect, and archive the best."""

from bio_reasoning.trial_loop.loop import predict_variant, run_variant, sample_examples
from bio_reasoning.trial_loop.types import TrialRecord, Variant

__all__ = ["Variant", "TrialRecord", "predict_variant", "run_variant", "sample_examples"]
