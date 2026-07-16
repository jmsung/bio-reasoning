"""Trial-loop CLI: score Track A prompt variants on the dual-OOD OOD-val split.

Two modes, both scoring each :class:`Variant` over the ``holdout_split`` val partition
of ``train.csv`` with the real gpt-oss-120b endpoint (OpenRouter by default — the
leaderboard-valid fixed model) and the shared ``mean(AUROC_de, AUROC_dir)`` metric.
Each trial is appended to ``outputs/trial-loop/trials.jsonl`` and the leaderboard +
best variant are refreshed after every trial.

- Single variant:  ``--variant-id <id> [--n-few-shot N]``
- Loop (``--grid``): drive propose → run → reflect over a few-shot grid until the
  proposer converges (``run_loop`` + ``make_grid_proposer``).

Fitness is the OOD-val mean; the honest floor to beat is the evidence prior ≈ 0.533.
A trustworthy number needs the FULL val partition (~1276 rows) — ``--val-n`` caps rows
for a cheap plumbing smoke only, and a capped run's score is a mirage (do not record it
as the variant's fitness). See ``mb/findings/track-strategy.md``.

Usage:
    uv run python scripts/trial_loop.py --variant-id zero-shot
    uv run python scripts/trial_loop.py --grid 0,2,4,8            # loop over few-shot sizes
    uv run python scripts/trial_loop.py --variant-id fs4 --n-few-shot 4 --val-n 40  # smoke
"""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.archive import archive, load_trials
from bio_reasoning.trial_loop.loop import run_loop, run_variant
from bio_reasoning.trial_loop.reflect import make_grid_proposer
from bio_reasoning.trial_loop.types import TrialRecord, Variant
from bio_reasoning.utils.openai_compat import post_chat_completion

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)
DEFAULT_TRAIN_CSV = Path(
    os.getenv("BIOREASONING_TRAIN_CSV", str(ROOT / "data" / "raw" / "track_a" / "train.csv"))
)
# gpt-oss-120b token pricing on OpenRouter (USD per token); override via env.
PRICE_IN = float(os.getenv("BIOREASONING_PRICE_IN_PER_TOKEN", "0.037e-6"))
PRICE_OUT = float(os.getenv("BIOREASONING_PRICE_OUT_PER_TOKEN", "0.170e-6"))
PRIOR_FLOOR = 0.533


def _build_infer_fn(args: argparse.Namespace, cost: dict[str, float]):
    """Return infer_fn(prompts, seed) -> texts, accumulating token cost in ``cost``."""
    api_base = os.getenv("BIOREASONING_OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("BIOREASONING_OPENROUTER_MODEL", "openai/gpt-oss-120b")

    def _one(prompt: str, seed: int) -> str:
        text, tok = post_chat_completion(
            api_base=api_base,
            api_key=api_key,
            model=model,
            prompt=prompt,
            seed=seed,
            max_tokens=args.max_tokens,
            timeout_s=args.timeout,
            reasoning_effort=args.reasoning_effort,
        )
        cost["prompt_tokens"] += tok["prompt_tokens"]
        cost["completion_tokens"] += tok["completion_tokens"]
        cost["usd"] += tok["prompt_tokens"] * PRICE_IN + tok["completion_tokens"] * PRICE_OUT
        return text

    def infer_fn(prompts, seed):
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            return list(ex.map(lambda p: _one(p, seed), prompts))

    return infer_fn


def _report(rec: TrialRecord) -> None:
    m = rec.metrics
    verdict = "BEATS" if m["mean"] > PRIOR_FLOOR else "below"
    print(
        f"[trial-loop] variant={rec.variant.id} n_val={m['n_val']} "
        f"mean={m['mean']:.3f} ({verdict} the {PRIOR_FLOOR} prior floor) "
        f"cost=${(rec.cost_usd or 0.0):.4f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--variant-id", help="Single-variant mode: stable id (required unless --grid).")
    ap.add_argument("--grid", help="Loop mode: comma-sep n_few_shot values, e.g. '0,2,4,8'.")
    ap.add_argument("--max-trials", type=int, default=None, help="Cap loop iterations.")
    ap.add_argument("--prompt-template", type=Path, help="Custom template file ({pert}/{gene}).")
    ap.add_argument("--n-few-shot", type=int, default=0)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--split-seed", type=int, default=0)
    ap.add_argument("--pert-frac", type=float, default=0.4)
    ap.add_argument("--gene-frac", type=float, default=0.4)
    ap.add_argument("--val-n", type=int, default=None, help="Cap val rows (SMOKE only — noisy).")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--reasoning-effort", default="low")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "trial-loop")
    args = ap.parse_args()
    if not args.grid and not args.variant_id:
        ap.error("--variant-id is required unless --grid is given")

    df = pd.read_csv(args.train_csv)
    if args.val_n is not None:
        print(f"[warn] --val-n={args.val_n} is a plumbing SMOKE; the score is noise, not fitness.")
        # Sub-sample the val rows to a deterministic head of the full val set.
        from bio_reasoning.eval.split import holdout_split

        _, val_idx = holdout_split(
            df, seed=args.split_seed, pert_frac=args.pert_frac, gene_frac=args.gene_frac
        )
        keep = set(val_idx[: args.val_n].tolist())
        train_mask = ~df.index.isin(val_idx)
        df = df[train_mask | df.index.isin(keep)].reset_index(drop=True)

    template = args.prompt_template.read_text() if args.prompt_template else None
    cost = {"prompt_tokens": 0.0, "completion_tokens": 0.0, "usd": 0.0}
    infer_fn = _build_infer_fn(args, cost)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trials_path = args.output_dir / "trials.jsonl"
    last = {"prompt_tokens": 0.0, "completion_tokens": 0.0, "usd": 0.0}

    def persist(rec: TrialRecord, _history: list[TrialRecord]) -> None:
        # Attribute cost to this trial as the delta since the previous one.
        rec.cost_usd = round(cost["usd"] - last["usd"], 4)
        rec.tokens = {k: cost[k] - last[k] for k in ("prompt_tokens", "completion_tokens")}
        last.update(cost)
        with trials_path.open("a") as fh:
            fh.write(rec.to_json() + "\n")
        archive(args.output_dir, load_trials(trials_path))
        _report(rec)

    kw = dict(seed=args.split_seed, pert_frac=args.pert_frac, gene_frac=args.gene_frac)
    if args.grid:
        candidates = [
            Variant(id=f"fs{n}", prompt_template=template, n_few_shot=n, seeds=tuple(args.seeds))
            for n in (int(x) for x in args.grid.split(","))
        ]
        run_loop(
            df,
            make_grid_proposer(candidates),
            infer_fn,
            max_trials=args.max_trials,
            on_trial=persist,
            **kw,
        )
    else:
        variant = Variant(
            id=args.variant_id,
            prompt_template=template,
            n_few_shot=args.n_few_shot,
            seeds=tuple(args.seeds),
        )
        persist(run_variant(df, variant, infer_fn, **kw), [])

    print(f"[trial-loop] archive → {args.output_dir}")


if __name__ == "__main__":
    main()
