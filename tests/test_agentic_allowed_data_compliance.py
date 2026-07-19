"""Compliance guard: the agentic search must be able to exclude the Traxler tool.

Traxler native-macrophage perturbation data is NOT on the competition allowed-data
list (PerturbQA + Tahoe-100M only), so a Traxler-using survivor would be
non-submittable. `--no-traxler-tool` routes to include_traxler=False; this pins the
invariant that include_traxler=False yields a grid with zero Traxler configs.
"""

from bio_reasoning.trial_loop.agent_variants import agent_variant_grid


def test_grid_excludes_traxler_when_disabled():
    grid = agent_variant_grid(include_traxler=False)
    assert grid, "grid should still have GO/STRING configs"
    for v in grid:
        assert "traxler_direction" not in getattr(
            v, "tools", ()
        ), f"{v.id} uses the disallowed Traxler tool"


def test_grid_includes_traxler_when_enabled():
    grid = agent_variant_grid(include_traxler=True)
    assert any("traxler_direction" in getattr(v, "tools", ()) for v in grid)
