"""TabPFN as the PRIMARY Track A predictor over rich functional features.

Framing #2 from ``knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md`` — the
one rules-legal, still-untried tabular-FM lever (framing #1, TabPFN-as-combiner, is
already dead: DIR 0.613 < 0.651). Here TabPFN *is* the model: a two-stage
``P(DE) · P(up|DE)`` predictor over the dense functional pair features
(``features/functional_pair_features.py`` — GO overlap, STRING degree/adjacency,
embedding cosine), the same knowledge sources the incumbent channels draw on.

Leak-free by construction: every feature is a pure function of ``(pert, gene)``
identity plus static external knowledge (never labels), and TabPFN trains only on the
dual-OOD train partition, where ``holdout_split`` holds out every val pert AND gene
(``assert_leak_free`` guards it). So there is no path for a val label to reach a
val feature, and no train identity overlaps a val identity.

Reports, on identical val rows, 5 dual-OOD seeds:
  - TabPFN two-stage: AUROC_de, AUROC_dir, mean
  - GO two-stage (the incumbent learned heads): AUROC_de, AUROC_dir, mean
  - neighbour-DIR standalone: AUROC_dir (the ~0.651 direction incumbent)

Walls to check (all measured, in findings): DE oracle ceiling 0.555 (TabPFN cannot
beat it); direction ceiling ~0.651 (neighbour-DIR); Track A / B LB 0.586 / 0.597.

Measurement-only: touches nothing in the submission pipeline.
Run: ``uv run --no-group eval --group tabpfn python scripts/tabpfn_predictor_eval.py``
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

from bio_reasoning.eval.direction_channels import neighbour_dir_r  # noqa: E402
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
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR  # noqa: E402

# Measured incumbents / walls (see findings/).
DE_ORACLE_CEIL = 0.555  # de-unlearnable-oracle-ceiling.md — TabPFN cannot beat this
DIR_CEIL = 0.651  # dir-ceiling-equal-weight-fusion.md — neighbour-DIR standalone
LB_TRACK_A = 0.586
LB_TRACK_B = 0.597
N_SEEDS = 5


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


def _safe_auroc(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def _tabpfn_two_stage(
    x_tr: np.ndarray, y_de: np.ndarray, y_up: np.ndarray, x_va: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Fit TabPFN P(DE) on all train rows and P(up|DE) on train DE rows; predict val."""
    de_clf = TabPFNClassifier(random_state=0).fit(x_tr, y_de)
    p_de = de_clf.predict_proba(x_va)[:, list(de_clf.classes_).index(1)]

    dir_clf = TabPFNClassifier(random_state=0).fit(x_tr[y_de == 1], y_up)
    dclasses = list(dir_clf.classes_)
    if 1 in dclasses:
        p_up = dir_clf.predict_proba(x_va)[:, dclasses.index(1)]
    else:  # degenerate single-direction train fold — constant
        p_up = np.full(len(x_va), float(dclasses[0]))
    return p_de * p_up, p_de * (1.0 - p_up)


def _seed_row(
    df: pd.DataFrame,
    go_terms: dict[str, list[str]],
    partners: dict[str, set[str]],
    embeddings: dict,
    seed: int,
) -> dict:
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

    up, down = _tabpfn_two_stage(x_tr, y_de, y_up, x_va)
    labels_va = val_df["label"].to_numpy()
    tab = evaluate(labels_va, up, down)

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
        "tab_de": tab["auroc_de"],
        "tab_dir": tab["auroc_dir"],
        "tab_mean": tab["mean"],
        "go_de": go["auroc_de"],
        "go_dir": go["auroc_dir"],
        "go_mean": go["mean"],
        "nb_dir": nb_dir,
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

    go_terms = load_go_terms(syms, GENE_CACHE)  # GO:BP terms per symbol (pert & gene share)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    gene_text = build_gene_text(syms, GO_TEXT_CACHE)
    embeddings = load_gene_embeddings(gene_text, EMB_CACHE)
    print(
        f"GO-term symbols {len(go_terms)}; STRING partners {len(partners)}; "
        f"embeddings {len(embeddings)}",
        flush=True,
    )

    rows = []
    for s in range(N_SEEDS):
        r = _seed_row(df, go_terms, partners, embeddings, s)
        print(
            f"  seed {s} done: tab(de {r['tab_de']:.3f} dir {r['tab_dir']:.3f} "
            f"mean {r['tab_mean']:.3f}) go_mean {r['go_mean']:.3f} nb_dir {r['nb_dir']:.3f}",
            flush=True,
        )
        rows.append(r)

    print(
        "\n"
        + f"{'seed':>4} {'n_de':>5} | "
        + f"{'tab_de':>7} {'tab_dir':>8} {'tab_mean':>9} | "
        + f"{'go_de':>6} {'go_dir':>7} {'go_mean':>8} | {'nb_dir':>7}",
        flush=True,
    )
    for r in rows:
        print(
            f"{r['seed']:>4} {r['n_val_de']:>5} | "
            f"{r['tab_de']:>7.3f} {r['tab_dir']:>8.3f} {r['tab_mean']:>9.3f} | "
            f"{r['go_de']:>6.3f} {r['go_dir']:>7.3f} {r['go_mean']:>8.3f} | {r['nb_dir']:>7.3f}",
            flush=True,
        )

    stats = {
        k: _ms(rows, k)
        for k in ("tab_de", "tab_dir", "tab_mean", "go_de", "go_dir", "go_mean", "nb_dir")
    }
    print("\n== mean ± sd (5 dual-OOD seeds, identical val rows) ==", flush=True)
    print(
        f"  TabPFN 2-stage   DE {stats['tab_de'][0]:.3f}±{stats['tab_de'][1]:.3f}  "
        f"DIR {stats['tab_dir'][0]:.3f}±{stats['tab_dir'][1]:.3f}  "
        f"mean {stats['tab_mean'][0]:.3f}±{stats['tab_mean'][1]:.3f}",
        flush=True,
    )
    print(
        f"  GO 2-stage       DE {stats['go_de'][0]:.3f}±{stats['go_de'][1]:.3f}  "
        f"DIR {stats['go_dir'][0]:.3f}±{stats['go_dir'][1]:.3f}  "
        f"mean {stats['go_mean'][0]:.3f}±{stats['go_mean'][1]:.3f}",
        flush=True,
    )
    print(f"  neighbour-DIR    DIR {stats['nb_dir'][0]:.3f}±{stats['nb_dir'][1]:.3f}", flush=True)

    print("\n== walls (measured, findings/) ==", flush=True)
    print(
        f"  DE oracle ceiling {DE_ORACLE_CEIL} | DIR ceiling {DIR_CEIL} | "
        f"LB Track A {LB_TRACK_A} / B {LB_TRACK_B}",
        flush=True,
    )

    tab_de, tab_dir, tab_mean = stats["tab_de"][0], stats["tab_dir"][0], stats["tab_mean"][0]
    beats_de_wall = tab_de > DE_ORACLE_CEIL + 0.02
    beats_dir = tab_dir > DIR_CEIL + 0.005
    beats_lb = tab_mean > max(LB_TRACK_A, LB_TRACK_B) + 0.005
    print("\n== VERDICT ==", flush=True)
    print(
        f"  DE {tab_de:.3f} vs oracle {DE_ORACLE_CEIL}: "
        f"{'BREACHES wall (AUDIT FOR LEAKAGE)' if beats_de_wall else 'hits the DE wall (expected)'}",
        flush=True,
    )
    print(
        f"  DIR {tab_dir:.3f} vs neighbour {DIR_CEIL}: "
        f"{'ADDS to direction' if beats_dir else 'does NOT beat the direction ceiling'}",
        flush=True,
    )
    print(
        f"  mean {tab_mean:.3f} vs incumbent LB {max(LB_TRACK_A, LB_TRACK_B)}: "
        f"{'BEATS incumbent → generate submission' if beats_lb else 'clean negative — no submission'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
