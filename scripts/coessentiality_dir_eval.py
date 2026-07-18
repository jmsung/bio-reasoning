"""DepMap co-essentiality as a DIRECTION neighbour key — leak-free dual-OOD eval.

Builds the same label-borrowing direction channel as the STRING neighbour-DIR incumbent
(``knowledge/wiki/findings/neighbor-retrieval-direction-lever.md``, DIR-AUROC 0.651) but
keyed on **co-essentiality** (correlated CRISPR dependency profiles across DepMap cell
lines) instead of STRING interaction edges. Reports, over 5 dual-OOD seeds:

- standalone co-essentiality DIR-AUROC (covered DE rows) vs the STRING incumbent,
- fused (STRING ⊕ co-essentiality) DIR-AUROC on the full DE-row set — does it ADD?,
- coverage % and the Spearman correlation between the two channels' direction.

Measurement-only. Run: ``uv run python scripts/coessentiality_dir_eval.py``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.coessentiality import load_coessentiality_partners
from bio_reasoning.features.neighbor_retrieval import neighbor_channel

_ROOT = Path(__file__).resolve().parents[1]


def _data(rel: str) -> str:
    """Persistent data path: worktree if present, else the sibling cb/ checkout."""
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


TRAIN = _data("data/raw/track_a/train.csv")
STRING_CACHE = _data("data/external/string_partners_universe.json")
GENE_EFFECT = _data("data/external/CRISPRGeneEffect.csv")
COESS_CACHE = _data("data/external/coessentiality_partners_universe.json")


def _dir_r(train_df, val_df, partners):
    tp = set(train_df["pert"].astype(str))
    tg = set(train_df["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val_df["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val_df["gene"].astype(str).unique()}
    r = neighbor_channel(val_df[["pert", "gene"]].astype(str), train_df, pnb, gnb, min_support=3).r
    assert r is not None
    return r


def _auroc_dir(r, labels, mask):
    dm = np.isfinite(r) & (labels != "none") & mask
    dt = (labels[dm] == "up").astype(int)
    if len(set(dt.tolist())) < 2:
        return float("nan"), int(dm.sum())
    return float(roc_auc_score(dt, r[dm])), int(dm.sum())


def _fused_auroc(r_string, r_coess, labels):
    """Rank-fuse the two direction channels (equal weight) over the full DE-row set."""
    from bio_reasoning.models.fuse import Channel, fuse

    up, down = fuse([Channel("string", r=r_string), Channel("coess", r=r_coess)])
    r = np.divide(up, up + down, out=np.full_like(up, 0.5), where=(up + down) > 0)
    de = labels != "none"
    dt = (labels[de] == "up").astype(int)
    return float(roc_auc_score(dt, r[de]))


def _seed(df, string_p, coess_p, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train = df.iloc[tr].reset_index(drop=True)
    val = df.iloc[va].reset_index(drop=True)
    labels = val["label"].to_numpy()
    all_de = labels != "none"

    r_s = _dir_r(train, val, string_p)
    r_c = _dir_r(train, val, coess_p)

    string_auroc, _ = _auroc_dir(r_s, labels, np.ones(len(val), bool))
    coess_auroc, coess_n = _auroc_dir(r_c, labels, np.ones(len(val), bool))
    # standalone-on-full-DE-rows (fuse pads uncovered to 0.5) — apples-to-apples w/ fused
    coess_cov = float(np.isfinite(r_c).mean())

    from bio_reasoning.models.fuse import Channel, fuse

    up_s, dn_s = fuse([Channel("s", r=r_s)])
    r_s_full = np.divide(up_s, up_s + dn_s, out=np.full_like(up_s, 0.5), where=(up_s + dn_s) > 0)
    string_full = float(roc_auc_score((labels[all_de] == "up").astype(int), r_s_full[all_de]))
    fused_full = _fused_auroc(r_s, r_c, labels)

    # diversity: Spearman between the two channels' r on rows BOTH cover
    both = np.isfinite(r_s) & np.isfinite(r_c)
    rho = spearmanr(r_s[both], r_c[both])[0] if both.sum() >= 3 else float("nan")

    return {
        "string": string_auroc,
        "coess": coess_auroc,
        "coess_n": coess_n,
        "coess_cov": coess_cov,
        "string_full": string_full,
        "fused_full": fused_full,
        "corr": float(rho) if np.isfinite(rho) else float("nan"),
    }


def main() -> None:
    df = pd.read_csv(TRAIN)
    universe = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    string_p = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    print(f"universe: {len(universe)} symbols; STRING partners: {len(string_p)}", flush=True)

    if not os.path.exists(GENE_EFFECT):
        raise SystemExit(f"missing gene-effect matrix: {GENE_EFFECT}")
    coess_p = load_coessentiality_partners(universe, COESS_CACHE, GENE_EFFECT)
    n_edges = sum(len(v) for v in coess_p.values())
    covered_syms = sum(1 for v in coess_p.values() if v)
    print(
        f"co-essentiality: {len(coess_p)} keyed symbols, {covered_syms} with ≥1 partner, "
        f"{n_edges} edges (avg {n_edges / max(covered_syms, 1):.1f})",
        flush=True,
    )

    rows = [_seed(df, string_p, coess_p, s) for s in range(5)]
    print(
        "\nseed | STRING | coess | coess_cov | coessDErows | corr | STRING_full | fused_full",
        flush=True,
    )
    for s, r in enumerate(rows):
        print(
            f"  {s}  | {r['string']:.3f} | {r['coess']:.3f} |   {r['coess_cov']:.0%}   |"
            f"    {r['coess_n']:>4}    | {r['corr']:+.2f} |    {r['string_full']:.3f}    |"
            f"   {r['fused_full']:.3f}",
            flush=True,
        )

    def ms(key):
        v = [r[key] for r in rows]
        return float(np.nanmean(v)), float(np.nanstd(v))

    print("\n== means (5 seeds) ==", flush=True)
    for key, label in [
        ("string", "STRING neighbour-DIR (covered rows, incumbent≈0.651)"),
        ("coess", "co-essentiality DIR (covered rows)"),
        ("string_full", "STRING-DIR (full DE rows, fuse-padded)"),
        ("fused_full", "STRING ⊕ co-ess (full DE rows)"),
    ]:
        m, sd = ms(key)
        print(f"  {label:<52} {m:.3f} ± {sd:.3f}", flush=True)
    cov_m, _ = ms("coess_cov")
    corr_m, _ = ms("corr")
    print(
        f"\n  co-essentiality coverage: {cov_m:.0%}   |   corr vs STRING: {corr_m:+.2f}", flush=True
    )

    coess_m, _ = ms("coess")
    sfull_m, _ = ms("string_full")
    fused_m, _ = ms("fused_full")
    print(
        f"\nVERDICT: standalone co-ess {coess_m:.3f} vs STRING 0.651; "
        f"fused {fused_m:.3f} vs STRING-full {sfull_m:.3f} "
        f"(Δ {fused_m - sfull_m:+.3f}) → "
        f"{'ADDS' if fused_m > sfull_m + 0.005 else 'does NOT add'}.",
        flush=True,
    )


if __name__ == "__main__":
    main()
