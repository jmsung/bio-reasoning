"""Trial-loop core: evaluate a Variant on the dual-OOD split, track-agnostically.

The loop's fitness surface is the leak-free ``holdout_split`` val partition scored
with the official ``mean(AUROC_de, AUROC_dir)`` metric — the only honest gate for a
tuned/prompted/agentic predictor (a small or naive CV is a mirage; see
``mb/findings/track-strategy.md``).

The prediction step is injected as a :data:`RowPredictor` — ``(val_rows, variant,
seed, examples) -> [(up, down), ...]`` — so the same split/score/reflect/archive
harness drives **both tracks**: Track A via :func:`make_prompt_row_predictor`
(format → single call → parse) and Track B via :func:`make_agent_row_predictor`
(run the agent per row). Predictors are injected, so the core is offline-testable
with fakes; the CLI wires the real gpt-oss-120b caller / agent.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.reflect import Proposer, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant
from mlgenx import format_prompt, parse_answer
from mlgenx.prompts import CELL_DESC

# infer_fn(prompts, seed) -> one raw text response per prompt (Track A model call).
InferFn = Callable[[Sequence[str], int], Sequence[str]]
# agent_fn(pert, gene, seed) -> graded (up, down) for one row (Track B agent).
AgentFn = Callable[[str, str, int], "tuple[float, float]"]
# examples_provider(val_row) -> that row's few-shot exemplars (or None). Per-row so a
# retrieval strategy can pick query-relevant exemplars; random returns a fixed set.
ExamplesProvider = Callable[["dict"], "list[dict[str, str]] | None"]
# example_key_fn(pert, gene) -> hashable relevance key (e.g. GO category) for retrieval.
ExampleKeyFn = Callable[[str, str], object]
# row_predictor(rows, variant, seed, get_examples) -> one (up, down) per row.
RowPredictor = Callable[
    ["list[dict]", Variant, int, ExamplesProvider],
    "Sequence[tuple[float, float]]",
]


def sample_examples(
    train_df: pd.DataFrame, variant: Variant, seed: int
) -> list[dict[str, str]] | None:
    """Draw ``variant.n_few_shot`` few-shot exemplars from the TRAIN partition.

    Sampling only from train keeps the val fitness leak-free: ``holdout_split``
    guarantees train shares zero perts and zero genes with val, so no exemplar can
    reveal a val row. Deterministic given ``seed``. Returns ``None`` for zero-shot.
    """
    if variant.n_few_shot <= 0 or len(train_df) == 0:
        return None
    rng = np.random.default_rng(seed)
    n = min(variant.n_few_shot, len(train_df))
    idx = rng.choice(len(train_df), size=n, replace=False)
    rows = train_df.iloc[idx]
    return [
        {"pert": str(r["pert"]), "gene": str(r["gene"]), "label": str(r["label"])}
        for r in rows.to_dict("records")
    ]


def retrieve_examples(
    query_key: object,
    train_df: pd.DataFrame,
    train_keys: np.ndarray,
    k: int,
    seed: int,
) -> list[dict[str, str]] | None:
    """Pick up to ``k`` train rows whose key matches ``query_key`` (relevance-selected).

    ``train_keys[i]`` is the precomputed relevance key of ``train_df`` row ``i``. If
    fewer than ``k`` in-key rows exist, top up with random out-of-key rows so the
    prompt still shows ``k`` exemplars. Deterministic given ``seed``; leak-free by
    construction (train rows only).
    """
    if k <= 0 or len(train_df) == 0:
        return None
    rng = np.random.default_rng(seed)
    same = np.where(train_keys == query_key)[0]
    other = np.where(train_keys != query_key)[0]
    picked: list[int] = []
    if len(same) > 0:
        picked = rng.choice(same, size=min(k, len(same)), replace=False).tolist()
    if len(picked) < k and len(other) > 0:
        need = k - len(picked)
        picked += rng.choice(other, size=min(need, len(other)), replace=False).tolist()
    if not picked:
        return None
    rows = train_df.iloc[picked]
    return [
        {"pert": str(r["pert"]), "gene": str(r["gene"]), "label": str(r["label"])}
        for r in rows.to_dict("records")
    ]


def _make_examples_provider(
    train_df: pd.DataFrame,
    variant: Variant,
    seed: int,
    key_fn: ExampleKeyFn | None,
) -> ExamplesProvider:
    """Build a per-row exemplar provider for ``variant`` (leak-free: train rows only).

    ``random`` (or no ``key_fn``) → one fixed sampled set for every row. Otherwise
    each row retrieves train exemplars sharing its relevance key (train keys are
    precomputed once).
    """
    if variant.n_few_shot <= 0 or len(train_df) == 0:
        return lambda row: None
    if variant.retrieval == "random" or key_fn is None:
        fixed = sample_examples(train_df, variant, seed)
        return lambda row: fixed
    recs = train_df.to_dict("records")
    train_keys = np.array([key_fn(str(r["pert"]), str(r["gene"])) for r in recs], dtype=object)

    def _get(row: dict) -> list[dict[str, str]] | None:
        q_key = key_fn(str(row["pert"]), str(row["gene"]))
        return retrieve_examples(q_key, train_df, train_keys, variant.n_few_shot, seed)

    return _get


def _format(pert: str, gene: str, variant: Variant, examples: list[dict[str, str]] | None) -> str:
    if variant.prompt_template is not None:
        return variant.prompt_template.format(pert=pert, gene=gene, cell_desc=CELL_DESC)
    return format_prompt(pert, gene, examples=examples)


def make_prompt_row_predictor(infer_fn: InferFn) -> RowPredictor:
    """Track A predictor: format each row's prompt, call the model, parse to (up, down)."""

    def _predict(rows, variant, seed, get_examples):
        prompts = [_format(str(r["pert"]), str(r["gene"]), variant, get_examples(r)) for r in rows]
        return [parse_answer(t) for t in infer_fn(prompts, seed)]

    return _predict


def make_agent_row_predictor(agent_fn: AgentFn, concurrency: int = 1) -> RowPredictor:
    """Track B predictor: run the agent per row → graded (up, down).

    ``get_examples`` is ignored — the agent gathers evidence via tools rather than
    few-shot exemplars. ``concurrency`` runs the (slow) agents in a thread pool, as
    the Track B harness does; ``ex.map`` preserves row order.

    Note: ``seed`` is forwarded to ``agent_fn`` but the DSPy agent is unseeded
    (temperature=1.0), so multi-seed variants would just repeat identical runs — the
    CLI collapses Track B to a single seed. Multi-sample averaging is a separate lever.
    """

    def _predict(rows, variant, seed, get_examples):
        if concurrency <= 1:
            return [agent_fn(str(r["pert"]), str(r["gene"]), seed) for r in rows]
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            return list(ex.map(lambda r: agent_fn(str(r["pert"]), str(r["gene"]), seed), rows))

    return _predict


# agent_fn_for(variant) -> the AgentFn for that variant's tool config.
AgentFnFor = Callable[[Variant], AgentFn]
# critic(pert, gene, initial_pair) -> revised (up, down) after a self-critique pass.
Critic = Callable[[str, str, "tuple[float, float]"], "tuple[float, float]"]


def with_self_critique(agent_fn: AgentFn, critic: Critic) -> AgentFn:
    """Wrap ``agent_fn`` with a second self-critique/verify pass.

    The base agent produces a first prediction; ``critic`` then reviews it (in the
    CLI, a second LLM call re-examines the evidence) and returns a possibly-revised
    ``(up, down)``. Offline-testable: inject a deterministic ``critic``.
    """

    def _fn(pert: str, gene: str, seed: int) -> tuple[float, float]:
        return critic(pert, gene, agent_fn(pert, gene, seed))

    return _fn


def make_configurable_agent_row_predictor(
    agent_fn_for: AgentFnFor, concurrency: int = 1
) -> RowPredictor:
    """Track B predictor whose agent is chosen per ``(Variant.tools, self_critique)``.

    ``agent_fn_for(variant)`` builds the agent for that variant's tool config and
    critique setting; the result is cached by ``(tools, self_critique)`` so each
    (expensive) agent is built once and reused across rows and self-consistency
    seeds. Delegates per-config to :func:`make_agent_row_predictor`, so the same
    split/score/gate harness drives the agentic search. Offline-testable with a
    fake ``agent_fn_for``.
    """
    cache: dict[object, RowPredictor] = {}

    def _predict(rows, variant, seed, get_examples):
        key = (variant.tools, variant.self_critique)
        rp = cache.get(key)
        if rp is None:
            rp = make_agent_row_predictor(agent_fn_for(variant), concurrency)
            cache[key] = rp
        return rp(rows, variant, seed, get_examples)

    return _predict


def predict_variant(
    df: pd.DataFrame,
    variant: Variant,
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    example_key_fn: ExampleKeyFn | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run ``variant`` over the val partition; return ``(val_idx, up, down)``.

    Prediction runs on val rows only (train rows would only add cost). Per-row
    predictions are averaged across ``variant.seeds`` — the multi-sample recipe that
    turns hard up/down calls into graded scores. ``example_key_fn`` supplies the
    relevance key when ``variant.retrieval`` selects exemplars by relevance.
    """
    train_idx, val_idx = holdout_split(df, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac)
    get_examples = _make_examples_provider(df.iloc[train_idx], variant, seed, example_key_fn)
    val_rows = df.iloc[val_idx].to_dict("records")

    if not val_rows:
        empty = np.zeros(0, dtype=float)
        return val_idx, empty, empty

    per_seed = [
        np.array(row_predictor(val_rows, variant, s, get_examples), dtype=float)
        for s in variant.seeds
    ]
    mean_pairs = np.stack(per_seed).mean(axis=0)
    return val_idx, mean_pairs[:, 0], mean_pairs[:, 1]


def run_variant(
    df: pd.DataFrame,
    variant: Variant,
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    example_key_fn: ExampleKeyFn | None = None,
    **record_kwargs: object,
) -> TrialRecord:
    """Evaluate ``variant`` on the dual-OOD val split → a :class:`TrialRecord`."""
    val_idx, up, down = predict_variant(
        df,
        variant,
        row_predictor,
        seed=seed,
        pert_frac=pert_frac,
        gene_frac=gene_frac,
        example_key_fn=example_key_fn,
    )
    labels = df.iloc[val_idx]["label"].to_numpy()
    metrics = evaluate(labels, up, down)
    metrics["n_val"] = int(len(val_idx))
    return TrialRecord(variant=variant, metrics=metrics, **record_kwargs)  # type: ignore[arg-type]


# on_trial(record, history_so_far) — persistence/side-effect hook per trial.
OnTrial = Callable[[TrialRecord, "list[TrialRecord]"], None]


def run_loop(
    df: pd.DataFrame,
    proposer: "Proposer",
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    max_trials: int | None = None,
    on_trial: OnTrial | None = None,
    example_key_fn: ExampleKeyFn | None = None,
) -> list[TrialRecord]:
    """Drive ``propose → run_variant → reflect`` until the proposer converges.

    Each cycle: build the reflection from the history so far, ask ``proposer`` for
    the next :class:`Variant` (``None`` → converged, stop), evaluate it on the
    OOD-val split, append the record, and fire ``on_trial`` (persist/archive).
    Stops at ``max_trials`` if the proposer never converges. Returns the history.
    """
    history: list[TrialRecord] = []
    while max_trials is None or len(history) < max_trials:
        variant = proposer(reflect(history), history)
        if variant is None:
            break
        rec = run_variant(
            df,
            variant,
            row_predictor,
            seed=seed,
            pert_frac=pert_frac,
            gene_frac=gene_frac,
            example_key_fn=example_key_fn,
        )
        history.append(rec)
        if on_trial is not None:
            on_trial(rec, history)
    return history
