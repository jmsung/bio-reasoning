"""Track A submission: the one unspent real-LB read for the PerturbQA data lane.

`research/perturb-seq-transfer-probe` (PR #48) closed the lane *offline*: the external
PerturbQA DE channel fused for only +0.0075 mean on the dual-OOD holdout (one-seed noise;
overlap DE 0.72 collapses to ~0.53 OOD; CFA 1/3). The go/no-go doc
(`docs/perturb-seq-lane-decision.md`) authorized one cheap real-LB read but the OOD-val
gate pre-empted it. This script spends exactly that read.

It emits the *same channel set the OOD-gate scored*, over the real test set, via the generic
rank-`fuse`:
- baseline = ``fuse([GO two-stage DE, neighbour DIR])``
- +external = ``fuse([GO, neighbour, external PerturbQA DE+DIR])``

Submitting both isolates external's real-board contribution as a clean delta (the generic
baseline is ~0.003 below our weighted LB-0.586 best, so comparing +ext against the generic
baseline — not against 0.586 — is the honest read). Deterministic → seed columns mirror.

Run: uv run --group eval python scripts/track_a_external_de_submission.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.features.external_labels import external_pert_channel, load_perturbqa
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
from bio_reasoning.features.string_graph import fetch_string_partners
from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_submission.json"
PQ_DIR = ROOT / "data/external/perturbqa"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT_BASE = ROOT / "submissions/track_a_ext_baseline.csv"
OUT_EXT = ROOT / "submissions/track_a_ext_de_dir.csv"


def _de_r(up, down):
    de = up + down
    import numpy as np

    return de, np.divide(up, de, out=np.full_like(de, 0.5), where=de > 0)


def build(train: pd.DataFrame, test: pd.DataFrame, partners, store):
    """Return (baseline_frame, external_frame) — generic fuse, real test rows."""
    go = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up_go, down_go = go.predict(test.pert.tolist(), test.gene.tolist())
    s_de_go, r_go = _de_r(up_go, down_go)

    q = test[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train)
    nb = neighbor_channel(q, train, pnb, gnb, min_support=3)
    ext, covered = external_pert_channel(q, store)
    print(
        f"external PerturbQA coverage on test: {covered.mean():.1%} ({covered.sum()} rows)",
        flush=True,
    )

    c_go = Channel("go", s_de=s_de_go, r=r_go)
    c_nb = Channel("nb", s_de=None, r=nb.r)

    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()

    def frame(channels, name):
        up, down = fuse(channels)
        # non-empty trace per row — empty strings round-trip to NaN and can trip
        # Kaggle's null check (matches the LB-0.586 submission's behaviour).
        ext_used = "external_perturbqa" in {c.name for c in channels}
        traces = [
            f"{name}: score_de={u + d:.3f} dir={(u / (u + d) if (u + d) else 0.5):.3f}"
            f"{' ext-covered' if (ext_used and cov) else ''}"
            for u, d, cov in zip(up, down, covered, strict=True)
        ]
        out = to_submission_frame(test.id, up, down, name, expected, traces=traces)
        assert len(out) == len(test), "row count mismatch vs test.csv"
        assert not out.isnull().any().any(), "submission has nulls"
        return out

    base = frame([c_go, c_nb], "track-a-go+nb-genericfuse")
    plus = frame([c_go, c_nb, ext], "track-a-go+nb+perturbqa-de-dir")
    return base, plus


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    syms = sorted(
        set(train.pert.astype(str))
        | set(train.gene.astype(str))
        | set(test.pert.astype(str))
        | set(test.gene.astype(str))
    )
    partners = fetch_string_partners(syms, STRING_CACHE)
    store = load_perturbqa(PQ_DIR)
    base, plus = build(train, test, partners, store)
    OUT_BASE.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(OUT_BASE, index=False)
    plus.to_csv(OUT_EXT, index=False)
    print(f"wrote {OUT_BASE.name} and {OUT_EXT.name} ({len(base)} rows each)", flush=True)


if __name__ == "__main__":
    main()
