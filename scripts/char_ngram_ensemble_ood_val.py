"""Does a char-ngram channel add over GO two-stage + neighbour-DIR? (OOD-val)

The probe (#39) found identity/family features carry a real-test signal our
dual-OOD split understates by ~0.06. Our best (GO two-stage DE + neighbour-DIR)
uses no char-ngram. This fuses a char-ngram channel in through the same
`fuse()`/`cfa_gate()` harness and compares on the holdout dual-OOD val split.

Honest expectation: char-ngram is ~chance on OUR split, so OOD-val will likely be
flat/negative and the CFA gate may reject it — the +0.06 lift (if any) is a
real-LB effect, not visible here. A flat OOD-val therefore doesn't kill the idea;
a clear regression does.

Measured (holdout seed 0): baseline GO+neighbour-DIR 0.5663 → +char 0.5485 (DE+DIR)
/ 0.5532 (DIR-only) — a clear **regression**, and the CFA gate REJECTs char
(DE-AUROC 0.487). Verdict: dead lever; char's chance-level direction dilutes the
strong neighbour-DIR. See mb/notes/rank1-plan.md (Killed/deferred).

Run: uv run --group eval python scripts/char_ngram_ensemble_ood_val.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
from bio_reasoning.features.pair_features import CharNgramFeaturizer
from bio_reasoning.features.string_graph import fetch_string_partners
from bio_reasoning.models.fuse import Channel, cfa_gate, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_universe.json"
SEED = 0


def _de_r(up: np.ndarray, down: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    de = up + down
    return de, np.divide(up, de, out=np.full_like(de, 0.5), where=de > 0)


def _score(name: str, labels, up, down) -> None:
    r = evaluate(labels, up, down)
    print(f"{name:<34}{r['auroc_de']:>9.3f}{r['auroc_dir']:>10.3f}{r['mean']:>9.4f}")


def main() -> None:
    df = pd.read_csv(TRAIN)
    tr, va = holdout_split(df, seed=SEED)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    labels = val.label.to_numpy()
    de_true = (labels != "none").astype(int)

    # GO two-stage (DE + direction)
    go = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert, train.gene, train.label.to_numpy()
    )
    up_go, down_go = go.predict(val.pert.tolist(), val.gene.tolist())
    s_de_go, r_go = _de_r(up_go, down_go)

    # Char-ngram two-stage (the identity channel under test)
    ch = TwoStageDEDIR(featurizer=CharNgramFeaturizer()).fit(
        train.pert, train.gene, train.label.to_numpy()
    )
    up_ch, down_ch = ch.predict(val.pert.tolist(), val.gene.tolist())
    s_de_ch, r_ch = _de_r(up_ch, down_ch)

    # Neighbour-retrieval direction channel
    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    partners = fetch_string_partners(syms, STRING_CACHE)
    q = val[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train)
    nb = neighbor_channel(q, train, pnb, gnb, min_support=3)

    c_go = Channel("go", s_de=s_de_go, r=r_go)
    c_ch = Channel("char", s_de=s_de_ch, r=r_ch)
    c_ch_dir = Channel("char-dir", s_de=None, r=r_ch)
    c_nb = Channel("nb", s_de=None, r=nb.r)

    print(f"\n{'config':<34}{'auroc_de':>9}{'auroc_dir':>10}{'mean':>9}")
    _score("GO alone", labels, up_go, down_go)
    _score("char-ngram alone", labels, up_ch, down_ch)
    base_up, base_down = fuse([c_go, c_nb])
    _score("baseline: GO + neighbour-DIR", labels, base_up, base_down)
    e_up, e_down = fuse([c_go, c_ch, c_nb])
    _score("+ char (DE+DIR)", labels, e_up, e_down)
    ed_up, ed_down = fuse([c_go, c_ch_dir, c_nb])
    _score("+ char (DIR only)", labels, ed_up, ed_down)

    base_mean = evaluate(labels, base_up, base_down)["mean"]
    for tag, (u, d) in [("char DE+DIR", (e_up, e_down)), ("char DIR-only", (ed_up, ed_down))]:
        delta = evaluate(labels, u, d)["mean"] - base_mean
        print(f"  Δ vs baseline ({tag}): {delta:+.4f}")

    # current_s_de is s_de_go: the neighbour channel is r-only, so the fused baseline's
    # s_de bus is exactly GO's — char must add DE signal over GO, not over the fusion.
    passed, stats = cfa_gate(s_de_ch, s_de_go, de_true)
    print(
        f"\nCFA gate on char DE channel: {'PASS' if passed else 'REJECT'} "
        f"(standalone DE-AUROC {stats['auroc']:.3f} vs min 0.55; "
        f"|corr| {stats['corr']:.3f} vs max 0.5)"
    )
    print(
        "\nReminder: char-ngram is ~chance on OUR dual-OOD split; the identity signal is "
        "understated here by ~0.06 (probe #39). A flat OOD-val does not kill the idea — "
        "only a clear regression does. The honest test is a real LB submission (Goal 3)."
    )


if __name__ == "__main__":
    main()
