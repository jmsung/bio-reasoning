"""Preflight the self-improvement loop — run ONE real smoke trial, assert it is healthy.

The full-val gate costs hours per trial, so a bug (deadlock, auth-401, empty responses,
empty-eval) can burn a whole night before it surfaces. This runs a single real trial on a
DEV-ONLY val subsample (``--val-n``, minutes not hours) and ASSERTS the loop is genuinely
working — non-empty response content AND a trial that archives with a real (non-nan) mean
over a non-empty val — codifying the lesson that liveness ≠ working
(mb/findings/loop-runtime-deadlock-throughput-verification.md).

Exit 0 = cleared to run unattended; exit 1 = a degenerate mode fired (message says which).

    uv run python scripts/verify_loop.py --val-n 80

Backend + key resolution: see ``bio_reasoning.trial_loop.inference`` (OpenRouter env).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.preflight import PreflightError, run_preflight

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

DEFAULT_TRAIN_CSV = Path(
    os.getenv("BIOREASONING_TRAIN_CSV", str(ROOT / "data" / "raw" / "track_a" / "train.csv"))
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--baseline-id", default="jsagent", help="Variant to smoke.")
    ap.add_argument("--val-n", type=int, default=80, help="DEV val subsample size (first N rows).")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--reasoning-effort", default="low")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument(
        "--output-dir", type=Path, default=ROOT / "outputs" / "self-improve-loop-verify"
    )
    args = ap.parse_args()

    if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("BIOREASONING_OPENAI_API_KEY"):
        print("[verify] FAIL: no API key (OPENROUTER_API_KEY) — cannot reach gpt-oss.", flush=True)
        sys.exit(1)

    df = pd.read_csv(args.train_csv)
    infer_fn = make_openrouter_infer_fn(
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        concurrency=args.concurrency,
    )

    print(f"[verify] smoking {args.baseline_id} on first {args.val_n} val rows…", flush=True)
    try:
        rec = run_preflight(
            df, infer_fn, args.output_dir, val_n=args.val_n, baseline_id=args.baseline_id
        )
    except PreflightError as e:
        print(f"[verify] FAIL: {e}", flush=True)
        sys.exit(1)

    m = rec.metrics
    print(
        f"[verify] PASS: n_val={int(m['n_val'])} mean={m['mean']:.3f} "
        f"(auroc_de={m['auroc_de']:.3f} auroc_dir={m['auroc_dir']:.3f}) — loop is live.",
        flush=True,
    )
    print(f"[verify] archive → {args.output_dir}", flush=True)


if __name__ == "__main__":
    main()
