"""Offline tests for the population-based AlphaEvolve driver (no network, fakes only).

These assert real evolutionary behaviour — the population climbs across generations,
top-K selection is elitist (the best individual is never dropped), best-so-far is
monotone, dry/budget stops trip, and the journal reflects the trajectory — not merely
that the loop "ran". The fake ``propose_fn`` returns valid mutated templates and the
fake predictor turns a template-embedded quality knob into a deterministic score.
"""

from __future__ import annotations

import re

import pandas as pd

from bio_reasoning.trial_loop.evolve import Individual, evolve_loop
from bio_reasoning.trial_loop.journal import append_journal_entry
from bio_reasoning.trial_loop.types import Variant

_PRED = {"up": (1.0, 0.0), "down": (0.0, 1.0), "none": (0.0, 0.0)}
_SCORE_RE = re.compile(r"SCORE=([0-9.]+)")


def _frame(n: int = 300) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 40}" for i in range(n)],
            "gene": [f"g{i % 37}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _template(score: float) -> str:
    """A valid free-form template (passes validate_prompt) with an embedded quality knob."""
    return (
        f"SCORE={score:.4f}\n"
        "Predict how a CRISPRi knockdown of {pert} affects {gene} in {cell_desc}.\n"
        "{examples_block}\n"
        "A) up-regulated\n"
        "B) down-regulated\n"
        "C) not significantly changed\n"
    )


def _stable_frac(pert: str, gene: str) -> float:
    return (abs(hash((pert, gene))) % 10_000) / 10_000.0


def _quality(variant: Variant) -> float:
    m = _SCORE_RE.search(variant.prompt_template or "")
    return float(m.group(1)) if m else 0.5


def _predictor(rows, variant, seed, get_examples):
    """Deterministic: predict the true label for a fraction ``quality`` of rows, else abstain.

    Higher embedded SCORE → more correct predictions → higher mean AUROC. Ignores seed
    so the only per-split-seed variation is the holdout redraw (a small, honest band).
    """
    p = _quality(variant)
    return [
        _PRED[r["label"]] if _stable_frac(r["pert"], r["gene"]) < p else (0.0, 0.0) for r in rows
    ]


def _improving_propose_fn():
    """Every call returns a strictly stronger template — the population must climb.

    Reads the per-child ``# Variation j`` hint the driver appends so children of one
    parent are distinct (diversity actually reaches distinct offspring).
    """
    state = {"n": 0}

    def _fn(instruction: str) -> str:
        state["n"] += 1
        m = re.search(r"# Variation (\d+)", instruction)
        j = int(m.group(1)) if m else 0
        score = min(0.50 + 0.03 * state["n"] + 0.002 * j, 0.98)
        return _template(score)

    return _fn


def _constant_propose_fn(score: float = 0.60):
    def _fn(instruction: str) -> str:
        return _template(score)

    return _fn


def _seed(score: float, sid: str = "seed") -> Variant:
    return Variant(id=sid, prompt_template=_template(score), seeds=(42,))


def test_population_evolves_and_best_is_monotone() -> None:
    res = evolve_loop(
        _frame(),
        [_seed(0.50)],
        _predictor,
        _improving_propose_fn(),
        top_k=2,
        children_per_parent=2,
        max_generations=3,
        seeds=(0, 1, 2),
        noise_band=0.0,
    )
    assert res.generations >= 2
    # best-so-far never decreases (elitist selection)
    traj = res.best_trajectory
    assert traj == sorted(traj), f"best-so-far not monotone: {traj}"
    # it actually climbed — the improving proposer produced something better than the seed
    assert traj[-1] > traj[0]
    # real mutation happened: many distinct child variant ids beyond the single seed
    child_ids = {r.variant.id for r in res.records}
    assert len(child_ids) >= 4
    # the surviving best is a mutated child, not the seed
    assert res.best.mean == max(ind.mean for ind in res.population)
    assert res.best.variant.id != "seed"


def test_topk_selection_keeps_the_best() -> None:
    # A strong seed; every child is weaker. Elitism must carry the seed forward and it
    # must remain the population best after several generations of worse offspring.
    res = evolve_loop(
        _frame(),
        [_seed(0.95, "champ"), _seed(0.55, "weak")],
        _predictor,
        _constant_propose_fn(0.55),
        top_k=2,
        children_per_parent=2,
        max_generations=4,
        seeds=(0, 1, 2),
        noise_band=0.03,
        dry_generations=99,  # disable dry-stop so we test selection, not stopping
    )
    assert res.best.variant.id == "champ"
    assert res.best.variant in [ind.variant for ind in res.population]
    # best-so-far pinned at the champion's level the whole run (offspring never beat it)
    assert res.best_trajectory[-1] == res.best_trajectory[0]


def test_dry_stop_fires() -> None:
    # Plateau: seed and every child score the same → no best-so-far improvement beyond
    # the band → dry-stop after ``dry_generations`` flat generations.
    res = evolve_loop(
        _frame(),
        [_seed(0.60)],
        _predictor,
        _constant_propose_fn(0.60),
        top_k=2,
        children_per_parent=2,
        max_generations=10,
        seeds=(0, 1, 2),
        noise_band=0.05,
        dry_generations=2,
    )
    assert res.stopped_reason == "dry"
    assert res.generations <= 3  # stopped shortly after the plateau set in


def test_budget_stop_fires() -> None:
    calls = {"n": 0}

    def counting_predictor(rows, variant, seed, get_examples):
        calls["n"] += 1
        return _predictor(rows, variant, seed, get_examples)

    res = evolve_loop(
        _frame(),
        [_seed(0.50)],
        counting_predictor,
        _improving_propose_fn(),
        top_k=2,
        children_per_parent=2,
        max_generations=10,
        seeds=(0, 1, 2),
        noise_band=0.0,
        budget=1.0,
        spent_fn=lambda: float(calls["n"]),
    )
    assert res.stopped_reason == "budget"
    assert res.spent >= 1.0


def test_children_are_diverse_within_a_generation() -> None:
    # Two offspring of the same parent in one generation must be distinct variants —
    # the driver's per-child diversity hint has to reach the proposer.
    res = evolve_loop(
        _frame(),
        [_seed(0.50)],
        _predictor,
        _improving_propose_fn(),
        top_k=1,
        children_per_parent=3,
        max_generations=1,
        seeds=(0,),
        noise_band=0.0,
        dry_generations=99,
    )
    # generation-1 children (records excluding the seed eval) are all distinct
    child_ids = [r.variant.id for r in res.records if r.variant.id != "seed"]
    assert len(child_ids) == 3
    assert len(set(child_ids)) == 3, f"children not diverse: {child_ids}"


def test_journal_reflects_the_trajectory(tmp_path) -> None:
    path = tmp_path / "journal.md"
    history: list = []

    def on_record(rec) -> None:
        history.append(rec)
        append_journal_entry(path, history)

    res = evolve_loop(
        _frame(),
        [_seed(0.50)],
        _predictor,
        _improving_propose_fn(),
        top_k=2,
        children_per_parent=2,
        max_generations=3,
        seeds=(0, 1, 2),
        noise_band=0.0,
        on_record=on_record,
    )
    text = path.read_text()
    assert "# Optimization journal" in text
    # one journal entry per evaluated record (seeds + children)
    assert text.count("| config:") == len(res.records)
    assert "best-so-far:" in text and "trajectory:" in text
    # the noise band recovered from each record's reflection is rendered (not "n/a")
    assert re.search(r"± [0-9]\.[0-9]{3}", text)
    # the full climbing trajectory is legible
    assert "iter 1 | config" in text and f"iter {len(res.records)} | config" in text


def test_individual_shape() -> None:
    res = evolve_loop(
        _frame(),
        [_seed(0.50)],
        _predictor,
        _improving_propose_fn(),
        top_k=1,
        children_per_parent=1,
        max_generations=1,
        seeds=(0, 1),
        noise_band=0.0,
        dry_generations=99,
    )
    ind = res.best
    assert isinstance(ind, Individual)
    assert len(ind.scores) == 2  # one score per split seed
    assert ind.band == max(ind.scores) - min(ind.scores)
    assert set(ind.metrics) >= {"mean", "auroc_de", "auroc_dir", "n_val"}
