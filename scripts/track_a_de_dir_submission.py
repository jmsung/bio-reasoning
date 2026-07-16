"""Track A submission: two-stage GO model with the neighbour direction fused in.

Keeps the two-stage model's DE score (``prediction_up + prediction_down``) but
rank-fuses its direction ``P(up|DE)`` with the neighbour-retrieval channel's
direction (STRING-neighbour label borrowing, TRAIN-only) via ``fuse()`` — the
`feat/de-retrieval` finding that lifted OOD-val mean +0.027. STRING partners for
train+test symbols are fetched from string-db.org (mouse, taxid 10090) on first
run and cached. Deterministic → seed columns mirror the base.

Run: uv run --group eval python scripts/track_a_de_dir_submission.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_submission.json"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT = ROOT / "submissions/track_a_de_dir.csv"
MODEL_NAME = "track-a-two-stage-go+neighbour-dir"


def fetch_string_partners(symbols: list[str]) -> dict[str, set[str]]:
    """Mouse STRING interaction partners per symbol (cached); public API, no key."""
    if STRING_CACHE.exists():
        return {k: set(v) for k, v in json.loads(STRING_CACHE.read_text()).items()}
    base = "https://string-db.org/api/json/interaction_partners"
    out: dict[str, set[str]] = {}
    for i in range(0, len(symbols), 60):
        data = urllib.parse.urlencode(
            {"identifiers": "\n".join(symbols[i : i + 60]), "species": 10090, "limit": 500}
        ).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(base, data=data), timeout=90) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print("STRING fetch err", i, repr(e), flush=True)
            rows = []
        for row in rows:
            out.setdefault(row["preferredName_A"], set()).add(row["preferredName_B"])
        time.sleep(1)
    STRING_CACHE.parent.mkdir(parents=True, exist_ok=True)
    STRING_CACHE.write_text(json.dumps({k: sorted(v) for k, v in out.items()}))
    return out


def build_submission(train: pd.DataFrame, test: pd.DataFrame, partners) -> pd.DataFrame:
    """Two-stage DE + neighbour-fused direction → schema-valid submission frame."""
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(test.pert.tolist(), test.gene.tolist())
    s_de = up + down
    r = np.divide(up, s_de, out=np.full_like(up, 0.5), where=s_de > 0)

    pnb, gnb = build_neighbor_graph(test[["pert", "gene"]].astype(str), partners, train)
    # min_support=3 tuned on OOD-val (feat/de-retrieval); don't lower without re-validating.
    nb = neighbor_channel(test[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)

    fu, fd = fuse([Channel("model", s_de=s_de, r=r), Channel("neighbour", s_de=None, r=nb.r)])
    cov = np.isfinite(nb.r).mean()
    print(f"neighbour direction coverage on test: {cov:.1%}", flush=True)

    covered = np.isfinite(nb.r)
    traces = [
        f"two-stage GO DE + {'neighbour-fused' if c else 'model-only'} direction: "
        f"score_de={u + d:.3f} dir={(u / (u + d) if (u + d) else 0.5):.3f}"
        for u, d, c in zip(fu, fd, covered, strict=True)
    ]
    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()
    out = to_submission_frame(test.id, fu, fd, MODEL_NAME, expected, traces=traces)
    assert len(out) == len(test), "row count mismatch vs test.csv"
    assert not out.isnull().any().any(), "submission has nulls"
    return out


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    syms = sorted(
        set(train.pert.astype(str))
        | set(train.gene.astype(str))
        | set(test.pert.astype(str))
        | set(test.gene.astype(str))
    )
    partners = fetch_string_partners(syms)
    out = build_submission(train, test, partners)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(out)} rows)", flush=True)


if __name__ == "__main__":
    main()
