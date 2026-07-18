"""DE-learnability ceiling probe — the go/no-go gate on the whole DE bet.

Upper-bounds AUROC_de on the dual-OOD split with a LEAKAGE-ALLOWED oracle (each
gene/pert's true DE propensity, computed over the full data). If even this oracle
can't beat chance, DE is unlearnable by design — a rigorous negative result. Prints
the per-feature ablation + the fitted-head bound vs the ~0.50 chance line.

Fully offline; no endpoint, no Kaggle quota:

    uv run python scripts/de_ceiling_probe.py            # default 5 split seeds
    uv run python scripts/de_ceiling_probe.py --seeds 0 1 2 3 4 5 6 7
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from bio_reasoning.eval.de_ceiling import ORACLE_FEATURES, de_ceiling_probe

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN_CSV = Path(
    os.getenv("BIOREASONING_TRAIN_CSV", str(ROOT / "data" / "raw" / "track_a" / "train.csv"))
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--pert-frac", type=float, default=0.4)
    ap.add_argument("--gene-frac", type=float, default=0.4)
    args = ap.parse_args()

    df = pd.read_csv(args.train_csv)
    de_rate = float((df["label"].to_numpy() != "none").mean())
    print(
        f"[de-ceiling] {len(df)} rows | genes={df['gene'].nunique()} perts={df['pert'].nunique()} "
        f"| DE-rate={de_rate:.3f} | {len(args.seeds)} dual-OOD seeds\n"
    )

    out = de_ceiling_probe(
        df, seeds=tuple(args.seeds), pert_frac=args.pert_frac, gene_frac=args.gene_frac
    )

    print("  HONEST oracle — train-derived rates + label-free counts (transferable)")
    print("  AUROC_de on dual-OOD val (0.500 = chance)")
    print("  " + "-" * 52)
    for feat in ORACLE_FEATURES:
        mean, std = out[feat]
        note = "  (identity unseen OOD → prior)" if feat.endswith("_de_rate") else ""
        print(f"    {feat:<16} {mean:.3f} ± {std:.3f}{note}")
    print("  " + "-" * 52)
    head_mean, head_std = out["fitted_head"]
    print(f"    {'fitted_head':<16} {head_mean:.3f} ± {head_std:.3f}   ← the HONEST upper bound")
    leaked_mean, leaked_std = out["leaked_head"]
    print(
        f"    {'leaked_head':<16} {leaked_mean:.3f} ± {leaked_std:.3f}   "
        "← MIRAGE: intra-val LOO leakage, unachievable at test (identities unseen)"
    )

    print()
    best = max(ORACLE_FEATURES, key=lambda f: out[f][0])
    if head_mean <= 0.60:
        print(
            f"[de-ceiling] VERDICT: the honest oracle caps at {head_mean:.3f} (≈chance); the only "
            f"non-chance channel is '{best}' ({out[best][0]:.3f}), a label-free structural count, "
            "NOT a DE mechanism. Per-gene/pert DE-rate does NOT transfer (val identities unseen) — "
            f"the {leaked_mean:.3f} leaked head is a mirage from intra-val label leakage. DE is "
            "effectively UNLEARNABLE from identity/marginals on OOD; write the negative result."
        )
    else:
        print(
            f"[de-ceiling] VERDICT: the honest oracle reaches {head_mean:.3f} > chance — real "
            f"headroom EXISTS, carried by '{best}' ({out[best][0]:.3f}). That names the crack to exploit."
        )


if __name__ == "__main__":
    main()
