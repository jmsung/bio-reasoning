"""Offline tests for the optimization journal — human-readable per-iteration log.

The journal is what lets a reader see whether the search is improving or
random-walking: per iteration it shows the config, the knob that changed vs the
running best, the result with a noise band, and the best-so-far trajectory. These
tests assert the rendered CONTENT (not merely that a file was written).
"""

from __future__ import annotations

from bio_reasoning.trial_loop.journal import append_journal_entry, render_journal_entry
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def _rec(
    variant: Variant,
    mean: float,
    baseline_mean: float,
    *,
    accepted: bool,
    band: float,
    de: float = 0.5,
    dir_: float = 0.5,
) -> TrialRecord:
    return TrialRecord(
        variant=variant,
        metrics={
            "mean": mean,
            "baseline_mean": baseline_mean,
            "auroc_de": de,
            "auroc_dir": dir_,
            "n_val": 200,
            "min_margin": mean - baseline_mean,
            "feasibility_ratio": 1.0 if accepted else 0.0,
            "accepted": float(accepted),
        },
        reflection=f"vs base: margins=[{mean - baseline_mean:.3f}] band={band:.3f} accepted={accepted}",
    )


def _history() -> list[TrialRecord]:
    return [
        _rec(Variant(id="v-default"), 0.55, 0.50, accepted=True, band=0.040, de=0.56, dir_=0.54),
        _rec(
            Variant(id="v-fewshot4", n_few_shot=4),
            0.60,
            0.55,
            accepted=True,
            band=0.030,
            de=0.62,
            dir_=0.58,
        ),
        _rec(
            Variant(id="v-go", n_few_shot=4, retrieval="go_category"),
            0.58,
            0.60,
            accepted=False,
            band=0.050,
        ),
    ]


def test_first_entry_reports_config_and_result() -> None:
    hist = _history()[:1]
    entry = render_journal_entry(hist)
    assert "iter 1" in entry
    assert "prompt=default" in entry and "few_shot=0" in entry
    assert "retrieval=random" in entry and "samples=3" in entry  # default seeds (42,43,44)
    assert "ACCEPTED" in entry and "REJECTED" not in entry
    assert "± 0.040" in entry  # noise band surfaced
    assert "de 0.560" in entry and "dir 0.540" in entry


def test_knob_diff_vs_running_best() -> None:
    hist = _history()[:2]
    entry = render_journal_entry(hist)  # entry for iter 2
    # iter 2 changed few_shot 0->4 vs the running best (iter 1, few_shot=0)
    assert "few_shot 0" in entry and "4" in entry
    assert "changed-vs-best" in entry
    assert "+0.050" in entry  # Δ vs baseline it was gated against
    assert "ACCEPTED" in entry


def test_rejected_entry_and_trajectory_and_best_so_far() -> None:
    hist = _history()  # 3 trials, last rejected
    entry = render_journal_entry(hist)
    assert "iter 3" in entry
    assert "REJECTED" in entry and "ACCEPTED" not in entry
    # the rejected variant changed retrieval vs the running best (iter 2)
    assert "retrieval random" in entry and "go_category" in entry
    assert "-0.020" in entry  # Δ vs-best is negative (inside/over the band)
    # best-so-far points back to iter 2 (0.600), not the current 0.580
    assert "best-so-far: 0.600 (iter 2)" in entry
    # full trajectory across all trials
    assert "0.550 → 0.600 → 0.580" in entry


def test_delta_inside_noise_band_is_readable() -> None:
    # Δ (-0.020) is smaller than the band (0.050): the reader can see it's within noise.
    entry = render_journal_entry(_history())
    assert "± 0.050" in entry


def test_append_writes_only_the_newest_entry(tmp_path) -> None:
    hist = _history()
    path = tmp_path / "journal.md"
    append_journal_entry(path, hist[:1])
    append_journal_entry(path, hist[:2])
    append_journal_entry(path, hist[:3])
    text = path.read_text()
    # each iteration's header line ("iter N | config") appears exactly once
    assert text.count("iter 1 | config") == 1
    assert text.count("iter 2 | config") == 1
    assert text.count("iter 3 | config") == 1
    assert text.count("# Optimization journal") == 1  # header written once
    # order preserved
    assert (
        text.index("iter 1 | config")
        < text.index("iter 2 | config")
        < text.index("iter 3 | config")
    )


def test_free_form_prompt_template_full_text_logged() -> None:
    tmpl = "Predict {pert} on {gene} in {cell_desc}. " + "REASON STEP. " * 20
    hist = [
        _rec(Variant(id="tmpl-v", prompt_template=tmpl), 0.57, 0.50, accepted=True, band=0.02),
    ]
    entry = render_journal_entry(hist)
    # config line shows a stable hash label, not the raw multi-line text
    assert "prompt=template#" in entry
    # but the full template text is logged somewhere in the entry (appendix / fenced block)
    assert "REASON STEP." in entry
    assert tmpl.strip() in entry
