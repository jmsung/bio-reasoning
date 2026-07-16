"""Blend the two-stage model's direction into a Track B submission.

The Track B champion is floor-to-prior (`tools/direction_prior.floor_to_prior`),
which scores dual-OOD val ~0.564 by giving every no-signal tie the category
prior. The two-stage GO model (`models/track_a_two_stage`) has a weak DE axis on
OOD but a stronger *direction* axis. Rank-averaging its direction into the
submission — while keeping the submission's DE magnitude (``up + down``)
untouched — lifts OOD-val direction AUROC and the mean above floor-to-prior
across every blend weight (`scripts/track_b_two_stage_ood_val.py`).

The DE axis is intentionally not blended: it is near-chance on OOD and would drag
the (stronger) submission DE ranking down.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata


def _dir_ratio(up: np.ndarray, down: np.ndarray) -> np.ndarray:
    de = up + down
    return np.divide(up, de, out=np.full_like(de, 0.5), where=de > 0)


def _unit_rank(x: np.ndarray) -> np.ndarray:
    return rankdata(x) / len(x) if len(x) else x


def blend_direction(up, down, ts_up, ts_down, weight: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """Rank-blend two-stage direction into (up, down), preserving DE magnitude.

    Only the direction ratio ``up / (up + down)`` is rank-averaged with the
    two-stage model's direction (``weight`` = two-stage share in ``[0, 1]``); the
    DE score ``up + down`` is carried through unchanged. Returns ``(new_up,
    new_down)`` with ``new_up + new_down == up + down``.
    """
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)
    de = up + down
    base_dir = _dir_ratio(up, down)
    ts_dir = _dir_ratio(np.asarray(ts_up, dtype=float), np.asarray(ts_down, dtype=float))
    blended = (1.0 - weight) * _unit_rank(base_dir) + weight * _unit_rank(ts_dir)
    return de * blended, de * (1.0 - blended)
