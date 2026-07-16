import numpy as np

from bio_reasoning.models.track_a_prior import PRIORS, predict


def test_known_category_maps_to_its_prior():
    cats = {"HK1": "housekeeping", "IL1": "immune"}
    up, down = predict(["HK1", "IL1"], cats)
    for i, sym in enumerate(["HK1", "IL1"]):
        u, d = PRIORS[cats[sym]]
        assert up[i] == d * u
        assert down[i] == d * (1.0 - u)
    # housekeeping skews up, immune skews down
    assert up[0] > down[0]
    assert down[1] > up[1]


def test_unknown_symbol_falls_back_to_other():
    up, down = predict(["NOPE"], {})
    u, d = PRIORS["other"]
    assert up[0] == d * u
    assert down[0] == d * (1.0 - u)


def test_score_invariants_hold_per_pair():
    syms = ["HK1", "IL1", "X"]
    cats = {"HK1": "housekeeping", "IL1": "immune"}
    up, down = predict(syms, cats)
    for i, sym in enumerate(syms):
        u, d = PRIORS[cats.get(sym, "other")]
        assert abs((up[i] + down[i]) - d) < 1e-12  # up + down == DE score
        assert abs(up[i] / (up[i] + down[i]) - u) < 1e-12  # DIR score


def test_output_arrays_aligned_and_sized():
    syms = ["a", "b", "c", "d"]
    up, down = predict(syms, {})
    assert isinstance(up, np.ndarray) and isinstance(down, np.ndarray)
    assert up.shape == down.shape == (len(syms),)
