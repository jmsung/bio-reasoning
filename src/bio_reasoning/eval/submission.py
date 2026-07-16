"""Build a schema-valid Track A Kaggle submission frame from graded up/down preds.

The competition CSV carries a base ``prediction_up``/``prediction_down`` plus three
seed columns and a reasoning trace per seed. For a deterministic (non-LLM) model the
seed columns mirror the base. This is the single place that shape lives, shared by
every Track A submission script.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

SEEDS = (42, 43, 44)


def to_submission_frame(
    ids: Sequence,
    up: np.ndarray,
    down: np.ndarray,
    model_name: str,
    expected_cols: list[str],
    traces: Sequence[str] | None = None,
    seeds: tuple[int, ...] = SEEDS,
) -> pd.DataFrame:
    """Return a DataFrame with exactly ``expected_cols`` (order enforced).

    ``up``/``down`` are the graded predictions aligned to ``ids``; the ``seed``
    columns mirror them (deterministic model). ``traces`` defaults to an empty
    string per row. Raises if any expected column is missing after assembly.
    """
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)
    traces = list(traces) if traces is not None else [""] * len(ids)

    out = pd.DataFrame({"id": ids, "prediction_up": up, "prediction_down": down})
    for seed in seeds:
        out[f"prediction_up_seed{seed}"] = up
        out[f"prediction_down_seed{seed}"] = down
        out[f"reasoning_trace_seed{seed}"] = traces
    out["tokens_used"] = 0
    out["prompt_tokens"] = 0
    out["model_name"] = model_name

    missing = [c for c in expected_cols if c not in out.columns]
    if missing:
        raise KeyError(f"submission frame missing expected columns: {missing}")
    return out[expected_cols]
