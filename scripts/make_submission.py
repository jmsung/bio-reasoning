"""Convert predictions to a Kaggle submission file.

Placeholder. Reads `outputs/<experiment_id>/preds/` and writes
`submissions/<track>_<experiment_id>_<YYYYMMDD>.csv` in the track's
required format.

Run: `uv run python scripts/make_submission.py --experiment <experiment_id>`
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError("make_submission: implement once submission format is known")


if __name__ == "__main__":
    main()
