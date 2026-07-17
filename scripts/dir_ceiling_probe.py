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

import itertools
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


def _data(rel: str) -> str:
    """Persistent data path: worktree if present, else the sibling cb/ checkout."""
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


# All caches — including the *writable* embedding cache — resolve via _data() to the shared
# cb/ checkout on a fresh worktree, so re-embedded vectors persist across worktrees (a
# worktree-local cache is lost when the worktree is pruned). All paths are gitignored.
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


def _seed_subsets(df: pd.DataFrame, embeddings: dict, partners: dict, seed: int) -> dict:
    """Fused DIR-AUROC for every non-empty subset of the 3 channels, one seed."""
    tr, va = holdout_split(df, seed=seed)  # defaults: pert_frac=gene_frac=0.4
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)
    labels = val_df["label"].to_numpy()

    rs = {
        "GO-DIR": _go_dir_r(train_df, val_df),
        "neighbour-DIR": _neighbour_dir_r(train_df, val_df, partners),
        "embedding-DIR": _embedding_dir_r(train_df, val_df, embeddings),
    }
    out: dict[tuple, float] = {}
    for k in range(1, len(CHANNELS) + 1):
        for combo in itertools.combinations(CHANNELS, k):
            out[combo] = _dir_auroc(labels, [Channel(name=c, r=rs[c]) for c in combo])
    return out


def _short(combo: tuple) -> str:
    return "+".join(c.split("-")[0] for c in combo)


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

    seeds = [_seed_subsets(df, embeddings, partners, s) for s in range(5)]
    combos = list(seeds[0].keys())
    mean = {c: float(np.nanmean([sd[c] for sd in seeds])) for c in combos}
    std = {c: float(np.nanstd([sd[c] for sd in seeds])) for c in combos}
    triple = CHANNELS

    # per-seed: standalones + full fusion
    print(
        "\n" + f"{'seed':>4} | " + " | ".join(f"{c:>13}" for c in CHANNELS) + " | fused", flush=True
    )
    for i, sd in enumerate(seeds):
        cells = " | ".join(f"{sd[(c,)]:>13.3f}" for c in CHANNELS)
        print(f"{i:>4} | {cells} | {sd[triple]:.3f}", flush=True)

    # subset lattice, ranked by mean.
    # NOTE: every subset (incl. singles) is scored on the SAME full DE-row set — fuse() pads
    # rows a channel doesn't cover to r=0.5. So a single-channel number here can sit slightly
    # below the covered-rows-only standalone that the per-channel eval scripts report; the
    # point of this probe is same-row-set comparability across subsets, not standalone parity.
    print("\n== subset lattice — fused DIR-AUROC (mean ± std, 5 seeds), ranked ==", flush=True)
    for c in sorted(combos, key=lambda c: -mean[c]):
        print(f"  {_short(c):<26} {mean[c]:.3f} ± {std[c]:.3f}  (n={len(c)})", flush=True)

    best_single = max((c for c in combos if len(c) == 1), key=lambda c: mean[c])
    best_overall = max(combos, key=lambda c: mean[c])

    # marginal contribution: Δ of adding channels onto the best single (equal-weight)
    print("\n== marginal contribution vs best single (equal-weight rank-fusion) ==", flush=True)
    for c in sorted((c for c in combos if best_single[0] in c and c != best_single), key=len):
        added = _short(tuple(x for x in c if x != best_single[0]))
        print(
            f"  {_short(best_single)} + {added:<24} {mean[c] - mean[best_single]:+.3f}", flush=True
        )

    helps = mean[best_overall] > mean[best_single] + 0.005
    print(
        f"\nVERDICT: best single = {_short(best_single)} {mean[best_single]:.3f}; "
        f"best subset = {_short(best_overall)} {mean[best_overall]:.3f}; all-three {mean[triple]:.3f}.",
        flush=True,
    )
    print(
        f"Under equal-weight rank-fusion, adding channels "
        f"{'HELPS' if helps else 'does NOT beat the best single'} → "
        f"naive DIR ceiling ≈ {mean[best_overall]:.3f} vs field ~0.693.",
        flush=True,
    )
    print(
        "NOTE: equal-weight only (lower bound). Weighted / learned fusion "
        "(up-weight neighbour-DIR) is feat/fuse-direction-channels' job.",
        flush=True,
    )


if __name__ == "__main__":
    main()
