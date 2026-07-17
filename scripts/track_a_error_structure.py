"""Error-structure EDA for the Track A incumbent (LB 0.585).

Dissects *where* the best pipeline is wrong on the dual-OOD holdout, instead of
only whether the mean AUROC moved. The incumbent is
``two-stage GO DE + neighbour-fused direction`` (`scripts/track_a_de_dir_submission.py`,
roadmap #14). We rebuild it on ``holdout_split`` folds — the same dual-OOD regime as
the hidden test — pool a few seeds for stable per-group AUROCs, then decompose:

1. **Axis budget** — DE-vs-none AUROC vs direction AUROC, and each axis's share of
   the remaining gap (the marginal-value-of-a-lever signal).
2. **By perturbation category** — housekeeping / immune / other (GO keyword match,
   `features/gene_function.classify`): does the EDA's category→direction signal show
   up in the *pipeline's* per-category AUROC?
3. **Neighbour coverage** — DIR-AUROC on rows the neighbour channel covered vs not.
4. **Confident-wrong** — DE rows called up/down with high confidence but wrong,
   cross-tabbed by category (the lever hunt).

All data is read from the offline caches (GO, STRING partners). Figures + tables land
in ``outputs/track-a-error-structure/`` (gitignored — upload to Drive to share).

Run: uv run --group eval python scripts/track_a_error_structure.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.error_structure import (
    axis_gap_budget,
    axis_scores,
    confident_wrong,
    coverage_dir_effect,
    per_group_axis,
)
from bio_reasoning.eval.split import assert_leak_free, holdout_split
from bio_reasoning.features.gene_function import classify
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, fuse_neighbour_direction
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_universe.json"
OUT_DIR = ROOT / "outputs/track-a-error-structure"

SEEDS = (0, 1, 2)
DIR_WEIGHT = 0.75  # incumbent neighbour-direction weight (roadmap #14)
MIN_SUPPORT = 3


def _md_table(df: pd.DataFrame) -> str:
    """Minimal GitHub-markdown table (avoids a `tabulate` dependency)."""
    df = df.round(3)
    cols = list(df.columns)
    head = "| " + " | ".join(map(str, cols)) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def load_partners(path: Path) -> dict[str, set[str]]:
    """STRING partners cache (symbol -> [partners]) as symbol -> set, offline."""
    raw = json.loads(Path(path).read_text())
    return {k: set(v) for k, v in raw.items()}


def incumbent_preds(train_df: pd.DataFrame, val_df: pd.DataFrame, partners) -> pd.DataFrame:
    """Fit the incumbent on ``train_df``; return ``val_df`` + fused up/down/covered."""
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train_df.pert.tolist(), train_df.gene.tolist(), train_df.label.to_numpy()
    )
    up, down = model.predict(val_df.pert.tolist(), val_df.gene.tolist())
    q = val_df[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train_df)
    fu, fd, covered = fuse_neighbour_direction(
        q, up, down, train_df, pnb, gnb, min_support=MIN_SUPPORT, weight=DIR_WEIGHT
    )
    out = val_df.copy()
    out["up"], out["down"], out["covered"] = fu, fd, covered
    return out


def build_pool() -> pd.DataFrame:
    """Pool incumbent predictions across dual-OOD holdout seeds."""
    df = pd.read_csv(TRAIN)
    partners = load_partners(STRING_CACHE)
    frames = []
    for seed in SEEDS:
        tr, va = holdout_split(df, seed=seed)
        assert_leak_free(df, tr, va)
        pred = incumbent_preds(
            df.iloc[tr].reset_index(drop=True), df.iloc[va].reset_index(drop=True), partners
        )
        pred["seed"] = seed
        frames.append(pred)
    return pd.concat(frames, ignore_index=True)


def tag_category(pool: pd.DataFrame) -> pd.Series:
    """Housekeeping / immune / other for each row's perturbation (GO keyword match)."""
    terms = json.loads(PERT_CACHE.read_text())
    cat = {p: classify(p, terms.get(p, [])) for p in pool.pert.unique()}
    return pool.pert.map(cat)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pool = build_pool()
    pool["pert_category"] = tag_category(pool)
    labels = pool.label.to_numpy()
    up, down, covered = pool.up.to_numpy(), pool.down.to_numpy(), pool.covered.to_numpy()

    lines: list[str] = ["# Track A error-structure EDA — incumbent (LB 0.585)", ""]
    lines.append(f"Pooled dual-OOD holdout rows: {len(pool)} across seeds {list(SEEDS)}")
    lines.append(f"Neighbour-direction coverage (DE+none rows): {covered.mean():.1%}")
    lines.append("")

    # 1. Axis budget — verify reproduction + where the gap lives.
    s = axis_scores(labels, up, down)
    b = axis_gap_budget(labels, up, down)
    lines += [
        "## 1. Axis budget",
        f"- mean AUROC (pooled): **{s['mean']:.3f}**  (DE {s['auroc_de']:.3f}, DIR {s['auroc_dir']:.3f})",
        f"- remaining gap: DE {b['de_gap']:.3f}, DIR {b['dir_gap']:.3f}  "
        f"→ DE holds **{b['de_share']:.0%}** of the total remaining gap",
        f"- n_de (rankable direction rows): {s['n_de']}",
        "",
    ]

    # 2. By perturbation category.
    cat_tbl = per_group_axis(labels, up, down, pool.pert_category.to_numpy(), min_n=50)
    cat_tbl.to_csv(OUT_DIR / "category_axis.csv", index=False)
    lines += ["## 2. By perturbation category", _md_table(cat_tbl), ""]

    # 3. Neighbour coverage effect on direction.
    cov_tbl = coverage_dir_effect(labels, up, down, covered)
    cov_tbl.to_csv(OUT_DIR / "coverage.csv", index=False)
    lines += ["## 3. Neighbour coverage → DIR-AUROC", _md_table(cov_tbl), ""]

    # 4. Confident-wrong, cross-tabbed by category.
    cw = confident_wrong(labels, up, down)
    cw["pert_category"] = pool.loc[pool.label.to_numpy() != "none", "pert_category"].to_numpy()
    conf = cw[cw.confident]
    by_cat = (
        conf.groupby("pert_category")
        .agg(n_confident=("wrong", "size"), n_wrong=("wrong", "sum"))
        .assign(wrong_rate=lambda d: d.n_wrong / d.n_confident)
        .reset_index()
    )
    by_cat.to_csv(OUT_DIR / "confident_wrong_by_category.csv", index=False)
    overall_cw = f"{conf.wrong.mean():.1%}" if len(conf) else "n/a"
    lines += [
        "## 4. Confident-direction rows: wrong-rate",
        f"- confident DE rows (dir_score outside [0.25, 0.75]): {len(conf)} / {len(cw)} "
        f"({len(conf) / max(len(cw), 1):.0%})",
        f"- overall confident-wrong rate: {overall_cw}",
        _md_table(by_cat),
        "",
    ]

    _figures(pool, labels, up, down)

    (OUT_DIR / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote outputs → {OUT_DIR}")


def _figures(pool, labels, up, down) -> None:
    """Two diagnostic figures: score separation on each axis."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    de_score = up + down
    m = labels != "none"
    denom = np.where((up[m] + down[m]) == 0, 1.0, up[m] + down[m])
    dir_score = up[m] / denom
    dir_labels = labels[m]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.hist(
        [de_score[labels != "none"], de_score[labels == "none"]],
        bins=30,
        label=["DE", "none"],
        density=True,
        alpha=0.7,
    )
    ax1.set(title="DE axis: up+down score", xlabel="up+down", ylabel="density")
    ax1.legend()
    ax2.hist(
        [dir_score[dir_labels == "up"], dir_score[dir_labels == "down"]],
        bins=30,
        label=["up", "down"],
        density=True,
        alpha=0.7,
    )
    ax2.set(title="DIR axis: up/(up+down) on DE rows", xlabel="P(up|DE)", ylabel="density")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "score_separation.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
