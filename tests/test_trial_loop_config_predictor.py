"""Offline tests for the fusion-config-consuming row predictor (no network, fakes only).

PR #69 made a :class:`PipelineConfig` *representable + validated* but never *scored* — a
config-mutation child inherited the parent's prompt and so scored identically. These tests
prove the gap is closed: a config is actually consumed (named channels built + rank-fused
via :mod:`bio_reasoning.models.fuse`), so **a change in channel weights MOVES the score**
— the config axis is now selectable, not merely representable.

The channel builder is injected, so the whole path is offline-testable with a fake that
turns a deterministic gene-parity direction signal into per-channel ``r``: one channel
tracks the true direction, another opposes it, so shifting weight between them sweeps the
DIR-AUROC across its full range — the honest proof that weights drive the score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.models.fuse import Channel
from bio_reasoning.trial_loop.config_predictor import (
    leak_free_train_df,
    make_config_row_predictor,
)
from bio_reasoning.trial_loop.evolve import evolve_loop
from bio_reasoning.trial_loop.journal import append_journal_entry
from bio_reasoning.trial_loop.types import PipelineConfig, Variant

# ── Fixtures ─────────────────────────────────────────────────────────────────

_PRED = {"up": (1.0, 0.0), "down": (0.0, 1.0), "none": (0.0, 0.0)}


def _gene_idx(gene: str) -> int:
    return int(gene[1:])


def _dir_frame(n: int = 300) -> pd.DataFrame:
    """A frame whose DE-row direction is a deterministic function of gene parity.

    Even-indexed genes are ``up``, odd are ``down`` (with every third row ``none`` so
    both a DE axis and a direction axis exist). A channel that reads gene parity can
    therefore recover the direction perfectly — the controlled signal the fake builds.
    """
    rows = []
    for i in range(n):
        gene = f"g{i % 30}"
        pert = f"p{i % 25}"
        if i % 3 == 2:
            lab = "none"
        else:
            lab = "up" if _gene_idx(gene) % 2 == 0 else "down"
        rows.append({"pert": pert, "gene": gene, "label": lab})
    return pd.DataFrame(rows)


def _fake_channel_builder(seen: list[str] | None = None):
    """Build deterministic DIR channels from gene parity (a fake, offline signal source).

    ``GO-DIR`` tracks the true direction (r=1 for up-genes, 0 for down-genes); the other
    named channels OPPOSE it (r=0 for up-genes). So weight on GO-DIR vs the others sweeps
    the fused direction from perfect to inverted — proving weights move the score.
    """

    def _build(name: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> Channel:
        if seen is not None:
            seen.append(name)
        even = val_df["gene"].map(lambda g: _gene_idx(str(g)) % 2 == 0).to_numpy()
        if name == "GO-DIR":
            r = np.where(even, 1.0, 0.0)  # tracks truth
        else:
            r = np.where(even, 0.0, 1.0)  # opposes truth
        return Channel(name=name, r=r.astype(float))

    return _build


def _score(rows, up, down) -> dict:
    labels = np.array([r["label"] for r in rows])
    return evaluate(labels, np.asarray(up), np.asarray(down))


# ── leak-free train reconstruction ───────────────────────────────────────────


def test_leak_free_train_df_shares_no_pert_or_gene_with_val():
    # Two disjoint blocks: val uses perts/genes 0-4, the rest use 5-9. Excluding every
    # val pert AND gene must leave exactly the second block (leak-free reconstruction).
    df = pd.DataFrame(
        {
            "pert": [f"p{i}" for i in range(5)] + [f"p{5 + i}" for i in range(5)],
            "gene": [f"g{i}" for i in range(5)] + [f"g{5 + i}" for i in range(5)],
            "label": ["up", "down", "none", "up", "down"] * 2,
        }
    )
    val_df = df.iloc[:5].reset_index(drop=True)
    train = leak_free_train_df(df, val_df)
    assert not (set(train["pert"]) & set(val_df["pert"]))
    assert not (set(train["gene"]) & set(val_df["gene"]))
    assert len(train) == 5


# ── the CORE proof: different weights → different predictions AND score ───────


def test_different_weights_move_the_score():
    df = _dir_frame()
    rows = df.to_dict("records")
    predict = make_config_row_predictor(df, _fake_channel_builder())

    truth = Variant(
        id="cfg-truth",
        pipeline_config=PipelineConfig(("GO-DIR", "neighbour-DIR"), (1.0, 0.0)),
        seeds=(0,),
    )
    inverted = Variant(
        id="cfg-inv",
        pipeline_config=PipelineConfig(("GO-DIR", "neighbour-DIR"), (0.0, 1.0)),
        seeds=(0,),
    )

    p_truth = predict(rows, truth, 0, lambda _r: None)
    p_inv = predict(rows, inverted, 0, lambda _r: None)

    # predictions differ row-wise (the config is genuinely consumed, not ignored)
    assert p_truth != p_inv

    up_t = [u for u, _ in p_truth]
    dn_t = [d for _, d in p_truth]
    up_i = [u for u, _ in p_inv]
    dn_i = [d for _, d in p_inv]
    s_truth = _score(rows, up_t, dn_t)["auroc_dir"]
    s_inv = _score(rows, up_i, dn_i)["auroc_dir"]
    # truth-weighted config scores near-perfect direction; inverted near-zero — the
    # weight change swings DIR-AUROC across its full range. THE axis is now live.
    assert s_truth > 0.95
    assert s_inv < 0.05
    assert abs(s_truth - s_inv) > 0.5


def test_predictor_builds_the_named_channels_and_applies_weights():
    df = _dir_frame()
    rows = df.to_dict("records")
    seen: list[str] = []
    predict = make_config_row_predictor(df, _fake_channel_builder(seen))
    v = Variant(
        id="cfg",
        pipeline_config=PipelineConfig(("GO-DIR", "embedding-DIR"), (2.0, 1.0)),
        seeds=(0,),
    )
    preds = predict(rows, v, 0, lambda _r: None)
    # exactly the config's named channels were constructed (vocabulary honored)
    assert set(seen) == {"GO-DIR", "embedding-DIR"}
    assert len(preds) == len(rows)
    # heavier weight on the truth-tracking channel → direction leans correct
    assert _score(rows, [u for u, _ in preds], [d for _, d in preds])["auroc_dir"] > 0.5


# ── degradation: never crash on empty / malformed config ─────────────────────


def test_degrades_to_fallback_on_missing_config():
    df = _dir_frame()
    rows = df.to_dict("records")
    called = {"n": 0}

    def fallback(rows, variant, seed, get_examples):
        called["n"] += 1
        return [(0.7, 0.1) for _ in rows]

    predict = make_config_row_predictor(df, _fake_channel_builder(), fallback=fallback)
    v = Variant(id="prompt-only", seeds=(0,))  # pipeline_config is None
    preds = predict(rows, v, 0, lambda _r: None)
    assert called["n"] == 1
    assert preds == [(0.7, 0.1) for _ in rows]


def test_degrades_to_neutral_without_fallback_and_never_crashes():
    df = _dir_frame()
    rows = df.to_dict("records")

    def boom(name, train_df, val_df):
        raise RuntimeError("channel build blew up")

    predict = make_config_row_predictor(df, boom)  # no fallback
    v = Variant(
        id="cfg",
        pipeline_config=PipelineConfig(("GO-DIR",), (1.0,)),
        seeds=(0,),
    )
    preds = predict(rows, v, 0, lambda _r: None)  # must not raise
    assert preds == [(0.5, 0.5) for _ in rows]


def test_empty_channels_config_degrades():
    df = _dir_frame()
    rows = df.to_dict("records")
    predict = make_config_row_predictor(df, _fake_channel_builder())
    v = Variant(
        id="cfg-empty",
        pipeline_config=PipelineConfig((), ()),
        seeds=(0,),
    )
    preds = predict(rows, v, 0, lambda _r: None)  # must not raise
    assert preds == [(0.5, 0.5) for _ in rows]


# ── end-to-end: evolve routes prompt vs config children to their predictors ──

_PROMPT_SEED = (
    "Predict how a CRISPRi knockdown of {pert} affects {gene} in {cell_desc}.\n"
    "{examples_block}\n"
    "A) up-regulated\nB) down-regulated\nC) not significantly changed\n"
)


def _prompt_predictor(rows, variant, seed, get_examples):
    """A weak prompt predictor: abstains on everything → chance-level DIR-AUROC."""
    return [(0.0, 0.0) for _ in rows]


def _reflect_alternating():
    """Reflector: first child a config edit (strong truth-tracking fusion), rest a prompt."""
    state = {"n": 0}

    def _fn(_instruction: str) -> str:
        state["n"] += 1
        if state["n"] == 1:
            return (
                'REASON: fuse the direction channels\n{"target":"config",'
                '"channels":["GO-DIR","neighbour-DIR"],"weights":[1.0,0.0]}'
            )
        return "REASON: reword\n" + _PROMPT_SEED

    return _fn


def test_evolve_routes_config_and_prompt_children_to_their_predictors(tmp_path):
    df = _dir_frame()
    path = tmp_path / "journal.md"
    history: list = []

    def on_record(rec) -> None:
        history.append(rec)
        append_journal_entry(path, history)

    config_predict = make_config_row_predictor(
        df, _fake_channel_builder(), fallback=_prompt_predictor
    )
    res = evolve_loop(
        df,
        [Variant(id="seed", prompt_template=_PROMPT_SEED, seeds=(0,))],
        _prompt_predictor,
        propose_fn=lambda _i: _PROMPT_SEED,
        top_k=1,
        children_per_parent=2,
        max_generations=1,
        seeds=(0, 1),
        noise_band=0.0,
        dry_generations=99,
        reflect_fn=_reflect_alternating(),
        error_top_n=10,
        config_row_predictor=config_predict,
        on_record=on_record,
    )

    by_id = {r.variant.id: r for r in res.records}
    cfg_recs = [r for r in res.records if r.variant.pipeline_config is not None]
    prompt_child = [
        r for r in res.records if r.variant.pipeline_config is None and r.variant.id != "seed"
    ]
    assert cfg_recs, "no config child was produced"
    assert prompt_child, "no prompt child was produced"

    seed_mean = by_id["seed"].metrics["mean"]
    cfg_mean = cfg_recs[0].metrics["mean"]
    prompt_mean = prompt_child[0].metrics["mean"]

    # The config child was scored through the CONFIG predictor: its truth-tracking fusion
    # beats the abstaining prompt predictor decisively — a REAL, differentiated score.
    assert cfg_mean > seed_mean + 0.2
    # The prompt child stayed on the prompt predictor → it scores like the (abstaining) seed.
    assert abs(prompt_mean - seed_mean) < 1e-9
    # The journal carries the config child's real number, not the parent's.
    text = path.read_text()
    assert f"{cfg_mean:.3f}" in text or f"{cfg_mean:.2f}" in text
    assert cfg_mean != prompt_mean
