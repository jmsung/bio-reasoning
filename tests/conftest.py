"""Shared fixtures for the test suite."""

import json

import numpy as np
import pytest

# Canonical Track A label vector: a mix of up / down / none with both DE classes
# and both directions present, so AUROC_de and AUROC_dir are always defined.
DE_LABELS = ["up", "down", "none", "up", "down", "none", "up", "none"]


@pytest.fixture
def de_labels() -> np.ndarray:
    """The canonical up/down/none label array used by score + metric tests."""
    return np.array(DE_LABELS)


@pytest.fixture
def write_go_cache(tmp_path):
    """Factory: write a {symbol: [GO terms]} cache to disk, return its path."""

    def _write(mapping: dict[str, list[str]], name: str = "go.json"):
        path = tmp_path / name
        path.write_text(json.dumps(mapping))
        return path

    return _write
