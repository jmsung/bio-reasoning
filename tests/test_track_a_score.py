import numpy as np

from bio_reasoning.eval.track_a_score import score_preds

LABELS = np.array(["up", "down", "none", "up", "down", "none", "up", "none"])


def test_perfect_predictions_score_one():
    up = np.where(LABELS == "up", 1.0, 0.0)
    down = np.where(LABELS == "down", 1.0, 0.0)
    s = score_preds(LABELS, up, down)
    assert s["auroc_de"] == 1.0
    assert s["auroc_dir"] == 1.0
    assert s["mean"] == 1.0


def test_constant_predictions_score_half():
    c = np.full(len(LABELS), 0.5)
    s = score_preds(LABELS, c, c)
    assert abs(s["auroc_de"] - 0.5) < 1e-9
    assert abs(s["auroc_dir"] - 0.5) < 1e-9


def test_matches_official_metric_formula():
    # de_score = up + down ranks none-vs-DE; dir_score = up/(up+down) ranks
    # up-vs-down on DE rows — mirror the vendored kaggle_metric_track_a.py.
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(0)
    up = rng.random(len(LABELS))
    down = rng.random(len(LABELS))
    de_true = (LABELS != "none").astype(int)
    exp_de = roc_auc_score(de_true, up + down)
    m = LABELS != "none"
    exp_dir = roc_auc_score((LABELS[m] == "up").astype(int), up[m] / (up[m] + down[m]))
    s = score_preds(LABELS, up, down)
    assert abs(s["auroc_de"] - exp_de) < 1e-9
    assert abs(s["auroc_dir"] - exp_dir) < 1e-9
    assert abs(s["mean"] - (exp_de + exp_dir) / 2) < 1e-9
