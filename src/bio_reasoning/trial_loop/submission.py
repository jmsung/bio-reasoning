"""Bridge a gate-surviving Variant to a schema-valid Track A submission frame.

The loop never submits — this only *builds* the frame; a human runs the documented
``kaggle competitions submit`` step. Predictions are averaged over ``variant.seeds``
(the same self-consistency recipe the loop scored the variant with) and formatted via
the shared :func:`to_submission_frame`, so the emitted CSV matches every other Track A
submission's schema.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.trial_loop.loop import RowPredictor
from bio_reasoning.trial_loop.types import Variant


def build_track_a_submission(
    test_df: pd.DataFrame,
    variant: Variant,
    row_predictor: RowPredictor,
    model_name: str,
    expected_cols: list[str],
    get_examples: Callable[[dict], "list[dict] | None"] | None = None,
) -> pd.DataFrame:
    """Predict ``test_df`` with ``variant`` and return a Kaggle-valid submission frame.

    ``row_predictor`` (e.g. ``make_prompt_row_predictor(openrouter_infer_fn)``) is called
    once per seed in ``variant.seeds`` and averaged — matching ``predict_variant``. Pass
    ``get_examples`` to supply few-shot exemplars from the full train set; the default is
    zero-shot. ``test_df`` must carry ``id``/``pert``/``gene`` columns.
    """
    rows = test_df.to_dict("records")
    provider = get_examples if get_examples is not None else (lambda _row: None)
    per_seed = [
        np.array(row_predictor(rows, variant, s, provider), dtype=float) for s in variant.seeds
    ]
    mean = np.stack(per_seed).mean(axis=0)
    return to_submission_frame(
        test_df["id"].tolist(),
        mean[:, 0],
        mean[:, 1],
        model_name,
        expected_cols,
        seeds=variant.seeds,
    )
