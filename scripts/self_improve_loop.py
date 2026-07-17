"""Self-improvement loop runner — 24/7 propose → triple-verify → promote on gpt-oss.

Wires the OpenRouter gpt-oss infer_fn + the live DE-votes proposer (KB-ruled-out
channels filtered) + the P9 triple-verify gate + the driver, archiving every trial
to ``outputs/self-improve-loop/``. It NEVER submits to Kaggle: a gate-surviving
variant is surfaced for a human-gated submission (Goal 5).

Run once (one loop to convergence / budget):
    uv run python scripts/self_improve_loop.py --budget-usd 5

24/7 cadence — wrap in launchd or a ``claude -p`` heartbeat:
    while true; do uv run python scripts/self_improve_loop.py --budget-usd 5; sleep 900; done

The gate is only trustworthy on the FULL val partition (each candidate is scored on
3 independent dual-OOD splits); there is deliberately no ``--val-n`` smoke here.
Backend + key resolution: see ``bio_reasoning.trial_loop.inference`` (OpenRouter env).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.archive import archive, load_trials
from bio_reasoning.trial_loop.driver import self_improve_loop
from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.loop import make_prompt_row_predictor
from bio_reasoning.trial_loop.proposers import PROPOSERS, select_proposer
from bio_reasoning.trial_loop.types import TrialRecord, Variant

_OPTIMIZER_PROMPT = (
    "You are tuning a prompt-only gpt-oss classifier for differential-expression. "
    "Given the trial history (variant id + OOD mean-AUROC), propose the NEXT config to try. "
    'Reply with ONLY a JSON object: {{"n_few_shot": <0|2|4|8>, "retrieval": '
    '"random"|"go_category", "n_samples": <3|5>}}.\n\nTrial history:\n{reflection}'
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)
DEFAULT_TRAIN_CSV = Path(
    os.getenv("BIOREASONING_TRAIN_CSV", str(ROOT / "data" / "raw" / "track_a" / "train.csv"))
)
PRICE_IN = float(os.getenv("BIOREASONING_PRICE_IN_PER_TOKEN", "0.037e-6"))
PRICE_OUT = float(os.getenv("BIOREASONING_PRICE_OUT_PER_TOKEN", "0.170e-6"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--baseline-id", default="jsagent", help="Starting baseline variant id.")
    ap.add_argument(
        "--proposer",
        choices=PROPOSERS,
        default="grid",
        help="Search policy: grid (walk once) | bandit (UCB resample) | llm (gpt-oss optimizer). "
        "bandit/llm never self-converge — pair with --max-trials or --budget-usd.",
    )
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2], help="Gate split seeds.")
    ap.add_argument("--noise-band", type=float, default=None, help="Override; default measured.")
    ap.add_argument("--dry-rounds", type=int, default=2, help="Stop after K non-improving rounds.")
    ap.add_argument("--budget-usd", type=float, default=None, help="Spend cap (USD).")
    ap.add_argument("--max-trials", type=int, default=None)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--reasoning-effort", default="low")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "self-improve-loop")
    args = ap.parse_args()

    df = pd.read_csv(args.train_csv)

    # go_category variants retrieve exemplars sharing the query pert's GO category;
    # without this key_fn they collapse to random few-shot (identical prompts/scores).
    from bio_reasoning.features.gene_function import annotate_perts

    cats = annotate_perts(
        sorted(df["pert"].astype(str).unique()),
        ROOT / "data" / "interim" / "pert_go_category.json",
    )
    example_key_fn = lambda pert, gene: cats.get(pert, "other")  # noqa: E731

    infer = make_openrouter_infer_fn(
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        concurrency=args.concurrency,
    )
    predictor = make_prompt_row_predictor(infer)

    def _propose_fn(reflection: str) -> str:
        # single gpt-oss completion proposing the next config; counts toward the budget.
        return infer([_OPTIMIZER_PROMPT.format(reflection=reflection)], 0)[0]

    proposer = select_proposer(
        args.proposer, propose_fn=_propose_fn if args.proposer == "llm" else None
    )

    def spent_usd() -> float:
        t = infer.token_totals  # type: ignore[attr-defined]
        return t["prompt_tokens"] * PRICE_IN + t["completion_tokens"] * PRICE_OUT

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trials_path = args.output_dir / "trials.jsonl"

    def persist(rec: TrialRecord) -> None:
        rec.cost_usd = round(spent_usd(), 4)
        with trials_path.open("a") as fh:
            fh.write(rec.to_json() + "\n")
        archive(args.output_dir, load_trials(trials_path))
        m = rec.metrics
        verdict = "ACCEPT" if m["accepted"] else "reject"
        print(
            f"[loop] {rec.variant.id}: mean={m['mean']:.3f} vs base {m['baseline_mean']:.3f} "
            f"min_margin={m['min_margin']:+.3f} feas={m['feasibility_ratio']:.2f} "
            f"→ {verdict}  spent=${spent_usd():.3f}",
            flush=True,
        )

    res = self_improve_loop(
        df,
        proposer,
        predictor,
        Variant(id=args.baseline_id, seeds=(42, 43, 44)),
        seeds=tuple(args.seeds),
        noise_band=args.noise_band,
        dry_rounds=args.dry_rounds,
        budget=args.budget_usd,
        spent_fn=spent_usd if args.budget_usd is not None else None,
        max_trials=args.max_trials,
        example_key_fn=example_key_fn,
        on_record=persist,
    )

    errs = int(infer.token_totals.get("errors", 0.0))  # type: ignore[attr-defined]
    # A/B metric: trials-to-best = index of the highest-mean trial (lower = faster search).
    if res.records:
        best_i = max(range(len(res.records)), key=lambda i: res.records[i].metrics["mean"])
        best = res.records[best_i]
        print(
            f"\n[loop] proposer={args.proposer}  trials={len(res.records)}  "
            f"trials-to-best={best_i + 1} (mean={best.metrics['mean']:.3f}, {best.variant.id})"
        )
    print(f"[loop] stopped: {res.stopped_reason}  spent=${res.spent:.3f}  errors={errs}")
    if res.accepted:
        winners = ", ".join(v.id for v in res.accepted)
        print(f"[loop] gate-SURVIVING variant(s): {winners}")
        print(f"[loop] final promoted baseline: {res.baseline.id}")
        print("[loop] NEXT (human-gated): build + submit this variant's Track A run (Goal 5).")
    else:
        print("[loop] no variant cleared the triple-verify gate — DE lane still locked.")
    print(f"[loop] ledger → {args.output_dir}")


if __name__ == "__main__":
    main()
