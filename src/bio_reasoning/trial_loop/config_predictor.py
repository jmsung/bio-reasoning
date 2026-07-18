"""Score a fusion :class:`PipelineConfig` — turn the config axis from *representable* into
*selectable*.

The evolve loop's prompt predictor (:func:`trial_loop.loop.make_prompt_row_predictor`)
ignores ``Variant.pipeline_config``, so a config-mutation child inherits the parent's
prompt and scores identically to it — the config axis proposed by
:mod:`trial_loop.reflective_mutation` is validated but never *evaluated*. This module
closes that gap with a **config-consuming** :data:`~trial_loop.loop.RowPredictor`: given a
validated config it builds the named DE/DIR channels, rank-fuses them per the config's
weights (reusing :func:`bio_reasoning.models.fuse.fuse` — no duplicated fusion logic), and
emits the same ``(up, down)`` per-row shape the evolve scorer consumes. So two configs
that fuse the same channels with *different weights* now produce *different* predictions
and *different* scores — the config axis is finally live.

Channel construction is deterministic and offline (retrieval + marginals, no LLM), so the
whole path is cheap and fully testable. The channel builder is injected (a
:data:`ChannelBuilder`), so tests wire a fake and the runner wires the real DE/DIR
builders (see :func:`direction_channel_builder`). Every failure — a missing/empty config,
an unbuildable channel, a raised exception — **degrades** to the injected ``fallback``
predictor (the prompt predictor, in the loop) or to neutral ``(0.5, 0.5)`` predictions, so
a bad config can never crash the search.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pandas as pd

from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.trial_loop.loop import RowPredictor
from bio_reasoning.trial_loop.types import Variant

# channel_builder(name, train_df, val_df) -> a fuse.Channel for ``name``, fit on ``train_df``
# and predicted on ``val_df`` (aligned to its rows). Raising for an unbuildable name is fine
# — the predictor degrades. Injected so the path is offline-testable with a fake.
ChannelBuilder = Callable[[str, pd.DataFrame, pd.DataFrame], Channel]


def leak_free_train_df(
    df: pd.DataFrame,
    val_df: pd.DataFrame,
    pert_col: str = "pert",
    gene_col: str = "gene",
) -> pd.DataFrame:
    """Return the rows of ``df`` that share **no** pert and **no** gene with ``val_df``.

    Channels are fit on train and predicted on the held-out val rows; the loop's
    :func:`~bio_reasoning.eval.split.holdout_split` guarantees train shares zero perts and
    zero genes with val, so excluding every val pert *and* val gene reconstructs a
    leak-free training partition from just the val rows (no split seed needed).
    """
    val_perts = set(val_df[pert_col].astype(str))
    val_genes = set(val_df[gene_col].astype(str))
    keep = ~df[pert_col].astype(str).isin(val_perts) & ~df[gene_col].astype(str).isin(val_genes)
    return df[keep].reset_index(drop=True)


def make_config_row_predictor(
    df: pd.DataFrame,
    channel_builder: ChannelBuilder,
    *,
    fallback: RowPredictor | None = None,
) -> RowPredictor:
    """Build a :data:`RowPredictor` that scores ``variant.pipeline_config`` by rank fusion.

    For a variant carrying a config, the returned predictor reconstructs the leak-free
    train partition (:func:`leak_free_train_df`), builds each named channel via
    ``channel_builder``, rank-fuses them with the config's ``weights``
    (:func:`bio_reasoning.models.fuse.fuse`), and returns one ``(up, down)`` per row. A
    variant with no config, an empty channel list, or a channel that fails to build
    **degrades**: to ``fallback`` when given (the prompt predictor, so a config child falls
    back to its parent's behaviour), else to neutral ``(0.5, 0.5)`` — never a crash.

    ``df`` supplies the training rows; ``get_examples`` is unused (channels gather their own
    evidence). Channel construction ignores the per-sample ``seed`` — the channels are
    deterministic given the split — so multi-sample averaging leaves the score unchanged.
    """

    def _degrade(rows, variant, seed, get_examples) -> Sequence[tuple[float, float]]:
        if fallback is not None:
            return fallback(rows, variant, seed, get_examples)
        return [(0.5, 0.5) for _ in rows]

    def _predict(rows, variant: Variant, seed, get_examples):
        cfg = variant.pipeline_config
        if cfg is None or not cfg.channels:
            return _degrade(rows, variant, seed, get_examples)
        try:
            val_df = pd.DataFrame(rows)
            train_df = leak_free_train_df(df, val_df)
            channels = [channel_builder(name, train_df, val_df) for name in cfg.channels]
            up, down = fuse(channels, weights=list(cfg.weights))
        except Exception:  # noqa: BLE001 — a bad config must never derail the search
            return _degrade(rows, variant, seed, get_examples)
        return list(zip(up.tolist(), down.tolist(), strict=True))

    return _predict


def direction_channel_builder(
    *,
    embeddings: dict,
    partners: dict[str, set[str]],
    pert_cache: str,
    gene_cache: str,
) -> ChannelBuilder:
    """Real builder for the three DIR channels (:data:`eval.direction_channels.CHANNELS`).

    Dispatches a channel name to its shipped constructor in
    :mod:`bio_reasoning.eval.direction_channels` — each fits on ``train_df`` and returns a
    per-row ``r`` = P(up) on ``val_df`` — and wraps the result in a direction-only
    :class:`~bio_reasoning.models.fuse.Channel`. Resources (embeddings, STRING partners, GO
    caches) are passed in by the caller, so this stays import-cheap and does no I/O — the
    same convention as ``direction_channels``. An unknown name raises, degrading the
    predictor rather than fusing a signal that does not exist.
    """
    from bio_reasoning.eval.direction_channels import embedding_dir_r, go_dir_r, neighbour_dir_r

    def _build(name: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> Channel:
        if name == "GO-DIR":
            r = go_dir_r(train_df, val_df, pert_cache, gene_cache)
        elif name == "neighbour-DIR":
            r = neighbour_dir_r(train_df, val_df, partners)
        elif name == "embedding-DIR":
            r = embedding_dir_r(train_df, val_df, embeddings)
        else:
            raise KeyError(f"no channel builder for {name!r}")
        return Channel(name=name, r=r)

    return _build
