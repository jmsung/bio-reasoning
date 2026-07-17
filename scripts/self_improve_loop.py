"""Self-improvement loop runner — 24/7 propose → triple-verify → promote on gpt-oss.

Two lanes share the P9 triple-verify gate + driver, archiving every trial to
``outputs/self-improve-loop/``; NEITHER submits to Kaggle (a gate-survivor is
surfaced for a human-gated submission, Goal 5):

  * DE-votes (default): prompt-only ``infer_fn`` + a ``--proposer`` search policy
    (grid | bandit | llm) over the KB-denylist DE variant space.
    uv run python scripts/self_improve_loop.py --proposer bandit --budget-usd 5

  * Agentic (``--agentic``): tool-config proposer + a per-variant DSPy ReAct agent
    over the real-data tools (GO/STRING/Traxler-direction). Baseline is the tool-free
    agent, so the gate accepts a config only if real tools beat it. A Traxler fold csv
    (``--traxler-fold``) adds the external real-label check; leak-safe (A) — the agent
    drops the Traxler tool for the whole run whenever that fold is gated.
    uv run python scripts/self_improve_loop.py --agentic --budget-usd 5

The gate is only trustworthy on the FULL val partition (each candidate is scored on
3 independent dual-OOD splits). ``--val-n N`` is a DEV-ONLY smoke knob that truncates
val to its first N rows so a real trial runs in minutes — for fast iteration / bug
detection only, NEVER to promote a survivor (the subsampled gate is untrustworthy).
Backend + key resolution: see ``bio_reasoning.trial_loop.inference`` (OpenRouter env).
"""

from __future__ import annotations

import argparse
import faulthandler
import importlib.util
import math
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from bio_reasoning.trial_loop.agent_variants import agent_variant_grid, make_agent_proposer
from bio_reasoning.trial_loop.archive import archive, load_trials
from bio_reasoning.trial_loop.driver import self_improve_loop
from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.loop import (
    make_configurable_agent_row_predictor,
    make_prompt_row_predictor,
)
from bio_reasoning.trial_loop.proposers import PROPOSERS, select_proposer
from bio_reasoning.trial_loop.tools import (
    make_cache_backend,
    make_tools,
    traxler_direction_lookup,
)
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

# Watchdog: if any operation blocks longer than this, dump ALL thread stacks to
# stderr (repeating) so a hang self-diagnoses. macOS py-spy needs sudo, so this is
# the in-process capture. Default 1800s (30 min) is comfortably above a single
# variant's legitimate scoring time (~6-18 min at concurrency 8, val ~1.3k rows) so
# it fires only on a genuine hang, not normal slow scoring. Tunable via
# BIOREASONING_HANG_DUMP_S (0 disables).
_HANG_DUMP_S = int(os.getenv("BIOREASONING_HANG_DUMP_S", "1800"))
if _HANG_DUMP_S > 0:
    faulthandler.dump_traceback_later(_HANG_DUMP_S, repeat=True)
DEFAULT_TRAIN_CSV = Path(
    os.getenv("BIOREASONING_TRAIN_CSV", str(ROOT / "data" / "raw" / "track_a" / "train.csv"))
)
PRICE_IN = float(os.getenv("BIOREASONING_PRICE_IN_PER_TOKEN", "0.037e-6"))
PRICE_OUT = float(os.getenv("BIOREASONING_PRICE_OUT_PER_TOKEN", "0.170e-6"))

# Real-data caches the agentic tools read (offline once warm; see trial_loop.tools).
GO_CACHE = ROOT / "data" / "interim" / "gene_go_bp.json"
STRING_CACHE = ROOT / "data" / "external" / "string_partners_universe.json"
DEFAULT_TRAXLER_FOLD = ROOT / "data" / "external" / "traxler_labels.csv"


def _load_track_b_module():
    """Import scripts/track_b_agentic.py by path (scripts/ is not a package)."""
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(
        "track_b_agentic", scripts_dir / "track_b_agentic.py"
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {scripts_dir / 'track_b_agentic.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_agentic_predictor(args, external_fold_df):
    """Agentic tool-config predictor + a DSPy-token spend function.

    Each variant's tool subset (``variant.tools``) selects real-data tools built via
    ``make_tools`` over the warm GO/STRING caches; the DSPy ReAct agent is built per
    tool-config and cached (``make_configurable_agent_row_predictor``). Leak-safe (A):
    whenever a Traxler fold is gated (``external_fold_df is not None``) the agent is
    built WITHOUT the Traxler tool, so it can never read the fold's own labels — the
    grid excludes Traxler configs and the backend leaves ``traxler_direction`` unset.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("--agentic needs OPENROUTER_API_KEY (Bing's gpt-oss endpoint).")
    tba = _load_track_b_module()
    lm = tba.build_openrouter_lm(args.max_tokens, args.max_retries)
    include_traxler = external_fold_df is None  # (A): no Traxler tool when its fold is the gate
    # Leak-safe (A): the Traxler labels power the tool ONLY when they are NOT the gated
    # fold (include_traxler) — so the tool is functional here, dropped when the fold gates.
    traxler_fn = None
    if include_traxler and DEFAULT_TRAXLER_FOLD.is_file():
        traxler_fn = traxler_direction_lookup(pd.read_csv(DEFAULT_TRAXLER_FOLD))
    backend = make_cache_backend(GO_CACHE, STRING_CACHE, traxler_direction=traxler_fn)
    all_tools = {t.__name__: t for t in make_tools(backend, include_traxler=include_traxler)}

    def agent_fn_for(variant: Variant):
        selected = [all_tools[n] for n in (variant.tools or ()) if n in all_tools]
        tools = [*selected, tba.submit_graded, tba.submit_answer]
        react = tba.build_react_agent(lm, args.max_iters, tools=tools)
        return lambda pert, gene, seed: tba.predict_row(react, pert, gene)

    predictor = make_configurable_agent_row_predictor(agent_fn_for, concurrency=args.concurrency)

    def spent_usd() -> float:
        # Conservative: price all DSPy tokens at the completion rate (over-estimates →
        # the budget cap trips earlier, never later). Splitting prompt/completion needs
        # per-call usage plumbing DSPy doesn't expose here.
        return tba._tokens_from_history(lm, 0) * PRICE_OUT

    return predictor, spent_usd, include_traxler


def _de_setup(args, df):
    """DE-votes lane: prompt-only predictor + a ``--proposer`` search policy (default)."""
    from bio_reasoning.features.gene_function import annotate_perts

    # go_category variants retrieve exemplars sharing the query pert's GO category;
    # without this key_fn they collapse to random few-shot (identical prompts/scores).
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

    def errors_fn() -> int:
        return int(infer.token_totals.get("errors", 0.0))  # type: ignore[attr-defined]

    baseline = Variant(id=args.baseline_id, seeds=(42, 43, 44))
    return proposer, predictor, baseline, spent_usd, example_key_fn, None, errors_fn


def _agentic_setup(args):
    """Agentic lane (③): tool-config proposer + per-variant agent predictor.

    Baseline is the tool-free agent (``tools=()``), so the gate accepts a tool config
    only if real tools beat the same agent with none — the honest "do the tools help?"
    A/B. When a Traxler fold csv is given it becomes the gate's external real-label
    check (leak-safe (A): the agent drops the Traxler tool for the whole run).
    """
    fold = args.traxler_fold
    external_fold = pd.read_csv(fold) if fold and Path(fold).is_file() else None
    predictor, spent_usd, include_traxler = _build_agentic_predictor(args, external_fold)
    proposer = make_agent_proposer(agent_variant_grid(include_traxler=include_traxler))
    baseline = Variant(id="agent-prior-s1", tools=(), seeds=(42,))
    # Agents gather evidence via tools, not few-shot exemplars → no example_key_fn.
    # DSPy per-call errors aren't tracked here (unlike the DE infer_fn); report 0.
    return proposer, predictor, baseline, spent_usd, None, external_fold, lambda: 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-csv", type=Path, default=DEFAULT_TRAIN_CSV)
    ap.add_argument("--baseline-id", default="jsagent", help="Starting baseline variant id.")
    ap.add_argument(
        "--proposer",
        choices=PROPOSERS,
        default="grid",
        help="DE lane search policy: grid (walk once) | bandit (UCB resample) | llm "
        "(gpt-oss optimizer). bandit/llm never self-converge — pair with --max-trials "
        "or --budget-usd. Ignored under --agentic.",
    )
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2], help="Gate split seeds.")
    ap.add_argument(
        "--val-n",
        type=int,
        default=None,
        help="DEV-ONLY smoke: score only the first N val rows per split (deterministic) "
        "so a real trial finishes in minutes. Makes the gate UNtrustworthy — for fast "
        "iteration / bug detection, never to promote a survivor. Omit for the full-val gate.",
    )
    ap.add_argument("--noise-band", type=float, default=None, help="Override; default measured.")
    ap.add_argument("--dry-rounds", type=int, default=2, help="Stop after K non-improving rounds.")
    ap.add_argument("--budget-usd", type=float, default=None, help="Spend cap (USD).")
    ap.add_argument("--max-trials", type=int, default=None)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--reasoning-effort", default="low")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "self-improve-loop")
    ap.add_argument(
        "--agentic",
        action="store_true",
        help="Loop style ③: search agentic tool configs (not DE-votes prompts).",
    )
    ap.add_argument("--max-iters", type=int, default=40, help="Agentic: ReAct rounds/row.")
    ap.add_argument("--max-retries", type=int, default=2, help="Agentic: LM retries.")
    ap.add_argument(
        "--traxler-fold",
        type=Path,
        default=DEFAULT_TRAXLER_FOLD,
        help="Agentic: external real-label fold csv; '' to disable. Leak-safe (A): the "
        "agent drops the Traxler tool whenever this fold is gated.",
    )
    args = ap.parse_args()

    df = pd.read_csv(args.train_csv)

    if args.agentic:
        proposer, predictor, baseline, spent_usd, example_key_fn, external_fold, errors_fn = (
            _agentic_setup(args)
        )
    else:
        proposer, predictor, baseline, spent_usd, example_key_fn, external_fold, errors_fn = (
            _de_setup(args, df)
        )

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
        baseline,
        seeds=tuple(args.seeds),
        noise_band=args.noise_band,
        dry_rounds=args.dry_rounds,
        budget=args.budget_usd,
        spent_fn=spent_usd if args.budget_usd is not None else None,
        max_trials=args.max_trials,
        example_key_fn=example_key_fn,
        external_fold=external_fold,
        val_n=args.val_n,
        on_record=persist,
    )

    lane = "agentic" if args.agentic else "DE"
    search = "agentic" if args.agentic else args.proposer
    # A/B metric: trials-to-best = index of the highest-mean trial (lower = faster search).
    if res.records:

        def _mean_at(i: int) -> float:
            m = res.records[i].metrics["mean"]
            return float("-inf") if math.isnan(m) else m  # nan gates never win trials-to-best

        best_i = max(range(len(res.records)), key=_mean_at)
        best = res.records[best_i]
        print(
            f"\n[loop] search={search}  trials={len(res.records)}  "
            f"trials-to-best={best_i + 1} (mean={best.metrics['mean']:.3f}, {best.variant.id})"
        )
    print(f"[loop] stopped: {res.stopped_reason}  spent=${res.spent:.3f}  errors={errors_fn()}")
    if res.accepted:
        winners = ", ".join(v.id for v in res.accepted)
        print(f"[loop] gate-SURVIVING variant(s): {winners}")
        print(f"[loop] final promoted baseline: {res.baseline.id}")
        print("[loop] NEXT (human-gated): build + submit this variant's Track run (Goal 5).")
    else:
        print(f"[loop] no variant cleared the triple-verify gate — {lane} lane still locked.")
    print(f"[loop] ledger → {args.output_dir}")


if __name__ == "__main__":
    main()
