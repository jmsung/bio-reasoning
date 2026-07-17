"""Goal 3: gate + eval the gene-embedding DIRECTION channel on OOD-val.

Multi-seed (0-4) on the dual-OOD ``holdout_split``. Per seed: fit the
GenePert-style ridge on the train fold's DE rows, score val → standalone
**DIR-AUROC** among DE rows + coverage, and (diversity) the Spearman correlation
of its ``r`` against the neighbour-retrieval DIR channel on the shared DE-covered
rows. Admit iff DIR-AUROC ≥ 0.55 AND |corr| ≤ 0.5 (a direction analogue of the
DE-only ``cfa_gate``) — the incumbent DIR lever is ~0.647.

Embeds each symbol's GO:BP text once (OpenAI, cached to ``data/external``); the
GO text itself is fetched from mygene.info once (cached). Run:
``uv run python scripts/gene_embedding_eval.py``.
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
from dotenv import load_dotenv
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

from bio_reasoning.eval.split import holdout_split  # noqa: E402
from bio_reasoning.features.gene_embeddings import (  # noqa: E402
    build_gene_text,
    fit_direction_ridge,
    gene_embedding_channel,
    load_gene_embeddings,
)
from bio_reasoning.features.neighbor_retrieval import neighbor_channel  # noqa: E402


def _data(rel: str) -> str:
    """Resolve a gitignored data path in the worktree, else the sibling cb/ checkout."""
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or _data("data/raw/track_a/train.csv")
GO_CACHE = _data("data/external/go_terms_universe.json")
EMB_CACHE = _ROOT / "data" / "external" / "gene_embeddings.json"
STRING_CACHE = _data("data/external/string_partners_universe.json")
DIR_BASELINE = 0.647


def _gene_text(symbols: list[str], batch: int = 100) -> dict[str, str]:
    """Build {symbol: GO-text} in batches so the GO cache persists incrementally."""
    text: dict[str, str] = {}
    for i in range(0, len(symbols), batch):
        text.update(build_gene_text(symbols[i : i + batch], GO_CACHE))
        print(f"  GO text {min(i + batch, len(symbols))}/{len(symbols)}", flush=True)
    return text


def _string_partners(syms: list[str]) -> dict[str, set[str]]:
    """Mouse-STRING interaction partners per symbol (cached) — for the diversity check."""
    if os.path.exists(STRING_CACHE):
        return {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
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
            print("STRING fetch err", i, repr(e), flush=True)
            rows = []
        for e in rows:
            out.setdefault(e["preferredName_A"], set()).add(e["preferredName_B"])
        time.sleep(1)
    os.makedirs(os.path.dirname(STRING_CACHE), exist_ok=True)
    json.dump({k: sorted(v) for k, v in out.items()}, open(STRING_CACHE, "w"))
    return out


def _neighbor_r(
    train: pd.DataFrame, val: pd.DataFrame, partners: dict[str, set[str]]
) -> np.ndarray:
    """Neighbour-retrieval DIR score on val rows (the incumbent DIR channel), for diversity."""
    tp = set(train["pert"].astype(str))
    tg = set(train["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val["gene"].astype(str).unique()}
    ch = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)
    return ch.r


def _seed_row(df: pd.DataFrame, embeddings: dict, partners: dict, seed: int) -> dict:
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train = df.iloc[tr].reset_index(drop=True)
    val = df.iloc[va].reset_index(drop=True)
    lab = val["label"].to_numpy()

    ridge = fit_direction_ridge(train, embeddings)
    ch = gene_embedding_channel(val[["pert", "gene"]], ridge, embeddings)

    dm = np.isfinite(ch.r) & (lab != "none")
    dt = (lab[dm] == "up").astype(int)
    dir_auroc = float(roc_auc_score(dt, ch.r[dm])) if len(set(dt.tolist())) > 1 else float("nan")

    nb_r = _neighbor_r(train, val, partners)
    both = np.isfinite(ch.r) & np.isfinite(nb_r) & (lab != "none")
    if int(both.sum()) >= 2:
        rho = spearmanr(ch.r[both], nb_r[both])[0]
        corr = float(abs(rho)) if np.isfinite(rho) else 0.0
    else:
        corr = 0.0

    admit = (dir_auroc >= 0.55) and (corr <= 0.5)
    return {
        "seed": seed,
        "cov": float(np.isfinite(ch.r).mean()),
        "dir_auroc": dir_auroc,
        "corr": corr,
        "n_de": int(dm.sum()),
        "admit": admit,
    }


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df["pert"].astype(str)) | set(df["gene"].astype(str)))
    print(
        f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes, "
        f"{len(syms)} unique symbols",
        flush=True,
    )

    print("building GO text (cached)…", flush=True)
    gene_text = _gene_text(syms)
    print("embedding symbols (OpenAI, cached)…", flush=True)
    embeddings = load_gene_embeddings(gene_text, EMB_CACHE)
    print(
        f"  embedded {len(embeddings)} symbols (dim {next(iter(embeddings.values())).shape[0]})",
        flush=True,
    )
    print("fetching STRING partners for diversity (cached)…", flush=True)
    partners = _string_partners(syms)

    rows = [_seed_row(df, embeddings, partners, s) for s in range(5)]

    print("\nseed | cov | DIR-AUROC | corr(vs nbr-DIR) | n_DE | admit", flush=True)
    for r in rows:
        print(
            f"  {r['seed']}  | {r['cov']:.0%} |   {r['dir_auroc']:.3f}   |      {r['corr']:.3f}"
            f"       | {r['n_de']:>4} | {r['admit']}",
            flush=True,
        )

    def _m(k: str) -> tuple[float, float]:
        v = np.array([r[k] for r in rows], dtype=float)
        return float(np.nanmean(v)), float(np.nanstd(v))

    dm, ds = _m("dir_auroc")
    cm, cs = _m("corr")
    n_admit = sum(r["admit"] for r in rows)
    print(
        f"\nDIR-AUROC mean={dm:.3f} ± {ds:.3f}  (incumbent neighbour-DIR ~{DIR_BASELINE})",
        flush=True,
    )
    print(f"corr vs nbr-DIR mean={cm:.3f} ± {cs:.3f}  (diverse if ≤ 0.5)", flush=True)
    print(f"admitted {n_admit}/5 seeds (DIR-AUROC ≥ 0.55 AND |corr| ≤ 0.5).", flush=True)
    verdict = "ADMIT — a real, diverse DIR channel" if n_admit >= 3 else "REJECT"
    print(f"VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
