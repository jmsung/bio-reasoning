"""Goal 3/4 validation: is the neighbour-retrieval DIRECTION signal real (multi-seed)?

Fetches the full mouse-STRING neighbour graph once (cached), then measures the
neighbour-retrieval channel's DIR-AUROC and DE-AUROC on the dual-OOD val partition
across seeds 0-4. Prints a table + means. Run: `uv run python scripts/de_retrieval_dir_validation.py`.
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
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.neighbor_retrieval import neighbor_channel

# Data is gitignored/local; a fresh worktree has none, so fall back to the sibling cb/ checkout.
_ROOT = Path(__file__).resolve().parents[1]
TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or str(_ROOT / "data" / "raw" / "track_a" / "train.csv")
if not os.path.exists(TRAIN):
    TRAIN = str(_ROOT.parent / "cb" / "data" / "raw" / "track_a" / "train.csv")
CACHE = "data/external/string_partners_universe.json"


def _fetch_universe(syms: list[str]) -> dict[str, set[str]]:
    if os.path.exists(CACHE):
        return {k: set(v) for k, v in json.load(open(CACHE)).items()}
    base = "https://string-db.org/api/json/interaction_partners"
    out: dict[str, set[str]] = {}
    for i in range(0, len(syms), 60):
        data = urllib.parse.urlencode(
            {"identifiers": "\n".join(syms[i : i + 60]), "species": 10090, "limit": 500}
        ).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(base, data=data), timeout=90) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print("fetch err", i, repr(e), flush=True)
            rows = []
        for e in rows:
            out.setdefault(e["preferredName_A"], set()).add(e["preferredName_B"])
        time.sleep(1)
    os.makedirs("data/external", exist_ok=True)
    json.dump({k: sorted(v) for k, v in out.items()}, open(CACHE, "w"))
    return out


def _seed_aurocs(df, partners, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    tp = set(train["pert"].astype(str))
    tg = set(train["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val["gene"].astype(str).unique()}
    ch = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)
    lab = val["label"].to_numpy()
    de = (lab != "none").astype(int)
    cov = np.isfinite(ch.s_de)
    de_auroc = roc_auc_score(de[cov], ch.s_de[cov]) if len(set(de[cov])) > 1 else float("nan")
    dm = np.isfinite(ch.r) & (lab != "none")
    dt = (lab[dm] == "up").astype(int)
    dir_auroc = roc_auc_score(dt, ch.r[dm]) if len(set(dt)) > 1 else float("nan")
    return dir_auroc, de_auroc, cov.mean(), int(dm.sum())


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    partners = _fetch_universe(syms)
    print(f"universe partners: {len(partners)} symbols", flush=True)
    rows = [_seed_aurocs(df, partners, s) for s in range(5)]
    print("seed | DIR-AUROC | DE-AUROC | cov | n_DE_covered", flush=True)
    for s, (d, e, c, n) in enumerate(rows):
        print(f"  {s}  |  {d:.3f}   |  {e:.3f}  | {c:.0%} | {n}", flush=True)
    dirs = [r[0] for r in rows]
    des = [r[1] for r in rows]
    print(f"\nDIR mean={np.mean(dirs):.3f} ± {np.std(dirs):.3f}  (vs current ~0.58)", flush=True)
    print(f"DE  mean={np.mean(des):.3f} ± {np.std(des):.3f}  (chance ~0.50)", flush=True)


if __name__ == "__main__":
    main()
