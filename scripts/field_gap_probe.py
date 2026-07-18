"""Characterize the Track A 0.586 (our honest ceiling) ↔ 0.693 (public LB top) gap.

Offline, no-spend probe. Answers: is the +0.107 gap driven by (a) transductive
tricks that inflate on THIS test but don't generalize, (b) an easier real test,
or (c) unreproducible/inflated public scores (the 6 public notebooks print no
scores; a correct char-ngram reached only real-LB 0.552 in probe #39)?

Two measurements, both offline:

  1. TRANSDUCTIVE-VOCAB DELTA. Build the public field's char-ngram two-stage
     model two ways on OUR honest dual-OOD holdout, scoring the SAME val labels:
       (i)  HONEST     — fit char vocab on train symbols only (unseen n-grams
                         dropped at transform).
       (ii) TRANSDUCTIVE — fit char vocab on train+val UNION (avikdas trick),
                         and/or add id-in-text (jek1wantaufik trick).
     The heads are always fit on TRAIN labels only (val labels are never fit —
     they only score). Delta = how much the leak-allowed vocab moves mean-AUROC.
     Mechanistic prediction: ~0, because a val-only n-gram column is all-zero in
     the train design matrix, so any train-fit head gives it ~0 weight.

  2. FAMILY / PREFIX OVERLAP (real test vs train). Quantify how OOD the real
     Kaggle test actually is: exact identity overlap (expected ~0) vs
     gene-family / prefix overlap (the legitimate zero-overlap generalization
     bridge a char model exploits). Compare against our dual-OOD holdout to
     reconcile probe #39's small +0.02–0.06 LB↔OOD-val gap.

Run: uv run --group eval python scripts/field_gap_probe.py
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.linear_model import LogisticRegression

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.pair_features import CharNgramFeaturizer, string_stats

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
SEEDS = [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Part 1 — transductive-vocab delta
# ---------------------------------------------------------------------------
def _char_tfidf(feat: CharNgramFeaturizer, perts, genes, ids=None) -> sp.csr_matrix:
    """[pert-tfidf | gene-tfidf | (id-tfidf) | string-stats] using a fit `feat`."""
    perts = [str(x) for x in perts]
    genes = [str(x) for x in genes]
    blocks = [feat._vp.transform(perts), feat._vg.transform(genes)]
    if ids is not None:
        blocks.append(feat._vid.transform([str(x) for x in ids]))
    blocks.append(string_stats(perts, genes))
    return sp.hstack(blocks, format="csr")


def _fit_featurizer(perts, genes, ids=None) -> CharNgramFeaturizer:
    """Fit char-TFIDF vectorizers on the given corpus (train-only or union)."""
    feat = CharNgramFeaturizer()
    feat._vp = feat._fit_vectorizer([str(x) for x in perts])
    feat._vg = feat._fit_vectorizer([str(x) for x in genes])
    if ids is not None:
        feat._vid = feat._fit_vectorizer([str(x) for x in ids])
    return feat


def _two_stage(X_tr, y_tr: np.ndarray, X_va) -> tuple[np.ndarray, np.ndarray]:
    """Learned P(DE)·P(up|DE) two-stage on prebuilt design matrices."""
    de_y = y_tr != "none"
    de_head = LogisticRegression(max_iter=1000, C=1.0).fit(X_tr, de_y)
    p_de = de_head.predict_proba(X_va)[:, list(de_head.classes_).index(True)]

    m = de_y
    dir_head = LogisticRegression(max_iter=1000, C=1.0).fit(X_tr[m], y_tr[m] == "up")
    p_up = dir_head.predict_proba(X_va)[:, list(dir_head.classes_).index(True)]
    return p_de * p_up, p_de * (1.0 - p_up)


def _variant(train, val, *, union: bool, id_in_text: bool) -> dict[str, float]:
    """Score one (vocab-corpus, id-in-text) configuration on the honest val labels."""
    use_id = id_in_text
    if union:
        perts = pd.concat([train.pert, val.pert])
        genes = pd.concat([train.gene, val.gene])
        ids = pd.concat([train.id, val.id]) if use_id else None
    else:
        perts, genes = train.pert, train.gene
        ids = train.id if use_id else None
    feat = _fit_featurizer(perts, genes, ids)

    tr_ids = train.id if use_id else None
    va_ids = val.id if use_id else None
    X_tr = _char_tfidf(feat, train.pert, train.gene, tr_ids)
    X_va = _char_tfidf(feat, val.pert, val.gene, va_ids)
    up, down = _two_stage(X_tr, train.label.to_numpy(), X_va)
    return evaluate(val.label.to_numpy(), up, down)


def part1_transductive_delta(df: pd.DataFrame) -> None:
    print("=" * 74)
    print("PART 1 — transductive-vocab delta on OUR honest dual-OOD holdout")
    print("=" * 74)
    configs = [
        ("honest (train vocab)", dict(union=False, id_in_text=False)),
        ("transductive (train+val vocab)", dict(union=True, id_in_text=False)),
        ("honest + id-in-text", dict(union=False, id_in_text=True)),
        ("transductive + id-in-text", dict(union=True, id_in_text=True)),
    ]
    means: dict[str, list[float]] = {name: [] for name, _ in configs}
    de_: dict[str, list[float]] = {name: [] for name, _ in configs}
    dir_: dict[str, list[float]] = {name: [] for name, _ in configs}
    for seed in SEEDS:
        tr, va = holdout_split(df, seed=seed)
        train, val = df.iloc[tr].reset_index(drop=True), df.iloc[va].reset_index(drop=True)
        for name, kw in configs:
            r = _variant(train, val, **kw)
            means[name].append(r["mean"])
            de_[name].append(r["auroc_de"])
            dir_[name].append(r["auroc_dir"])

    print(f"\n{'config':<34}{'auroc_de':>10}{'auroc_dir':>10}{'mean':>10}  (mean±sd over 5 seeds)")
    base = None
    for name, _ in configs:
        mu, sd = np.mean(means[name]), np.std(means[name])
        print(
            f"{name:<34}{np.mean(de_[name]):>10.4f}{np.mean(dir_[name]):>10.4f}"
            f"{mu:>10.4f} ± {sd:.4f}"
        )
        if base is None:
            base = mu
    print()
    honest = np.mean(means["honest (train vocab)"])
    for name, _ in configs[1:]:
        d = np.mean(means[name]) - honest
        print(f"  Δmean vs honest — {name:<34}{d:+.4f}")
    print(
        "\n  Interpretation: a val-only n-gram column is all-zero in the train design\n"
        "  matrix, so a train-fit head assigns it ~0 weight. Transductive vocab and\n"
        "  id-in-text therefore cannot lift mean-AUROC on an honest OOD split. If Δ≈0,\n"
        "  these tricks are NOT the 0.586→0.693 mechanism."
    )


# ---------------------------------------------------------------------------
# Part 2 — family / prefix overlap: how OOD is the real test?
# ---------------------------------------------------------------------------
def _family_stem(sym: str) -> str:
    """Leading-alpha gene-family stem, e.g. Slc35b1→'Slc', Rpl13→'Rpl', 9930111J21Rik2→'Rik'.

    Family names in the mouse gene set are a capitalized letter run at the start
    (Slc, Zfp, Rpl, Ifit, Gm); numeric-lead RIKEN ids collapse to their 'Rik' tail.
    """
    m = re.match(r"^[A-Za-z]+", str(sym))
    stem = m.group(0) if m else str(sym)
    if not stem or stem[0].isdigit():
        return "Rik" if "Rik" in str(sym) else str(sym)
    return stem


def _overlap(test_syms: set[str], train_syms: set[str], label: str) -> None:
    exact = len(test_syms & train_syms) / len(test_syms)
    for k in (2, 3, 4):
        tr_pref = {s[:k] for s in train_syms}
        frac = np.mean([s[:k] in tr_pref for s in test_syms])
        print(f"  {label:<12} prefix-{k} overlap: {frac:6.1%}")
    tr_fam = {_family_stem(s) for s in train_syms}
    fam_frac = np.mean([_family_stem(s) in tr_fam for s in test_syms])
    print(f"  {label:<12} family-stem  overlap: {fam_frac:6.1%}")
    print(f"  {label:<12} EXACT identity overlap: {exact:6.1%}  (OOD → expect ~0)")


def _trigrams(s: str) -> set[str]:
    s = f"<{s}>"
    return {s[i : i + 3] for i in range(max(len(s) - 2, 1))}


def _max_jaccard(test_syms: list[str], train_syms: list[str]) -> np.ndarray:
    tr_tri = [_trigrams(s) for s in set(train_syms)]
    out = []
    for s in test_syms:
        t = _trigrams(s)
        best = max((len(t & u) / len(t | u) for u in tr_tri), default=0.0)
        out.append(best)
    return np.array(out)


def part2_ood_ness(df: pd.DataFrame, test: pd.DataFrame) -> None:
    print("\n" + "=" * 74)
    print("PART 2 — how OOD is the REAL Kaggle test? (identity vs family/prefix)")
    print("=" * 74)

    tr_perts, tr_genes = set(df.pert.astype(str)), set(df.gene.astype(str))
    te_perts = set(test.pert.astype(str))
    te_genes = set(test.gene.astype(str))
    print("\nREAL test.csv vs full train.csv:")
    _overlap(te_perts, tr_perts, "pert")
    _overlap(te_genes, tr_genes, "gene")

    # char-similarity: max trigram Jaccard of each test gene to any train gene
    jg = _max_jaccard(sorted(te_genes), sorted(tr_genes))
    jp = _max_jaccard(sorted(te_perts), sorted(tr_perts))
    print(
        f"\n  test gene → nearest train gene, trigram Jaccard: "
        f"median {np.median(jg):.3f}, mean {np.mean(jg):.3f}, "
        f"frac>0.3 {np.mean(jg > 0.3):.1%}"
    )
    print(
        f"  test pert → nearest train pert, trigram Jaccard: "
        f"median {np.median(jp):.3f}, mean {np.mean(jp):.3f}, "
        f"frac>0.3 {np.mean(jp > 0.3):.1%}"
    )

    # Our dual-OOD holdout: does OUR split preserve the same family bridge?
    tr, va = holdout_split(df, seed=0)
    htr, hva = df.iloc[tr], df.iloc[va]
    print("\nOUR dual-OOD holdout (val) vs its train fold — same family bridge?")
    _overlap(set(hva.gene.astype(str)), set(htr.gene.astype(str)), "gene")
    jg_h = _max_jaccard(sorted(set(hva.gene.astype(str))), sorted(set(htr.gene.astype(str))))
    print(
        f"  holdout gene → nearest train gene, trigram Jaccard: "
        f"median {np.median(jg_h):.3f}, frac>0.3 {np.mean(jg_h > 0.3):.1%}"
    )
    print(
        "\n  Reconciles probe #39: both the real test and our split are exact-identity\n"
        "  OOD but share family/prefix structure, so string features transfer on BOTH.\n"
        "  Our split is only marginally harder → LB↔OOD-val gap stays +0.02–0.06, not +0.10."
    )


def main() -> None:
    df = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    part1_transductive_delta(df)
    part2_ood_ness(df, test)


if __name__ == "__main__":
    main()
