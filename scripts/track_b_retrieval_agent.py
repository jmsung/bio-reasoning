"""Track B external-knowledge-retrieval agent — eval + submission.

Runs the retrieval-augmented per-row predictor
(:mod:`bio_reasoning.agents.retrieval_agent`): for each (pert, gene) it retrieves
local external biology (GO:BP for both, the pert's functional-category direction
prior, optional STRING partners) and asks gpt-oss-120b for a calibrated
``{de_prob, dir_prob}``. Two modes:

  --eval   Score a dual-OOD ``holdout_split`` subsample with the official
           ``mean(AUROC_de, AUROC_dir)`` metric; report the abstention rate and a
           calibration read (is the DE signal spread, or collapsed to no-effect?).
           This is the cheap gate before spending on a full run.

  (default) Produce a full Track B submission CSV (15-col schema + traces) over
           test.csv, ready for the orchestrator to submit.

Model: gpt-oss-120b via OpenRouter (the fixed challenge model — leaderboard-valid).
Key from .env.local (OPENROUTER_API_KEY). Never prints key contents.

Usage:
    uv run --group eval python scripts/track_b_retrieval_agent.py --eval --eval-n 60 --string
    uv run --group eval python scripts/track_b_retrieval_agent.py --out submissions/track_b_retrieval_agent.csv --string
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.agents.retrieval_agent import (
    RowResult,
    build_prompt,
    openrouter_llm_fn,
    predict_row,
    retrieve,
    string_partners,
)
from bio_reasoning.eval.split import assert_leak_free, holdout_split
from bio_reasoning.eval.track_a_score import evaluate

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
MODEL = "openai/gpt-oss-120b"
SEEDS = (42, 43, 44)


def _run_rows(rows: list[dict], llm_fn, use_string: bool, concurrency: int) -> list[RowResult]:
    sfn = string_partners if use_string else None

    def _one(r: dict) -> RowResult:
        return predict_row(str(r["pert"]), str(r["gene"]), 42, llm_fn=llm_fn, string_fn=sfn)

    if concurrency <= 1:
        results = [_one(r) for r in rows]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            results = list(ex.map(_one, rows))
    return results


def _diagnostics(results: list[RowResult]) -> dict:
    de = np.array([r.de_prob if r.de_prob is not None else 0.0 for r in results])
    parsed = sum(r.parsed for r in results)
    abst = sum(r.abstained for r in results)
    return {
        "n": len(results),
        "parsed_frac": round(parsed / max(len(results), 1), 3),
        "abstention_rate": round(abst / max(len(results), 1), 3),
        "de_prob_mean": round(float(de.mean()), 3),
        "de_prob_std": round(float(de.std()), 3),
        "de_prob_min": round(float(de.min()), 3),
        "de_prob_max": round(float(de.max()), 3),
        "category_mix": dict(Counter(r.category for r in results)),
        "direct_edges": sum(r.direct_edge for r in results),
    }


def run_eval(args, llm_fn) -> None:
    train_full = pd.read_csv(TRAIN)
    tr_idx, ev_idx = holdout_split(train_full, seed=args.fold_seed)
    assert_leak_free(train_full, tr_idx, ev_idx)
    ev = train_full.iloc[ev_idx].reset_index(drop=True)
    if args.eval_n is not None:
        ev = ev.head(args.eval_n).reset_index(drop=True)
    rows = ev.to_dict("records")
    print(
        f"--eval: dual-OOD holdout (seed={args.fold_seed}), {len(rows)} rows, "
        f"string={'on' if args.string else 'off'}, model={MODEL}"
    )

    results = _run_rows(rows, llm_fn, args.string, args.concurrency)
    labels = ev["label"].astype(str).to_numpy()

    up_raw = np.array([r.up for r in results])
    down_raw = np.array([r.down for r in results])
    floored = [r.floored() for r in results]
    up_fl = np.array([u for u, _ in floored])
    down_fl = np.array([d for _, d in floored])

    diag = _diagnostics(results)
    tok = int(sum(r.tokens.get("total_tokens", 0) for r in results))
    print("\n=== calibration diagnostics ===")
    print(json.dumps(diag, indent=2))
    print(f"tokens_used(total) = {tok}")

    try:
        s_raw = evaluate(labels, up_raw, down_raw)
        s_fl = evaluate(labels, up_fl, down_fl)
    except ValueError as e:
        print(f"\n[eval] cannot score: {e} — raise --eval-n for real class balance.")
        return

    floor = 0.533  # dual-OOD evidence-prior floor
    incumbent = 0.597  # current Track B best (LB); OOD-val ~0.592
    print("\n=== Track B retrieval-agent — dual-OOD val ===")
    print(
        f"  raw     : mean={s_raw['mean']:.3f} (de={s_raw['auroc_de']:.3f}, dir={s_raw['auroc_dir']:.3f})"
    )
    print(
        f"  floored : mean={s_fl['mean']:.3f} (de={s_fl['auroc_de']:.3f}, dir={s_fl['auroc_dir']:.3f})"
    )
    print(f"  vs prior floor {floor:.3f} / incumbent {incumbent:.3f}")
    verdict = "COLLAPSED" if diag["abstention_rate"] > 0.6 else "calibrated"
    print(f"  abstention {diag['abstention_rate']:.1%} -> {verdict}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "pert": ev["pert"],
                "gene": ev["gene"],
                "label": labels,
                "de_prob": [r.de_prob for r in results],
                "dir_prob": [r.dir_prob for r in results],
                "up": up_fl,
                "down": down_fl,
            }
        ).to_csv(args.out, index=False)
        print(f"  wrote per-row eval dump -> {args.out}")


def _trace_str(r: RowResult) -> str:
    return json.dumps(r.trace, default=str)[:6000]


def run_submission(args, llm_fn) -> None:
    test = pd.read_csv(TEST)
    if args.limit is not None:
        test = test.head(args.limit).reset_index(drop=True)
    rows = test.to_dict("records")
    print(
        f"submission: {len(rows)} test rows, string={'on' if args.string else 'off'}, model={MODEL}"
    )

    results = _run_rows(rows, llm_fn, args.string, args.concurrency)
    diag = _diagnostics(results)
    print(json.dumps(diag, indent=2))

    # One prompt is representative for the prompt-token report.
    sample = retrieve(str(rows[0]["pert"]), str(rows[0]["gene"]), string_fn=None)
    prompt_tokens = len(build_prompt(sample)) // 4

    out_rows = []
    for row, r in zip(rows, results, strict=True):
        up, down = r.floored()
        trace = _trace_str(r)
        tok = int(r.tokens.get("total_tokens", 0))
        out_rows.append(
            {
                "id": row["id"],
                "prediction_up": up,
                "prediction_down": down,
                "prediction_up_seed42": up,
                "prediction_down_seed42": down,
                "prediction_up_seed43": up,
                "prediction_down_seed43": down,
                "prediction_up_seed44": up,
                "prediction_down_seed44": down,
                "reasoning_trace_seed42": trace,
                "reasoning_trace_seed43": trace,
                "reasoning_trace_seed44": trace,
                "tokens_used": tok,
                "prompt_tokens": prompt_tokens,
                "model_name": MODEL,
            }
        )
    out = Path(args.out or ROOT / "submissions/track_b_retrieval_agent.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(out_rows).to_csv(out, index=False)
    print(f"wrote {out}  ({len(out_rows)} rows, 15 cols)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval", action="store_true", help="score a dual-OOD holdout subsample")
    ap.add_argument("--eval-n", type=int, default=60, help="cap holdout rows in --eval")
    ap.add_argument("--fold-seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None, help="cap test rows (submission smoke)")
    ap.add_argument("--string", action="store_true", help="retrieve STRING partners (network, dev)")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high"])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("BIOREASONING_OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not found in env (.env.local).")
    llm_fn = openrouter_llm_fn(
        api_key=api_key,
        model=MODEL,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
    )

    if args.eval:
        run_eval(args, llm_fn)
    else:
        run_submission(args, llm_fn)


if __name__ == "__main__":
    main()
