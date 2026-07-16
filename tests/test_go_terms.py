"""Tests for the GO-term pair featurizer.

The featurizer learns a GO:BP term vocabulary for perturbation genes and for
target genes from the train fold, then encodes any pair as [pert term BoW |
target term BoW | shared-term count]. Because the vocabulary is GO terms (not
symbol identity), an unseen pert/gene at transform time still lands on shared
terms — the OOD generalization the char-ngram features lacked. Tests run offline
against pre-seeded caches.
"""

import numpy as np
import scipy.sparse as sp

import bio_reasoning.features.gene_function as gf
from bio_reasoning.features.go_terms import GoPairFeaturizer

PERT_GO = {"Rpl3": ["translation", "ribosome"], "Il6": ["cytokine", "inflammation"]}
GENE_GO = {"Ga": ["ribosome", "apoptosis"], "Gb": ["cytokine"], "Gc": []}


def _no_network(monkeypatch):
    monkeypatch.setattr(
        gf, "_fetch_go_bp", lambda s: (_ for _ in ()).throw(AssertionError(f"fetch {s}"))
    )


def test_fit_transform_shape_and_offline(tmp_path, monkeypatch, write_go_cache):
    _no_network(monkeypatch)
    pc = write_go_cache(PERT_GO, name="pert.json")
    gc = write_go_cache(GENE_GO, name="gene.json")
    f = GoPairFeaturizer(pc, gc, min_df=1).fit(["Rpl3", "Il6"], ["Ga", "Gb"])
    X = f.transform(["Rpl3", "Il6"], ["Ga", "Gb"])
    assert sp.issparse(X)
    assert X.shape == (2, f.n_features_)
    # pert vocab (4 terms) + gene vocab (3 terms) + 1 shared-count column
    assert f.n_features_ == 4 + 3 + 1


def test_shared_term_count_is_last_column(tmp_path, monkeypatch, write_go_cache):
    _no_network(monkeypatch)
    pc = write_go_cache(PERT_GO, name="pert.json")
    gc = write_go_cache(GENE_GO, name="gene.json")
    f = GoPairFeaturizer(pc, gc, min_df=1).fit(["Rpl3", "Il6"], ["Ga", "Gb"])
    X = f.transform(["Rpl3", "Il6"], ["Ga", "Gb"]).toarray()
    shared = X[:, -1]
    assert shared[0] == 1  # Rpl3{translation,ribosome} ∩ Ga{ribosome,apoptosis} = 1
    assert shared[1] == 1  # Il6{cytokine,inflammation} ∩ Gb{cytokine} = 1


def test_min_df_backs_off_when_vocab_would_be_empty(tmp_path, monkeypatch, write_go_cache):
    _no_network(monkeypatch)
    # Every term appears once → min_df=3 would empty the vocab; must not crash.
    pc = write_go_cache({"Pa": ["ta"], "Pb": ["tb"]}, name="pert.json")
    gc = write_go_cache({"Ga": ["tx"], "Gb": ["ty"]}, name="gene.json")
    f = GoPairFeaturizer(pc, gc, min_df=3).fit(["Pa", "Pb"], ["Ga", "Gb"])
    X = f.transform(["Pa"], ["Ga"])
    assert X.shape == (1, f.n_features_)
    assert f.n_features_ > 1  # backed off to min_df=1, vocab non-empty


def test_unseen_symbol_at_transform_drops_unknown_terms(tmp_path, monkeypatch, write_go_cache):
    _no_network(monkeypatch)
    pc = write_go_cache({**PERT_GO, "New": ["ribosome", "novel_term"]}, name="pert.json")
    gc = write_go_cache(GENE_GO, name="gene.json")
    f = GoPairFeaturizer(pc, gc, min_df=1).fit(["Rpl3", "Il6"], ["Ga", "Gb"])
    # 'New' was not in fit; 'ribosome' maps to a known column, 'novel_term' drops.
    X = f.transform(["New"], ["Gc"])
    assert X.shape == (1, f.n_features_)
    assert np.isfinite(X.toarray()).all()
