"""Tahoe-100M drug-perturbation transfer onto the Track A CRISPRi task.

Tahoe-100M is a ~100M-cell atlas of ~1,100 **small-molecule** perturbations across
50 **cancer** cell lines ([[2025-zhang-tahoe-100m]]). Track A is **genetic** CRISPRi
knockdown in **mouse macrophages**. The only leak-free way Tahoe can touch our
``(pert_gene X, readout_gene Y) -> {up, down, none}`` task is the **drug-MoA channel**:
a Tahoe drug that *inhibits* gene X is a rough proxy for "knocking down X", so Tahoe's
drug-induced differential expression of gene Y proxies the (X -> Y) response.

This module is deliberately data-light. It carries:

- :func:`load_drug_targets` / :func:`covered_perts` — the drug-MoA coverage: which
  Track A perturbation genes are the *target* of some Tahoe drug (the only perts a
  drug-MoA channel could ever score). This is the feasibility crux — our CRISPRi
  panel is dominated by structural/housekeeping genes with no selective inhibitor in
  Tahoe's oncology drug set, so coverage is ~3%.
- :func:`perfect_oracle_channel` — a **leakage-allowed upper bound**. It gives the
  covered rows their *true* DE and direction (the best any Tahoe drug-MoA channel could
  possibly achieve, ignoring the drug!=knockdown and cancer!=macrophage mismatches and
  selection inflation) and leaves the rest ``NaN``. Fusing this oracle bounds the lane:
  if even a perfect Tahoe channel at ~3% coverage cannot move the dual-OOD mean-AUROC
  above seed noise, the real (mismatched, noisy) channel cannot either. Mirrors the
  ``de-ceiling-probe`` oracle method ([[de-unlearnable-oracle-ceiling]]).

The channel is labelled ORACLE and is never a submission path.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.models.fuse import Channel


def load_drug_targets(path: str | Path) -> dict[str, list[str]]:
    """Load the ``{drug: [target gene symbols]}`` map derived from Tahoe drug metadata.

    Symbols are upper-case human (Tahoe convention). Produced offline by
    ``scripts/fetch_tahoe_drug_targets.py`` from ``metadata/drug_metadata.parquet``.
    """
    with open(path) as fh:
        return json.load(fh)


def target_genes(drug_targets: dict[str, list[str]]) -> set[str]:
    """The set of all genes that are the target of at least one Tahoe drug (upper-case)."""
    return {g.upper() for genes in drug_targets.values() for g in genes}


def covered_perts(perts, drug_targets: dict[str, list[str]]) -> set[str]:
    """Track A perturbation symbols (any case) that a drug-MoA channel could score.

    A pert gene X is *covered* iff some Tahoe drug targets X (inhibition ~ knockdown),
    so Tahoe carries a drug-induced transcriptome that proxies knocking down X. Match
    is on upper-cased symbol (the mouse->human ortholog first pass, as in
    ``external_labels.to_human``).
    """
    tgt = target_genes(drug_targets)
    return {str(p) for p in perts if str(p).upper() in tgt}


def coverage_report(track_df: pd.DataFrame, drug_targets: dict[str, list[str]]) -> dict:
    """Row/pert coverage of the drug-MoA channel over a Track A frame.

    Returns covered-row fraction, covered-pert list, and pert-coverage fraction — the
    feasibility number that decides whether the channel can matter at all.
    """
    cov = covered_perts(track_df["pert"], drug_targets)
    row_mask = track_df["pert"].astype(str).isin(cov)
    n_perts = track_df["pert"].nunique()
    return {
        "n_rows": int(len(track_df)),
        "n_rows_covered": int(row_mask.sum()),
        "row_coverage": float(row_mask.mean()) if len(track_df) else 0.0,
        "n_perts": int(n_perts),
        "n_perts_covered": len(cov),
        "pert_coverage": (len(cov) / n_perts) if n_perts else 0.0,
        "covered_perts": sorted(cov),
    }


def perfect_oracle_channel(
    queries: pd.DataFrame, labels, drug_targets: dict[str, list[str]]
) -> tuple[Channel, np.ndarray]:
    """A leakage-allowed *perfect* Tahoe drug-MoA channel — the transfer upper bound.

    On rows the drug-MoA channel *covers* (pert is a Tahoe drug target), emit the
    **true** DE score (1 if the row is DE else 0) and **true** direction ``r`` (1 if
    up, 0 if down; ``0.5`` for none — direction is undefined there). Uncovered rows
    stay ``NaN`` so :func:`fuse` defers to the other channels. This is the best case any
    Tahoe drug-MoA channel could achieve; the real channel does strictly worse (drug !=
    knockdown, cancer != macrophage, selection inflation). Returns the channel and a
    boolean ``covered`` mask.
    """
    labels = np.asarray(labels)
    if len(queries) != len(labels):
        raise ValueError("queries and labels must align row-for-row")
    cov = covered_perts(queries["pert"], drug_targets)
    covered = queries["pert"].astype(str).isin(cov).to_numpy()
    n = len(queries)
    s_de = np.full(n, np.nan)
    r = np.full(n, np.nan)
    is_de = labels != "none"
    s_de[covered] = is_de[covered].astype(float)
    r_vals = np.where(labels == "up", 1.0, np.where(labels == "down", 0.0, 0.5))
    r[covered] = r_vals[covered]
    return Channel(name="tahoe_oracle", s_de=s_de, r=r), covered
