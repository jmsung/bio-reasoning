"""Trial-loop CLI (Goal 1): score one Track A prompt variant on the OOD-val split.

Runs a single :class:`Variant` over the dual-OOD ``holdout_split`` val partition of
``train.csv`` using the real gpt-oss-120b endpoint (OpenRouter by default — the
leaderboard-valid fixed model), scores it with the shared ``mean(AUROC_de, AUROC_dir)``
metric, and appends a :class:`TrialRecord` to ``outputs/trial-loop/trials.jsonl``.

Fitness is the OOD-val mean; the honest floor to beat is the evidence prior ≈ 0.533.
A trustworthy number needs the FULL val partition (~1276 rows) — ``--val-n`` caps rows
for a cheap plumbing smoke only, and a capped run's score is a mirage (do not record it
as the variant's fitness). See ``mb/findings/track-strategy.md``.

Usage:
    uv run python scripts/trial_loop.py --variant-id zero-shot
    uv run python scripts/trial_loop.py --variant-id fs4 --n-few-shot 4 --val-n 40
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.archive import archive, load_trials
from bio_reasoning.trial_loop.loop import run_variant
from bio_reasoning.trial_loop.types import Variant
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--variant-id", required=True, help="Stable id for this variant.")
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

    df = pd.read_csv(args.train_csv)
    template = args.prompt_template.read_text() if args.prompt_template else None
    variant = Variant(
        id=args.variant_id,
        prompt_template=template,
        n_few_shot=args.n_few_shot,
        seeds=tuple(args.seeds),
    )

    cost = {"prompt_tokens": 0.0, "completion_tokens": 0.0, "usd": 0.0}
    infer_fn = _build_infer_fn(args, cost)

    if args.val_n is not None:
        print(f"[warn] --val-n={args.val_n} is a plumbing SMOKE; the score is noise, not fitness.")
        # Sub-sample the val rows by shrinking to a deterministic head of the full val set.
        from bio_reasoning.eval.split import holdout_split

        _, val_idx = holdout_split(
            df, seed=args.split_seed, pert_frac=args.pert_frac, gene_frac=args.gene_frac
        )
        keep = set(val_idx[: args.val_n].tolist())
        # Keep all train rows + only the capped val rows so the split reproduces them.
        train_mask = ~df.index.isin(val_idx)
        df = df[train_mask | df.index.isin(keep)].reset_index(drop=True)

    rec = run_variant(
        df,
        variant,
        infer_fn,
        seed=args.split_seed,
        pert_frac=args.pert_frac,
        gene_frac=args.gene_frac,
        cost_usd=round(cost["usd"], 4),
        tokens={k: cost[k] for k in ("prompt_tokens", "completion_tokens")},
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trials_path = args.output_dir / "trials.jsonl"
    with trials_path.open("a") as fh:
        fh.write(rec.to_json() + "\n")

    # Refresh the derived views (leaderboard + best variant) from the full history.
    archive(args.output_dir, load_trials(trials_path))

    m = rec.metrics
    verdict = "BEATS" if m["mean"] > PRIOR_FLOOR else "below"
    print(json.dumps(m, indent=2))
    print(
        f"[trial-loop] variant={variant.id} n_val={m['n_val']} "
        f"mean={m['mean']:.3f} ({verdict} the {PRIOR_FLOOR} prior floor) "
        f"cost=${rec.cost_usd:.4f} → {trials_path}"
    )


if __name__ == "__main__":
    main()
