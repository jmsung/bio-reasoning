"""Offline tests for the KB denylist + DE-votes variant grid."""

from __future__ import annotations

from bio_reasoning.trial_loop.de_variants import de_variant_grid, make_de_proposer
from bio_reasoning.trial_loop.ruled_out import RULED_OUT, is_ruled_out
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def test_de_grid_is_nonempty_and_all_live():
    grid = de_variant_grid()
    assert len(grid) >= 4
    assert all(not is_ruled_out(v.id) for v in grid)
    # every grid variant explores the live votes/self-consistency lane
    assert all(v.id.startswith("de-votes-") for v in grid)


def test_is_ruled_out_matches_dead_static_channels():
    assert is_ruled_out("string-degree-de")
    assert is_ruled_out("marginal-degree-x")
    assert is_ruled_out("neighbour-retrieval-de-v2")
    assert not is_ruled_out("de-votes-nfs4-random-s5")
    assert RULED_OUT  # non-empty registry


def test_proposer_never_emits_a_ruled_out_channel():
    # a poisoned candidate list containing a dead static channel
    poisoned = [
        Variant(id="string-degree-de"),  # ruled out — must be skipped
        Variant(id="de-votes-nfs0-s3"),
        Variant(id="marginal-degree-fuse"),  # ruled out
        Variant(id="de-votes-nfs4-random-s5"),
    ]
    proposer = make_de_proposer(poisoned)
    emitted, history = [], []
    while (v := proposer("", history)) is not None:
        emitted.append(v)
        history.append(TrialRecord(variant=v, metrics={"mean": 0.5}))
    assert emitted  # some live ones got through
    assert all(not is_ruled_out(v.id) for v in emitted)
    assert {v.id for v in emitted} == {"de-votes-nfs0-s3", "de-votes-nfs4-random-s5"}
