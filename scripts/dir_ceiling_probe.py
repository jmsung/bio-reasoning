"""Goal 1: bound the fused-DIRECTION ceiling on OOD-val.

Assembles the three gate-passing DIRECTION channels — GO-DIR (two-stage GO model),
neighbour-DIR (STRING-neighbour label borrowing), embedding-DIR (GenePert ridge) —
on the dual-OOD ``holdout_split`` (seeds 0-4), rank-fuses their direction via the
existing ``fuse()``, and reports **fused DIR-AUROC** vs the 0.647 neighbour-DIR
incumbent alongside each channel's standalone DIR-AUROC. The number decides how high
direction alone can carry us (DE is pinned ~0.55).

Measurement-only: reads existing channels + ``fuse()``; touches nothing in the
submission pipeline. Run: ``uv run python scripts/dir_ceiling_probe.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

from bio_reasoning.eval.split import holdout_split  # noqa: E402
from bio_reasoning.eval.track_a_score import evaluate  # noqa: E402
from bio_reasoning.features.gene_embeddings import (  # noqa: E402
    build_gene_text,
    fit_direction_ridge,
    gene_embedding_channel,
    load_gene_embeddings,
)
from bio_reasoning.features.go_terms import GoPairFeaturizer  # noqa: E402
from bio_reasoning.features.neighbor_retrieval import neighbor_channel  # noqa: E402
from bio_reasoning.models.fuse import Channel, fuse  # noqa: E402
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR  # noqa: E402

DIR_BASELINE = 0.647  # incumbent neighbour-DIR


def _data(rel: str) -> str:
    """Persistent data path: worktree if present, else the sibling cb/ checkout."""
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


TRAIN = _data("data/raw/track_a/train.csv")
PERT_CACHE = _data("data/interim/pert_go_category.json")
GENE_CACHE = _data("data/interim/gene_go_bp.json")
GO_TEXT_CACHE = _data("data/external/go_terms_universe.json")
EMB_CACHE = _data("data/external/gene_embeddings.json")
STRING_CACHE = _data("data/external/string_partners_universe.json")

CHANNELS = ("GO-DIR", "neighbour-DIR", "embedding-DIR")


def _go_dir_r(train_df: pd.DataFrame, val_df: pd.DataFrame) -> np.ndarray:
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train_df["pert"], train_df["gene"], train_df["label"].to_numpy()
    )
    up, down = model.predict(val_df["pert"], val_df["gene"])
    denom = np.where(up + down == 0, 1.0, up + down)
    return up / denom


def _neighbour_dir_r(
    train_df: pd.DataFrame, val_df: pd.DataFrame, partners: dict[str, set[str]]
) -> np.ndarray:
    tp = set(train_df["pert"].astype(str))
    tg = set(train_df["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val_df["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val_df["gene"].astype(str).unique()}
    return neighbor_channel(
        val_df[["pert", "gene"]].astype(str), train_df, pnb, gnb, min_support=3
    ).r


def _embedding_dir_r(train_df: pd.DataFrame, val_df: pd.DataFrame, embeddings: dict) -> np.ndarray:
    ridge = fit_direction_ridge(train_df, embeddings)
    return gene_embedding_channel(val_df[["pert", "gene"]], ridge, embeddings).r


def _dir_auroc(labels: np.ndarray, channels: list[Channel]) -> float:
    up, down = fuse(channels)
    return evaluate(labels, up, down)["auroc_dir"]


def _seed_row(df: pd.DataFrame, embeddings: dict, partners: dict, seed: int) -> dict:
    tr, va = holdout_split(df, seed=seed)  # defaults: pert_frac=gene_frac=0.4
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)
    labels = val_df["label"].to_numpy()

    rs = {
        "GO-DIR": _go_dir_r(train_df, val_df),
        "neighbour-DIR": _neighbour_dir_r(train_df, val_df, partners),
        "embedding-DIR": _embedding_dir_r(train_df, val_df, embeddings),
    }
    standalone = {k: _dir_auroc(labels, [Channel(name=k, r=v)]) for k, v in rs.items()}
    fused = _dir_auroc(labels, [Channel(name=k, r=v) for k, v in rs.items()])
    return {"seed": seed, "standalone": standalone, "fused": fused}


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    print(f"train: {len(df)} rows, {len(syms)} unique symbols", flush=True)

    print("building embeddings (OpenAI, cached to cb/data/external)…", flush=True)
    gene_text = build_gene_text(syms, GO_TEXT_CACHE)
    embeddings = load_gene_embeddings(gene_text, EMB_CACHE)
    print(f"  embedded {len(embeddings)} symbols", flush=True)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    print(f"  STRING partners: {len(partners)} symbols", flush=True)

    rows = [_seed_row(df, embeddings, partners, s) for s in range(5)]

    hdr = f"{'seed':>4} | " + " | ".join(f"{c:>13}" for c in CHANNELS) + " | fused"
    print("\n" + hdr, flush=True)
    for r in rows:
        cells = " | ".join(f"{r['standalone'][c]:>13.3f}" for c in CHANNELS)
        print(f"{r['seed']:>4} | {cells} | {r['fused']:.3f}", flush=True)

    def _ms(vals: list[float]) -> str:
        a = np.array(vals, dtype=float)
        return f"{np.nanmean(a):.3f} ± {np.nanstd(a):.3f}"

    print("\n== mean ± std (5 seeds) ==", flush=True)
    for c in CHANNELS:
        print(
            f"  {c:>14} standalone DIR-AUROC: {_ms([r['standalone'][c] for r in rows])}", flush=True
        )
    fused_ms = _ms([r["fused"] for r in rows])
    print(f"  {'FUSED':>14} DIR-AUROC: {fused_ms}", flush=True)

    fused_mean = float(np.nanmean([r["fused"] for r in rows]))
    lift = fused_mean - DIR_BASELINE
    print(
        f"\nFused-DIR ceiling {fused_mean:.3f} vs incumbent neighbour-DIR {DIR_BASELINE} "
        f"→ {lift:+.3f}.",
        flush=True,
    )
    print(
        "NOTE: lower bound — measured on the current channels; re-run once "
        "feat/fuse-direction-channels lands any improved fusion.",
        flush=True,
    )


if __name__ == "__main__":
    main()
