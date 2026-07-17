"""Goal 2: does a MARGINAL DE channel (per-symbol STRING degree) beat chance on OOD-val?

Builds per-symbol connectivity (STRING interaction degree, mouse taxid 10090) for
train+val symbols, fits a logistic head on the two marginal features
``[log1p(pert_degree), log1p(gene_degree)]`` over the train partition, and measures
standalone DE-AUROC on the dual-OOD val partition (seeds 0-4), compared against the
``cfa_gate`` 0.55 admission bar. Decisive: clears 0.55 → a real new DE lever; ~chance
→ the DE axis is declared done (6 channels, marginal + pairwise, all chance).

Run: uv run --group eval python scripts/marginal_de_eval.py
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.marginal_properties import marginal_features

_ROOT = Path(__file__).resolve().parents[1]
_DATA = (
    _ROOT / "data"
    if (_ROOT / "data/raw/track_a/train.csv").exists()
    else _ROOT.parent / "cb" / "data"
)
TRAIN = str(_DATA / "raw/track_a/train.csv")
DEGREE_CACHE = str(_DATA / "external/string_degree.json")


def _string_degree(syms: list[str]) -> dict[str, float]:
    """Per-symbol STRING interaction degree (partner count), cached; public API."""
    if os.path.exists(DEGREE_CACHE):
        return json.load(open(DEGREE_CACHE))
    base = "https://string-db.org/api/json/interaction_partners"
    deg: dict[str, float] = {}
    for i in range(0, len(syms), 60):
        data = urllib.parse.urlencode(
            {"identifiers": "\n".join(syms[i : i + 60]), "species": 10090, "limit": 2000}
        ).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(base, data=data), timeout=90) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print("fetch err", i, repr(e), flush=True)
            rows = []
        for row in rows:
            deg[row["preferredName_A"]] = deg.get(row["preferredName_A"], 0) + 1
        time.sleep(1)
    os.makedirs(os.path.dirname(DEGREE_CACHE), exist_ok=True)
    json.dump(deg, open(DEGREE_CACHE, "w"))
    return deg


def _seed(df, degree, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va]
    Xtr = marginal_features(train.pert.tolist(), train.gene.tolist(), degree, log1p=True)
    Xva = marginal_features(val.pert.tolist(), val.gene.tolist(), degree, log1p=True)
    de_tr = (train.label.to_numpy() != "none").astype(int)
    de_va = (val.label.to_numpy() != "none").astype(int)
    if len(set(de_tr)) < 2:
        return float("nan")
    head = LogisticRegression(max_iter=1000).fit(Xtr, de_tr)
    s_de = head.predict_proba(Xva)[:, 1]
    return roc_auc_score(de_va, s_de) if len(set(de_va)) > 1 else float("nan")


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    degree = _string_degree(syms)
    cov = np.mean([str(s) in degree for s in syms])
    print(f"symbols with a STRING degree: {cov:.1%} of {len(syms)}", flush=True)
    aurocs = [_seed(df, degree, s) for s in range(5)]
    for s, a in enumerate(aurocs):
        print(f"seed {s}: DE-AUROC {a:.3f}", flush=True)
    m, sd = float(np.nanmean(aurocs)), float(np.nanstd(aurocs))
    print(f"\nmarginal DE-AUROC = {m:.3f} ± {sd:.3f}  (chance 0.50; CFA bar 0.55)", flush=True)
    print(
        "VERDICT:",
        (
            "CLEARS 0.55 — real DE lever"
            if m >= 0.55
            else "~chance — DE axis declared done (6th dead channel)"
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
