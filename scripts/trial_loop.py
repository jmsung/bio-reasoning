"""Trial-loop CLI: score Track A prompt variants on the dual-OOD OOD-val split.

Two modes, both scoring each :class:`Variant` over the ``holdout_split`` val partition
of ``train.csv`` with the real gpt-oss-120b endpoint (OpenRouter by default — the
leaderboard-valid fixed model) and the shared ``mean(AUROC_de, AUROC_dir)`` metric.
Each trial is appended to ``outputs/trial-loop/trials.jsonl`` and the leaderboard +
best variant are refreshed after every trial.

- Single variant:  ``--variant-id <id> [--n-few-shot N]``
- Loop (``--grid``): drive propose → run → reflect over a few-shot grid until the
  proposer converges (``run_loop`` + ``make_grid_proposer``).

``--track a`` (default) is prompt-only. ``--track b`` reuses the identical
split/score/reflect/archive harness via the DSPy ReAct agent (one run per val row,
tools restricted to the split's train partition for leak-freedom); needs the
``track-b`` dep group + ``OPENROUTER_API_KEY``.

Fitness is the OOD-val mean; the honest floor to beat is the evidence prior ≈ 0.533.
A trustworthy number needs the FULL val partition (~1276 rows) — ``--val-n`` caps rows
for a cheap plumbing smoke only, and a capped run's score is a mirage (do not record it
as the variant's fitness). See ``mb/findings/track-strategy.md``.

Few-shot exemplars are ``--retrieval random`` (default) or ``go_category`` — the latter
retrieves, per query, train exemplars sharing the query perturbation's GO category
(relevance-selected). On the dual-OOD split random few-shot hurts (exemplars aren't
analogous to unseen queries); go_category tests whether *relevant* exemplars recover lift.

Usage:
    uv run python scripts/trial_loop.py --variant-id zero-shot
    uv run python scripts/trial_loop.py --grid 0,2,4,8            # random few-shot sizes
    uv run python scripts/trial_loop.py --grid 2,4,8 --retrieval go_category  # retrieval
    uv run python scripts/trial_loop.py --variant-id fs4 --n-few-shot 4 --val-n 40  # smoke
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.archive import archive, load_trials
from bio_reasoning.trial_loop.loop import (
    make_agent_row_predictor,
    make_prompt_row_predictor,
    run_loop,
    run_variant,
)
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
        # Resilience: a single bad response (rate-limit, 5xx, non-JSON/truncated body)
        # must degrade ONE row to the uniform default, not kill a 15k-call run.
        for attempt in range(args.max_retries + 1):
            try:
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
                cost["usd"] += (
                    tok["prompt_tokens"] * PRICE_IN + tok["completion_tokens"] * PRICE_OUT
                )
                return text
            except Exception:
                if attempt == args.max_retries:
                    cost["errors"] += 1
                    return ""  # parse_answer("") → uniform (1/3, 1/3) fallback for this row
                time.sleep(2.0 * (attempt + 1))
        return ""

    def infer_fn(prompts, seed):
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            return list(ex.map(lambda p: _one(p, seed), prompts))

    return infer_fn


def _load_track_b_module():
    """Import scripts/track_b_agentic.py by file path (scripts/ is not a package)."""
    import importlib.util

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(
        "track_b_agentic", scripts_dir / "track_b_agentic.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_track_b_predictor(df, args):
    """Build a Track B agent RowPredictor: DSPy ReAct agent, one run per val row.

    Restricts the agent's lookup tools to the split's TRAIN partition (same split
    params ``predict_variant`` uses) so the agent can't read a val row's own label.
    Reuses the extracted ``build_openrouter_lm``/``build_react_agent``/``predict_row``.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("--track b needs OPENROUTER_API_KEY (in .env.local).")
    try:
        tba = _load_track_b_module()
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"--track b needs the 'track-b' dep group (uv sync --group track-b): {e}"
        ) from e

    from bio_reasoning.eval.split import holdout_split

    train_idx, _ = holdout_split(
        df, seed=args.split_seed, pert_frac=args.pert_frac, gene_frac=args.gene_frac
    )
    tba._set_train_df(df.iloc[train_idx])  # leak-free: tools see disjoint train only

    lm = tba.build_openrouter_lm(args.max_tokens, args.max_retries)
    react = tba.build_react_agent(lm, args.max_iters)

    # Resumable per-row cache: agent runs are slow + expensive, so a kill/timeout
    # must not waste completed rows. Cached (pert,gene,seed) → (up,down) returns
    # instantly; a relaunch resumes for free. Saved every 25 new rows.
    import json

    cache_path = args.output_dir / "trackb_row_cache.json"
    row_cache: dict = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    done = {"n": 0, "hit": 0}
    lock = threading.Lock()

    def agent_fn(pert: str, gene: str, seed: int) -> tuple[float, float]:
        key = f"{pert}__{gene}__{seed}"
        with lock:
            if key in row_cache:
                done["hit"] += 1
                return tuple(row_cache[key])  # type: ignore[return-value]
        pair = tba.predict_row(react, pert, gene)
        with lock:
            row_cache[key] = list(pair)
            done["n"] += 1
            if done["n"] % 25 == 0:
                cache_path.write_text(json.dumps(row_cache))
            if (done["n"] + done["hit"]) % 50 == 0:
                print(f"[track-b] {done['n']} new / {done['hit']} cached", flush=True)
        return pair

    return make_agent_row_predictor(agent_fn, concurrency=args.concurrency)


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
    ap.add_argument("--track", choices=["a", "b"], default="a", help="a=prompt-only, b=agentic.")
    ap.add_argument("--variant-id", help="Single-variant mode: stable id (required unless --grid).")
    ap.add_argument("--grid", help="Loop mode: comma-sep n_few_shot values, e.g. '0,2,4,8'.")
    ap.add_argument("--max-trials", type=int, default=None, help="Cap loop iterations.")
    ap.add_argument("--prompt-template", type=Path, help="Custom template file ({pert}/{gene}).")
    ap.add_argument("--n-few-shot", type=int, default=0)
    ap.add_argument(
        "--retrieval",
        choices=["random", "go_category"],
        default="random",
        help="Few-shot exemplar selection: random sample vs GO-category retrieval.",
    )
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--split-seed", type=int, default=0)
    ap.add_argument("--pert-frac", type=float, default=0.4)
    ap.add_argument("--gene-frac", type=float, default=0.4)
    ap.add_argument("--val-n", type=int, default=None, help="Cap val rows (SMOKE only — noisy).")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--max-iters", type=int, default=40, help="Track B: ReAct rounds/row.")
    ap.add_argument("--max-retries", type=int, default=2, help="Track B: LM retries.")
    ap.add_argument("--reasoning-effort", default="low")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "trial-loop")
    args = ap.parse_args()
    if not args.grid and not args.variant_id:
        # 'jsagent' (Jongmin Sung's agent) is our official agent name for BOTH tracks;
        # single-variant runs default to it. The grid uses descriptive fs*/go* ids.
        args.variant_id = "jsagent"

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

    # Retrieval few-shot: relevance key = the perturbation's GO functional category
    # (same signal the direction prior uses). Random few-shot ignores this.
    example_key_fn = None
    if args.retrieval == "go_category":
        from bio_reasoning.features.gene_function import annotate_perts

        cats = annotate_perts(
            sorted(df["pert"].astype(str).unique()),
            ROOT / "data" / "interim" / "pert_go_category.json",
        )
        example_key_fn = lambda pert, gene: cats.get(pert, "other")  # noqa: E731

    template = args.prompt_template.read_text() if args.prompt_template else None
    cost = {"prompt_tokens": 0.0, "completion_tokens": 0.0, "usd": 0.0, "errors": 0.0}
    if args.track == "a":
        row_predictor = make_prompt_row_predictor(_build_infer_fn(args, cost))
        variant_seeds = tuple(args.seeds)
    else:
        row_predictor = _build_track_b_predictor(df, args)
        # One agent run per row is already expensive; don't silently multiply by
        # len(seeds). Multi-sample averaging is a separate lever (track-b-multisample).
        variant_seeds = (args.seeds[0],)

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

    kw = dict(
        seed=args.split_seed,
        pert_frac=args.pert_frac,
        gene_frac=args.gene_frac,
        example_key_fn=example_key_fn,
    )
    pfx = "go" if args.retrieval == "go_category" else "fs"  # distinct ids per strategy
    if args.grid:
        candidates = [
            Variant(
                id=f"{pfx}{n}",
                prompt_template=template,
                n_few_shot=n,
                retrieval=args.retrieval,
                seeds=variant_seeds,
            )
            for n in (int(x) for x in args.grid.split(","))
        ]
        run_loop(
            df,
            make_grid_proposer(candidates),
            row_predictor,
            max_trials=args.max_trials,
            on_trial=persist,
            **kw,
        )
    else:
        variant = Variant(
            id=args.variant_id,
            prompt_template=template,
            n_few_shot=args.n_few_shot,
            retrieval=args.retrieval,
            seeds=variant_seeds,
        )
        persist(run_variant(df, variant, row_predictor, **kw), [])

    if cost["errors"]:
        print(f"[trial-loop] WARNING: {int(cost['errors'])} call(s) failed → uniform fallback.")
    print(f"[trial-loop] archive → {args.output_dir}")


if __name__ == "__main__":
    main()
