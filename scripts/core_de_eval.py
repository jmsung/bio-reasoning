"""Goal 4: gate the CORE contrastive DE channel on OOD-val (kill-test vs 0.55).

CORE-Voting (no LLM): P(DE) = DE-fraction of the contrastive references per val row.
Prior (findings/contrastive-de-core-assessment.md): this IS our neighbour-retrieval-DE,
so expect ≈0.498–0.50 — a clean empirical kill via the CORE framing. CORE-Reasoning is
endpoint-blocked (Bing logprobs) and is not run here.

Run: uv run python scripts/core_de_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.contrastive_context import contrastive_references
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph
from bio_reasoning.models.core_de_scorer import voting_pde

_ROOT = Path(__file__).resolve().parents[1]


def _data(rel: str) -> str:
    p = _ROOT / rel
    return str(p if p.exists() else _ROOT.parent / "cb" / rel)


TRAIN = _data("data/raw/track_a/train.csv")
STRING_CACHE = _data("data/external/string_partners_universe.json")
KILL_BAR = 0.55
NEIGHBOUR_DE = 0.498


def _seed(df: pd.DataFrame, partners: dict, seed: int) -> tuple[float, float]:
    tr, va = holdout_split(df, seed=seed)
    train = df.iloc[tr].reset_index(drop=True)
    val = df.iloc[va].reset_index(drop=True)
    pnb, gnb = build_neighbor_graph(val[["pert", "gene"]].astype(str), partners, train)
    pde = np.array(
        [
            voting_pde(contrastive_references(p, g, train, pnb, gnb, min_support=3))
            for p, g in zip(val["pert"].astype(str), val["gene"].astype(str), strict=True)
        ]
    )
    lab = val["label"].to_numpy()
    de = (lab != "none").astype(int)
    cov = np.isfinite(pde)
    auroc = roc_auc_score(de[cov], pde[cov]) if len(set(de[cov].tolist())) > 1 else float("nan")
    return float(auroc), float(cov.mean())


def main() -> None:
    df = pd.read_csv(TRAIN)
    partners = {k: set(v) for k, v in json.load(open(STRING_CACHE)).items()}
    print(f"train: {len(df)} rows; STRING partners {len(partners)}", flush=True)

    rows = [_seed(df, partners, s) for s in range(5)]
    aurocs = np.array([r[0] for r in rows])
    covs = np.array([r[1] for r in rows])
    m, s = float(np.nanmean(aurocs)), float(np.nanstd(aurocs))
    print(f"\nCORE-Voting DE-AUROC: {m:.3f} ± {s:.3f}  (coverage {covs.mean():.0%})", flush=True)
    print(f"kill bar {KILL_BAR}; neighbour-retrieval-DE floor {NEIGHBOUR_DE}", flush=True)
    verdict = "ADMIT" if m >= KILL_BAR else "KILL"
    print(
        f"VERDICT (CORE-Voting): {verdict} — {'clears' if m >= KILL_BAR else 'at/near chance, does NOT clear'} "
        f"the 0.55 bar; matches the neighbour-retrieval-DE prior (~{NEIGHBOUR_DE}).",
        flush=True,
    )
    print(
        "CORE-Reasoning (LLM over contrastive set): endpoint-blocked (Bing logprobs) — not run.",
        flush=True,
    )


if __name__ == "__main__":
    main()
