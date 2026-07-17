"""Kill-test: does DE self-consistency escape chance on the dual-OOD val split?

The project's central finding is that DE-vs-none is near-chance under dual-OOD
(AUROC_de ~= 0.50; tech report §3, Yuan 2026 on LLM over-DE bias). The user's
hypothesis is that model-based *self-consistency* (sample the model K times per
(pert, gene) and aggregate the votes into a graded score) might crack DE where
six curated / retrieval channels could not.

This script measures it directly: hold out a dual-OOD val split, sample the
gpt-oss endpoint K times per row, aggregate with the tested
`votes_to_scores` aggregator, and score AUROC_de / AUROC_dir with the official
`eval.track_a_score.evaluate`. If AUROC_de stays ~0.50, the hypothesis is dead.

EXECUTION NEEDS: (1) the Track A train.csv, and (2) a live gpt-oss endpoint
(Bing's GPT-OSS DGX, or any OpenAI-compatible gpt-oss). Configure via the same
env the other scripts use (BIOREASONING_LLM_PROVIDER etc.) + .env.

Run:
    uv run python scripts/de_logprob_probe.py --n-rows 150 --k-samples 5
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.models.de_logprob import votes_to_scores
from bio_reasoning.utils.llm_clients import load_provider_config
from bio_reasoning.utils.openai_compat import post_chat_completion

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.local", override=True)

# Data lives in the main checkout (gitignored); fall back to ../cb/data in a worktree.
_LOCAL = _ROOT / "data" / "raw" / "track_a" / "train.csv"
DEFAULT_TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or (
    str(_LOCAL)
    if _LOCAL.exists()
    else str(_ROOT.parent / "cb" / "data" / "raw" / "track_a" / "train.csv")
)

PROMPT = (
    "In mouse macrophages, the gene {pert} is knocked down by CRISPRi. "
    "Does the expression of the target gene {gene} go up, down, or stay unchanged? "
    "Reason briefly, then answer on the last line with exactly one word: up, down, or none."
)


def _parse_answer(text: str) -> str:
    """Extract the final up/down/none token from a reasoning-model response."""
    low = text.lower()
    # prefer the last occurrence (the model's final answer line)
    best, best_pos = "", -1
    for tok in ("up", "down", "none"):
        pos = low.rfind(tok)
        if pos > best_pos:
            best, best_pos = tok, pos
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", default=DEFAULT_TRAIN)
    ap.add_argument("--n-rows", type=int, default=150, help="val rows to probe (cost control)")
    ap.add_argument("--k-samples", type=int, default=5, help="self-consistency samples per row")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout-s", type=int, default=120)
    args = ap.parse_args()

    df = pd.read_csv(args.train_csv)
    _, val_idx = holdout_split(df, seed=args.seed)
    rng = np.random.default_rng(args.seed)
    val_idx = rng.permutation(val_idx)[: args.n_rows]
    val = df.iloc[val_idx].reset_index(drop=True)
    print(
        f"Probing {len(val)} dual-OOD val rows × {args.k_samples} samples "
        f"({len(val) * args.k_samples} calls)…"
    )

    cfg = load_provider_config()
    pred_up = np.zeros(len(val))
    pred_down = np.zeros(len(val))
    for i, row in val.iterrows():
        prompt = PROMPT.format(pert=row["pert"], gene=row["gene"])
        answers = []
        for s in range(args.k_samples):
            text, _ = post_chat_completion(
                api_base=cfg.api_base or "",
                api_key=cfg.api_key,
                model=cfg.model,
                prompt=prompt,
                seed=args.seed * 1000 + s,
                max_tokens=args.max_tokens,
                timeout_s=args.timeout_s,
            )
            answers.append(_parse_answer(text))
        p_up, p_down, _ = votes_to_scores(answers)
        pred_up[i], pred_down[i] = p_up, p_down
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(val)} rows")

    res = evaluate(val["label"].to_numpy(), pred_up, pred_down)
    print("\n=== DE self-consistency kill-test ===")
    print(f"  AUROC_de  = {res['auroc_de']:.3f}   (chance = 0.500)")
    print(f"  AUROC_dir = {res['auroc_dir']:.3f}")
    print(f"  mean      = {res['mean']:.3f}")
    verdict = "ESCAPES chance" if res["auroc_de"] >= 0.55 else "near-chance — hypothesis DEAD on DE"
    print(f"  DE verdict: {verdict}")


if __name__ == "__main__":
    main()
