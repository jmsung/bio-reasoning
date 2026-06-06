# data/

All contents are gitignored except this README.

## Layout
- `raw/` — original downloads from Kaggle / source providers. Never edit by hand.
- `interim/` — partially processed intermediates (cached features, train/val splits).
- `processed/` — final ML-ready datasets consumed by training scripts.
- `external/` — third-party reference data (gene panels, ontologies, etc.).

## Sources
- Track A (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a
- Track B (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b

## Download
TBD — add `scripts/prepare_data.py` to fetch + materialize once track is chosen.

## Schema
TBD — document column names, dtypes, sizes per dataset here as they land.
