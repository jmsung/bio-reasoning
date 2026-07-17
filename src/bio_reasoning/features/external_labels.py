"""External measured-response labels from PerturbQA (the Stage-0 transfer gate).

Every internal Track A channel *infers* DE/direction from static features of an
unseen ``(pert, gene)`` pair and fails at chance on DE. PerturbQA ships the
*curated, measured* labels for four human CRISPRi lines (K562, RPE1, HepG2,
Jurkat) in our exact ``(pert, gene) -> {DE, up/down}`` form — the pre-thresholded
Replogle-essential signal. This module loads them, ortholog-maps them onto Track A
(mouse) symbols, and measures whether the external *measurement* agrees with our
labels above chance — the one cheap number that decides the external-data lane.

Label convention (from PerturbQA ``examples/summer/parsing.py``):
- ``de`` label ``1`` = differentially expressed, ``0`` = none.
- ``dir`` label ``1`` = increase (up), ``0`` = decrease (down); defined only for DE-positive pairs.

Ortholog map is a first-pass uppercase (mouse ``Psmd4`` -> human ``PSMD4``), which
covers the 1:1 orthologs that dominate the essential/housekeeping core; a
``mygene``/``pybiomart`` refinement is a later add if coverage demands it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

CELL_LINES = ("k562", "rpe1", "hepg2", "jurkat")

# GO:BP keyword -> slice. Housekeeping/essential = the transferable core; immune =
# the macrophage-specific program the deep-dive predicts does NOT transfer.
_HOUSEKEEPING_KW = (
    "proteasome",
    "ubiquitin",
    "protein catabolic",
    "translation",
    "ribosom",
    "splic",
    "mrna",
    "rna processing",
    "rna cap",
    "trna",
    "transcription",
    "dna replication",
    "cell cycle",
    "mitotic",
    "mitochond",
    "vesicle",
    "golgi",
    "endoplasmic",
    "nuclear transport",
    "chromatin",
)
_IMMUNE_KW = (
    "immune",
    "interferon",
    "cytokine",
    "inflammat",
    "macrophage activation",
    "nf-kappab",
    "nfkappab",
    "defense response",
    "chemokine",
    "antigen",
    "toll-like",
    "interleukin",
    "innate",
    "leukocyte",
)


def to_human(symbol: str) -> str:
    """Ortholog first-pass: mouse title-case symbol -> human upper-case symbol."""
    return str(symbol).upper()


def classify_pert(go_terms: list[str]) -> str:
    """Bucket a pert as ``housekeeping`` | ``immune`` | ``other`` from its GO:BP terms.

    Immune keywords win ties (macrophage-specific signal is the discriminating axis).
    """
    blob = " ".join(go_terms).lower()
    if any(k in blob for k in _IMMUNE_KW):
        return "immune"
    if any(k in blob for k in _HOUSEKEEPING_KW):
        return "housekeeping"
    return "other"


def load_perturbqa(datasets_dir: str | Path, cell_lines=CELL_LINES) -> dict[tuple[str, str], dict]:
    """Aggregate PerturbQA de/dir CSVs into ``(PERT, GENE) -> scores`` across cell lines.

    For each pair present in one or more lines:
    - ``de_score`` = fraction of measuring lines where the pair is differentially expressed.
    - ``dir_score`` = fraction *up* among the lines that call it DE (``nan`` if none do).
    - ``n_de`` / ``n_dir`` = number of lines contributing to each score.

    Keys are already human upper-case (PerturbQA symbols); Track A queries are
    mapped via :func:`to_human` at lookup time.
    """
    datasets_dir = Path(datasets_dir)
    de_sum: dict[tuple[str, str], list[int]] = {}  # [n_de_lines, n_de_positive]
    dir_sum: dict[tuple[str, str], list[int]] = {}  # [n_dir_lines, n_up]
    for line in cell_lines:
        de = pd.read_csv(datasets_dir / f"{line}-de.csv")
        for pert, gene, lab in zip(
            de.pert.astype(str), de.gene.astype(str), de.label.astype(int), strict=True
        ):
            k = (pert.upper(), gene.upper())
            s = de_sum.setdefault(k, [0, 0])
            s[0] += 1
            s[1] += lab
        dr = pd.read_csv(datasets_dir / f"{line}-dir.csv")
        for pert, gene, lab in zip(
            dr.pert.astype(str), dr.gene.astype(str), dr.label.astype(int), strict=True
        ):
            k = (pert.upper(), gene.upper())
            s = dir_sum.setdefault(k, [0, 0])
            s[0] += 1
            s[1] += lab

    store: dict[tuple[str, str], dict] = {}
    for k, (n, pos) in de_sum.items():
        dn, dup = dir_sum.get(k, (0, 0))
        store[k] = {
            "de_score": pos / n,
            "n_de": n,
            "dir_score": (dup / dn) if dn else np.nan,
            "n_dir": dn,
        }
    return store


def transfer_agreement(track_df: pd.DataFrame, store: dict[tuple[str, str], dict]) -> dict:
    """Does the external measurement agree with Track A labels? (the Stage-0 gate).

    On the overlap (Track A pairs whose ortholog-mapped ``(PERT, GENE)`` is in the
    external store):
    - ``de_auroc`` = AUROC of external ``de_score`` predicting Track A DE (label != none).
    - ``dir_auroc`` = AUROC of external ``dir_score`` predicting Track A *up* (label == up),
      over pairs Track A calls up/down and the store gives a direction for.

    Returns the two AUROCs plus the support (``n_de``, ``n_dir``). AUROC is ``nan``
    when a slice has a single class or no support.
    """
    de_y, de_s, dir_y, dir_s = [], [], [], []
    for pert, gene, label in zip(track_df.pert, track_df.gene, track_df.label, strict=True):
        rec = store.get((to_human(pert), to_human(gene)))
        if rec is None:
            continue
        de_y.append(int(label != "none"))
        de_s.append(rec["de_score"])
        if label in ("up", "down") and not np.isnan(rec["dir_score"]):
            dir_y.append(int(label == "up"))
            dir_s.append(rec["dir_score"])
    return {
        "de_auroc": _safe_auroc(de_y, de_s),
        "dir_auroc": _safe_auroc(dir_y, dir_s),
        "n_de": len(de_y),
        "n_dir": len(dir_y),
    }


def _safe_auroc(y: list[int], s: list[float]) -> float:
    if len(set(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))
