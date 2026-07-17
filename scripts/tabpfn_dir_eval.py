"""Goal 2: TabPFN direction combiner vs the hand-fused DIR ceiling.

Trains a TabPFN classifier over the three DIRECTION channels (GO / neighbour /
embedding) as a *learned nonlinear combiner* and scores DIR-AUROC on the dual-OOD
``holdout_split`` (seeds 0-4) against the two incumbents on **identical val rows**:

  - neighbour-DIR standalone (~0.647, the best single channel)
  - equal-weight rank-fusion of the 3 channels (~0.65, ``dir_ceiling_probe``)

Leak-free by construction: TabPFN trains only on train-partition rows, and their
channel features are **out-of-fold** (cross-fitted over dual-OOD inner folds via
``oof_dir_feature_matrix``) so the training signal matches the dual-OOD regime of
the rows it will score. Val features are fit on the full train partition. Uncovered
channel cells are imputed to 0.5 (neutral P(up)), mirroring ``fuse``'s fallback.

Measurement-only: touches nothing in the submission pipeline. The question is
whether a learned combiner clears the hand-fused ceiling; Goal 3 wires it into the
Track-A submission only if it does.

Run: ``uv run --no-group eval --group tabpfn python scripts/tabpfn_dir_eval.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score
from tabpfn import TabPFNClassifier

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

from bio_reasoning.eval.direction_channels import (  # noqa: E402
    CHANNELS,
    dir_feature_matrix,
    oof_dir_feature_matrix,
)
from bio_reasoning.eval.split import holdout_split  # noqa: E402
from bio_reasoning.eval.track_a_score import evaluate  # noqa: E402
from bio_reasoning.features.gene_embeddings import (  # noqa: E402
    build_gene_text,
    load_gene_embeddings,
)
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

NB_COL = CHANNELS.index("neighbour-DIR")


def _impute(x: np.ndarray) -> np.ndarray:
    """Uncovered channel cells → 0.5 (neutral P(up)), matching fuse's fallback."""
    return np.where(np.isnan(x), 0.5, x)


def _safe_auroc(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def _seed_row(df: pd.DataFrame, embeddings: dict, partners: dict, seed: int) -> dict:
    tr, va = holdout_split(df, seed=seed)
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)

    # Out-of-fold channel features for train rows (leak-free combiner training set).
    x_tr, covered = oof_dir_feature_matrix(
        train_df,
        partners=partners,
        embeddings=embeddings,
        pert_cache=PERT_CACHE,
        gene_cache=GENE_CACHE,
        seed=seed,
    )
    y_all = train_df["label"].to_numpy()
    fit_mask = covered & (y_all != "none")  # DIR is defined on DE rows only
    x_fit = _impute(x_tr[fit_mask])
    y_fit = (y_all[fit_mask] == "up").astype(int)

    # Val features fit on the full train partition.
    x_va = dir_feature_matrix(
        train_df,
        val_df,
        partners=partners,
        embeddings=embeddings,
        pert_cache=PERT_CACHE,
        gene_cache=GENE_CACHE,
    )

    clf = TabPFNClassifier(random_state=0).fit(x_fit, y_fit)
    classes = list(clf.classes_)
    proba = clf.predict_proba(_impute(x_va))
    # Real train DE rows carry both directions, but guard the degenerate single-class fit.
    r_tab = proba[:, classes.index(1)] if 1 in classes else np.full(len(x_va), float(classes[0]))

    labels = val_df["label"].to_numpy()
    de = labels != "none"
    is_up = (labels[de] == "up").astype(int)

    # Incumbents on identical val rows. neighbour here is the raw impute-to-0.5 column, not
    # the single-channel fuse() path dir_ceiling_probe uses — same rows, slightly different
    # NaN handling, so this column is self-consistent but not byte-identical to that probe.
    r_nb = _impute(x_va[:, NB_COL])
    up, down = fuse([Channel(name=c, r=x_va[:, i]) for i, c in enumerate(CHANNELS)])

    return {
        "seed": seed,
        "n_fit": int(fit_mask.sum()),
        "n_val_de": int(de.sum()),
        "neighbour": _safe_auroc(is_up, r_nb[de]),
        "equal_fuse": evaluate(labels, up, down)["auroc_dir"],
        "tabpfn": _safe_auroc(is_up, r_tab[de]),
    }


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    print(f"train: {len(df)} rows, {len(syms)} unique symbols", flush=True)

    gene_text = build_gene_text(syms, GO_TEXT_CACHE)
    embeddings = load_gene_embeddings(gene_text, EMB_CACHE)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    print(f"embedded {len(embeddings)} symbols; STRING partners {len(partners)}", flush=True)

    rows = [_seed_row(df, embeddings, partners, s) for s in range(5)]

    cols = ("neighbour", "equal_fuse", "tabpfn")
    print(
        "\n" + f"{'seed':>4} | {'n_fit':>6} {'n_val':>6} | " + " | ".join(f"{c:>10}" for c in cols)
    )
    for r in rows:
        cells = " | ".join(f"{r[c]:>10.3f}" for c in cols)
        print(f"{r['seed']:>4} | {r['n_fit']:>6} {r['n_val_de']:>6} | {cells}", flush=True)

    mean = {c: float(np.nanmean([r[c] for r in rows])) for c in cols}
    std = {c: float(np.nanstd([r[c] for r in rows])) for c in cols}
    print("\n== DIR-AUROC (mean ± std, 5 seeds), identical val rows ==")
    for c in cols:
        print(f"  {c:<12} {mean[c]:.3f} ± {std[c]:.3f}")

    ceiling = max(mean["neighbour"], mean["equal_fuse"])
    delta = mean["tabpfn"] - ceiling
    clears = delta > 0.005
    print(
        f"\nVERDICT: TabPFN {mean['tabpfn']:.3f} vs ceiling "
        f"max(neighbour {mean['neighbour']:.3f}, equal-fuse {mean['equal_fuse']:.3f}) "
        f"= {ceiling:.3f} → {delta:+.3f} "
        f"({'CLEARS' if clears else 'does NOT clear'} the hand-fused DIR ceiling).",
        flush=True,
    )
    if clears:
        print("→ Goal 3: wire the TabPFN combiner into the two-stage Track-A submission.")
    else:
        print("→ learned combiner does not beat hand-fusion; DIR ceiling stands. No submit.")


if __name__ == "__main__":
    main()
