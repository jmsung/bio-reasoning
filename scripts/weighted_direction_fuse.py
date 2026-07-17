"""Weighted + learned direction fusion — is 0.651 the hard DIR ceiling?

Goal 1: sweep the neighbour-DIR weight in a rank-fusion of the 3 direction channels
(GO-DIR & embedding-DIR held at 1). Goal 2: an out-of-fold learned stacker
(:class:`DirectionStacker`) over the channels' per-row ``r``. Both on the dual-OOD
split, vs neighbour-DIR alone (~0.651). Result: weighted fusion peaks at ~0.660
(w≈4, within seed noise) and the stacker lands ~0.641 — **neither robustly clears the
single best channel, so ~0.65 is the hard direction ceiling.**

Run: uv run python scripts/weighted_direction_fuse.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

from bio_reasoning.eval.direction_channels import CHANNELS, seed_channels  # noqa: E402
from bio_reasoning.eval.track_a_score import evaluate  # noqa: E402
from bio_reasoning.features.gene_embeddings import (  # noqa: E402
    build_gene_text,
    load_gene_embeddings,
)
from bio_reasoning.models.direction_stacker import DirectionStacker  # noqa: E402
from bio_reasoning.models.fuse import Channel, fuse  # noqa: E402


def _data(rel: str) -> str:
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


TRAIN = _data("data/raw/track_a/train.csv")
PERT_CACHE = _data("data/interim/pert_go_category.json")
GENE_CACHE = _data("data/interim/gene_go_bp.json")
GO_TEXT_CACHE = _data("data/external/go_terms_universe.json")
EMB_CACHE = _data("data/external/gene_embeddings.json")
STRING_CACHE = _data("data/external/string_partners_universe.json")

NBR_WEIGHTS = [1, 2, 4, 8, 16, 32]  # neighbour-DIR up-weight; GO-DIR & embedding-DIR at 1


def _dir_auroc(labels: np.ndarray, channels: list[Channel], weights=None) -> float:
    up, down = fuse(channels, weights=weights)
    return evaluate(labels, up, down)["auroc_dir"]


def _stacker_oof_auroc(rs: dict, labels: np.ndarray, seed: int, n_splits: int = 5) -> float:
    """Out-of-fold DIR-AUROC of the learned stacker over val DE rows — leak-free.

    The channels' r are already OOD (fit on the train fold); the stacker only learns
    to combine them, cross-fit within the val DE rows so its reported ranking never
    sees its own training labels.
    """
    de = labels != "none"
    is_up = (labels[de] == "up").astype(int)
    # Deliberate asymmetry: the stacker sees RAW channel r (logistic is invariant to monotonic
    # per-feature transforms; only its pairwise interactions matter), while the weighted baseline
    # feeds rank-normalized r via fuse(). Each is scored by its own AUROC, so the comparison is
    # fair — don't "fix" this by rank-norming the stacker input.
    r_matrix = np.column_stack([rs[c] for c in CHANNELS])[de]
    if len(set(is_up.tolist())) < 2:
        return float("nan")
    oof = np.full(len(is_up), np.nan)
    for tr_idx, te_idx in StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(
        r_matrix, is_up
    ):
        model = DirectionStacker().fit(r_matrix[tr_idx], is_up[tr_idx])
        oof[te_idx] = model.predict_up(r_matrix[te_idx])
    return float(roc_auc_score(is_up, oof))


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    print(f"train: {len(df)} rows, {len(syms)} symbols", flush=True)
    embeddings = load_gene_embeddings(build_gene_text(syms, GO_TEXT_CACHE), EMB_CACHE)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    print(f"  embedded {len(embeddings)}; STRING partners {len(partners)}", flush=True)

    rows: list[dict] = []
    for seed in range(5):
        val_df, rs = seed_channels(
            df,
            seed,
            embeddings=embeddings,
            partners=partners,
            pert_cache=PERT_CACHE,
            gene_cache=GENE_CACHE,
        )
        labels = val_df["label"].to_numpy()
        chans = [Channel(name=c, r=rs[c]) for c in CHANNELS]  # order: GO, neighbour, embedding
        row: dict = {
            "neighbour_alone": _dir_auroc(labels, [Channel(name="n", r=rs["neighbour-DIR"])]),
            "stacker": _stacker_oof_auroc(rs, labels, seed),
        }
        for w in NBR_WEIGHTS:
            row[w] = _dir_auroc(labels, chans, weights=[1.0, float(w), 1.0])
        rows.append(row)

    def _ms(key) -> tuple[float, float]:
        a = np.array([r[key] for r in rows], dtype=float)
        return float(np.nanmean(a)), float(np.nanstd(a))

    print("\nneighbour weight (GO,emb=1) | fused DIR-AUROC (mean ± std)", flush=True)
    for w in NBR_WEIGHTS:
        m, s = _ms(w)
        tag = "  (= equal-weight all-three)" if w == 1 else ""
        print(f"  w_nbr={w:>3} | {m:.3f} ± {s:.3f}{tag}", flush=True)
    nm, ns = _ms("neighbour_alone")
    print(f"\n  neighbour-DIR alone | {nm:.3f} ± {ns:.3f}", flush=True)

    best_w = max(NBR_WEIGHTS, key=lambda w: _ms(w)[0])
    bm = _ms(best_w)[0]
    robust = (bm - nm) > ns  # beats neighbour-alone by more than one seed-std
    print(
        f"\nBest weighted fusion: w_nbr={best_w} → {bm:.3f} vs neighbour-alone {nm:.3f} "
        f"({bm - nm:+.3f}; seed σ≈{ns:.3f}).",
        flush=True,
    )
    print(
        f"VERDICT (weighted): a shallow interior optimum at w_nbr≈{best_w} nudges to {bm:.3f}, "
        f"{'beyond' if robust else 'WITHIN'} seed noise vs neighbour-alone. Weighted rank-fusion "
        "is bounded by its extremes (equal-weight dilutes ↓, w→∞ → neighbour-alone); the weak "
        "channels help only as tie-breakers on neighbour's uncovered rows.",
        flush=True,
    )

    # Goal 2: leak-free learned stacker (out-of-fold within val DE rows)
    sm, ss = _ms("stacker")
    stack_robust = (sm - nm) > ns
    print(f"\n  learned stacker (OOF) | {sm:.3f} ± {ss:.3f}", flush=True)
    print(
        f"VERDICT (stacker): non-linear combiner {sm:.3f} vs neighbour-alone {nm:.3f} "
        f"({sm - nm:+.3f}; seed σ≈{ns:.3f}) — {'a robust win' if stack_robust else 'WITHIN seed noise'}. "
        f"vs weighted-best {bm:.3f}: {sm - bm:+.3f}.",
        flush=True,
    )
    if not (robust or stack_robust):
        print(
            "CONCLUSION: neither weighting nor a learned combiner robustly clears neighbour-alone "
            f"(~{nm:.3f}) beyond seed noise → **~0.65 is the hard DIR ceiling**. Direction lane is "
            "closed; next = submit once, read the LB gap, then decide the Perturb-seq data lane.",
            flush=True,
        )


if __name__ == "__main__":
    main()
