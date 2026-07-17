"""Offline tests for the shared STRING partner fetch (cache-hit path, no network)."""

import json

from bio_reasoning.features.string_graph import fetch_string_partners


def test_cache_hit_is_offline(tmp_path):
    cache = tmp_path / "string.json"
    cache.write_text(json.dumps({"Stat1": ["Irf1", "Jak2"], "Rpl3": ["Rps6"]}))
    # No network: a cache hit returns sets, never calls the API.
    out = fetch_string_partners(["Stat1", "Rpl3"], cache)
    assert out == {"Stat1": {"Irf1", "Jak2"}, "Rpl3": {"Rps6"}}
    assert isinstance(out["Stat1"], set)
