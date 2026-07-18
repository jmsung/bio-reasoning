"""XGBoost as a Track A predictor — the gradient-boosted twin of the TabPFN probe.

Completeness probe closing the tabular-ML class: TabPFN (a strictly stronger
small-data tabular model) was just measured as a clean negative in *both* framings
(`knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md` — combiner DIR 0.613 <
0.651; primary-predictor mean ≤ incumbent, on the DE + dir walls). XGBoost is
expected-null and largely redundant: the DE oracle ceiling (0.555,
[[de-unlearnable-oracle-ceiling]]) is classifier-AGNOSTIC, so no gradient-boosted
model can rank DE above chance on the dual-OOD split, and learned direction fusion
was already ≤0.651 ([[dir-ceiling-equal-weight-fusion]]). Measure it anyway.

Two framings, both mirroring the TabPFN scripts exactly (swap the classifier only):

1. **Primary two-stage predictor** — ``XGBClassifier`` for P(DE) and P(up|DE) over
   the SAME dense functional pair features TabPFN used
   (``features/functional_pair_features.py``). Mirrors ``tabpfn_predictor_eval.py``.
2. **Learned combiner** — ``XGBClassifier`` over the 3 direction channels (GO /
   neighbour / embedding), leak-free out-of-fold. Mirrors ``tabpfn_dir_eval.py``.

Leak-free by construction: every feature is a pure function of ``(pert, gene)``
identity + static external KB (never labels); XGBoost trains only on the dual-OOD
train partition, where ``holdout_split`` holds out every val pert AND gene
(``assert_leak_free`` guards it). Modest depth / n_estimators + subsampling guard
the tiny-data overfitting XGBoost is prone to.

Reports both framings on identical val rows, 5 dual-OOD seeds, vs the measured walls:
DE oracle ceiling 0.555, direction ceiling 0.651 (neighbour-DIR), Track A/B LB
0.586/0.597, and the TabPFN numbers (combiner 0.613; primary 0.552/0.598).

Measurement-only: touches nothing in the submission pipeline.
Run: ``uv run python scripts/xgboost_predictor_eval.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

from bio_reasoning.eval.direction_channels import (  # noqa: E402
    CHANNELS,
    dir_feature_matrix,
    neighbour_dir_r,
    oof_dir_feature_matrix,
)
from bio_reasoning.eval.split import assert_leak_free, holdout_split  # noqa: E402
from bio_reasoning.eval.track_a_score import evaluate  # noqa: E402
from bio_reasoning.features.functional_pair_features import (  # noqa: E402
    FUNCTIONAL_FEATURE_NAMES,
    functional_pair_features,
)
from bio_reasoning.features.gene_embeddings import (  # noqa: E402
    build_gene_text,
    load_gene_embeddings,
)
from bio_reasoning.features.gene_function import load_go_terms  # noqa: E402
from bio_reasoning.features.go_terms import GoPairFeaturizer  # noqa: E402
from bio_reasoning.models.fuse import Channel, fuse  # noqa: E402
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR  # noqa: E402

# Measured incumbents / walls (see findings/).
DE_ORACLE_CEIL = 0.555  # de-unlearnable-oracle-ceiling.md — classifier-agnostic
DIR_CEIL = 0.651  # dir-ceiling-equal-weight-fusion.md — neighbour-DIR standalone
LB_TRACK_A = 0.586
LB_TRACK_B = 0.597
TABPFN_PRIMARY_MEAN = (0.552, 0.598)  # measured, 2 seeds — tabpfn-for-perturbation-tracks.md
TABPFN_COMBINER_DIR = 0.613
N_SEEDS = 5

# Modest, subsampled trees — guard the tiny-data (7.7k rows, ~10 features) overfitting
# gradient boosting is prone to. Not tuned: a stronger fit cannot cross a classifier-
# agnostic ceiling, and tuning on the val split would leak.
XGB_PARAMS = dict(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    reg_lambda=1.0,
    eval_metric="logloss",
    n_jobs=1,
)


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

NB_COL = CHANNELS.index("neighbour-DIR")


def _safe_auroc(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def _fit_p_positive(x_tr: np.ndarray, y: np.ndarray, x_va: np.ndarray, seed: int) -> np.ndarray:
    """Fit XGB and return P(class==1) on ``x_va``.

    Guards the degenerate single-class train fold at *fit* time: XGBoost rejects a
    lone-class ``y`` unless it is 0-indexed (all-``1`` raises), so short-circuit to a
    constant — 1.0 if the only class is the positive one, else 0.0.
    """
    classes = np.unique(y)
    if len(classes) < 2:
        return np.full(len(x_va), 1.0 if classes[0] == 1 else 0.0)
    clf = XGBClassifier(**XGB_PARAMS, random_state=seed).fit(x_tr, y)
    return clf.predict_proba(x_va)[:, list(clf.classes_).index(1)]


def xgb_two_stage(
    x_tr: np.ndarray, y_de: np.ndarray, y_up: np.ndarray, x_va: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Fit XGB P(DE) on all train rows and P(up|DE) on train DE rows; predict val.

    Returns ``(up_score, down_score)`` = ``P(DE)*P(up)`` and ``P(DE)*(1-P(up))``.
    """
    p_de = _fit_p_positive(x_tr, y_de, x_va, seed)
    p_up = _fit_p_positive(x_tr[y_de == 1], y_up, x_va, seed)
    return p_de * p_up, p_de * (1.0 - p_up)


def _impute(x: np.ndarray) -> np.ndarray:
    """Uncovered channel cells → 0.5 (neutral P(up)), matching fuse's fallback."""
    return np.where(np.isnan(x), 0.5, x)


def _primary_seed_row(
    df: pd.DataFrame,
    go_terms: dict[str, list[str]],
    partners: dict[str, set[str]],
    embeddings: dict,
    seed: int,
) -> dict:
    """Framing 1: XGB two-stage primary predictor vs GO heads + neighbour-DIR."""
    tr, va = holdout_split(df, seed=seed)
    assert_leak_free(df, tr, va)
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)

    kb = dict(go_terms=go_terms, partners=partners, embeddings=embeddings)
    x_tr = functional_pair_features(train_df["pert"], train_df["gene"], **kb)
    x_va = functional_pair_features(val_df["pert"], val_df["gene"], **kb)

    labels_tr = train_df["label"].to_numpy()
    y_de = (labels_tr != "none").astype(int)
    y_up = (labels_tr[y_de == 1] == "up").astype(int)

    up, down = xgb_two_stage(x_tr, y_de, y_up, x_va, seed)
    labels_va = val_df["label"].to_numpy()
    xgb = evaluate(labels_va, up, down)

    # Incumbent #1: GO two-stage learned heads, identical val rows.
    go_model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train_df["pert"], train_df["gene"], labels_tr
    )
    go_up, go_down = go_model.predict(val_df["pert"], val_df["gene"])
    go = evaluate(labels_va, go_up, go_down)

    # Incumbent #2: neighbour-DIR standalone direction (~0.651), identical val rows.
    r_nb = neighbour_dir_r(train_df, val_df, partners)
    de = labels_va != "none"
    is_up = (labels_va[de] == "up").astype(int)
    nb_cov = ~np.isnan(r_nb[de])
    nb_dir = _safe_auroc(is_up[nb_cov], r_nb[de][nb_cov])

    return {
        "seed": seed,
        "n_val_de": int(de.sum()),
        "xgb_de": xgb["auroc_de"],
        "xgb_dir": xgb["auroc_dir"],
        "xgb_mean": xgb["mean"],
        "go_de": go["auroc_de"],
        "go_dir": go["auroc_dir"],
        "go_mean": go["mean"],
        "nb_dir": nb_dir,
    }


def _combiner_seed_row(df: pd.DataFrame, embeddings: dict, partners: dict, seed: int) -> dict:
    """Framing 2: XGB learned combiner over the 3 DIR channels vs neighbour + equal-fuse."""
    tr, va = holdout_split(df, seed=seed)
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)

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

    x_va = dir_feature_matrix(
        train_df,
        val_df,
        partners=partners,
        embeddings=embeddings,
        pert_cache=PERT_CACHE,
        gene_cache=GENE_CACHE,
    )

    r_xgb = _fit_p_positive(x_fit, y_fit, _impute(x_va), seed)

    labels = val_df["label"].to_numpy()
    de = labels != "none"
    is_up = (labels[de] == "up").astype(int)

    r_nb = _impute(x_va[:, NB_COL])
    up, down = fuse([Channel(name=c, r=x_va[:, i]) for i, c in enumerate(CHANNELS)])

    return {
        "seed": seed,
        "n_fit": int(fit_mask.sum()),
        "n_val_de": int(de.sum()),
        "neighbour": _safe_auroc(is_up, r_nb[de]),
        "equal_fuse": evaluate(labels, up, down)["auroc_dir"],
        "xgb": _safe_auroc(is_up, r_xgb[de]),
    }


def _ms(rows: list[dict], key: str) -> tuple[float, float]:
    vals = [r[key] for r in rows]
    return float(np.nanmean(vals)), float(np.nanstd(vals))


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    print(f"train: {len(df)} rows, {len(syms)} unique symbols", flush=True)
    print(
        f"functional features ({len(FUNCTIONAL_FEATURE_NAMES)}): {FUNCTIONAL_FEATURE_NAMES}",
        flush=True,
    )

    go_terms = load_go_terms(syms, GENE_CACHE)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    gene_text = build_gene_text(syms, GO_TEXT_CACHE)
    embeddings = load_gene_embeddings(gene_text, EMB_CACHE)
    print(
        f"GO-term symbols {len(go_terms)}; STRING partners {len(partners)}; "
        f"embeddings {len(embeddings)}",
        flush=True,
    )

    # ---- Framing 1: primary two-stage predictor -------------------------------------
    prim = []
    for s in range(N_SEEDS):
        r = _primary_seed_row(df, go_terms, partners, embeddings, s)
        print(
            f"  [primary] seed {s} done: xgb(de {r['xgb_de']:.3f} dir {r['xgb_dir']:.3f} "
            f"mean {r['xgb_mean']:.3f}) go_mean {r['go_mean']:.3f} nb_dir {r['nb_dir']:.3f}",
            flush=True,
        )
        prim.append(r)

    print(
        "\n== FRAMING 1: XGBoost primary two-stage predictor ==\n"
        + f"{'seed':>4} {'n_de':>5} | "
        + f"{'xgb_de':>7} {'xgb_dir':>8} {'xgb_mean':>9} | "
        + f"{'go_de':>6} {'go_dir':>7} {'go_mean':>8} | {'nb_dir':>7}",
        flush=True,
    )
    for r in prim:
        print(
            f"{r['seed']:>4} {r['n_val_de']:>5} | "
            f"{r['xgb_de']:>7.3f} {r['xgb_dir']:>8.3f} {r['xgb_mean']:>9.3f} | "
            f"{r['go_de']:>6.3f} {r['go_dir']:>7.3f} {r['go_mean']:>8.3f} | {r['nb_dir']:>7.3f}",
            flush=True,
        )
    ps = {
        k: _ms(prim, k)
        for k in ("xgb_de", "xgb_dir", "xgb_mean", "go_de", "go_dir", "go_mean", "nb_dir")
    }
    print("\n-- mean ± sd (5 dual-OOD seeds, identical val rows) --", flush=True)
    print(
        f"  XGB 2-stage    DE {ps['xgb_de'][0]:.3f}±{ps['xgb_de'][1]:.3f}  "
        f"DIR {ps['xgb_dir'][0]:.3f}±{ps['xgb_dir'][1]:.3f}  "
        f"mean {ps['xgb_mean'][0]:.3f}±{ps['xgb_mean'][1]:.3f}",
        flush=True,
    )
    print(
        f"  GO 2-stage     DE {ps['go_de'][0]:.3f}±{ps['go_de'][1]:.3f}  "
        f"DIR {ps['go_dir'][0]:.3f}±{ps['go_dir'][1]:.3f}  "
        f"mean {ps['go_mean'][0]:.3f}±{ps['go_mean'][1]:.3f}",
        flush=True,
    )
    print(f"  neighbour-DIR  DIR {ps['nb_dir'][0]:.3f}±{ps['nb_dir'][1]:.3f}", flush=True)

    # ---- Framing 2: learned combiner over the 3 DIR channels -------------------------
    comb = [_combiner_seed_row(df, embeddings, partners, s) for s in range(N_SEEDS)]
    cols = ("neighbour", "equal_fuse", "xgb")
    print(
        "\n== FRAMING 2: XGBoost learned direction combiner ==\n"
        + f"{'seed':>4} | {'n_fit':>6} {'n_val':>6} | "
        + " | ".join(f"{c:>10}" for c in cols),
        flush=True,
    )
    for r in comb:
        cells = " | ".join(f"{r[c]:>10.3f}" for c in cols)
        print(f"{r['seed']:>4} | {r['n_fit']:>6} {r['n_val_de']:>6} | {cells}", flush=True)
    cm = {c: _ms(comb, c) for c in cols}
    print("\n-- DIR-AUROC (mean ± sd, 5 seeds), identical val rows --", flush=True)
    for c in cols:
        print(f"  {c:<12} {cm[c][0]:.3f} ± {cm[c][1]:.3f}", flush=True)

    # ---- Verdict --------------------------------------------------------------------
    print("\n== walls (measured, findings/) ==", flush=True)
    print(
        f"  DE oracle {DE_ORACLE_CEIL} | DIR ceiling {DIR_CEIL} | "
        f"LB A {LB_TRACK_A} / B {LB_TRACK_B} | "
        f"TabPFN primary mean {TABPFN_PRIMARY_MEAN} | TabPFN combiner DIR {TABPFN_COMBINER_DIR}",
        flush=True,
    )

    x_de, x_dir, x_mean = ps["xgb_de"][0], ps["xgb_dir"][0], ps["xgb_mean"][0]
    x_comb = cm["xgb"][0]
    beats_de_wall = x_de > DE_ORACLE_CEIL + 0.02
    beats_dir_primary = x_dir > DIR_CEIL + 0.005
    beats_lb = x_mean > max(LB_TRACK_A, LB_TRACK_B) + 0.005
    beats_dir_combiner = x_comb > DIR_CEIL + 0.005
    print("\n== VERDICT ==", flush=True)
    print(
        f"  [primary] DE {x_de:.3f} vs oracle {DE_ORACLE_CEIL}: "
        f"{'BREACHES wall (AUDIT FOR LEAKAGE)' if beats_de_wall else 'hits the DE wall (expected)'}",
        flush=True,
    )
    print(
        f"  [primary] DIR {x_dir:.3f} vs neighbour {DIR_CEIL}: "
        f"{'ADDS to direction' if beats_dir_primary else 'does NOT beat the direction ceiling'}",
        flush=True,
    )
    print(
        f"  [primary] mean {x_mean:.3f} vs incumbent LB {max(LB_TRACK_A, LB_TRACK_B)}: "
        f"{'BEATS incumbent → generate submission' if beats_lb else 'clean negative — no submission'}",
        flush=True,
    )
    print(
        f"  [combiner] DIR {x_comb:.3f} vs neighbour {DIR_CEIL}: "
        f"{'CLEARS the DIR ceiling' if beats_dir_combiner else 'does NOT clear the DIR ceiling'}",
        flush=True,
    )
    submit = beats_lb or beats_dir_primary or beats_dir_combiner
    print(
        f"\n  → {'GENERATE Track A submission' if submit else 'CLEAN NEGATIVE — no submission'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
