"""Derive ``data/external/tahoe_drug_targets.json`` from Tahoe-100M drug metadata.

Downloads only ``metadata/drug_metadata.parquet`` (~40 KB) — NOT the ~92 GB
pseudobulk DE nor the 100M-cell expression matrix — and extracts the
``{drug: [target gene symbols]}`` map that the drug-MoA transfer channel needs.

Run: ``uv run --with pyarrow python scripts/fetch_tahoe_drug_targets.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

_URL = (
    "https://huggingface.co/datasets/tahoebio/Tahoe-100M/"
    "resolve/main/metadata/drug_metadata.parquet"
)
_OUT = Path(__file__).resolve().parents[1] / "data" / "external" / "tahoe_drug_targets.json"


def main() -> None:
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp, _ = urlretrieve(_URL)  # noqa: S310 — fixed HTTPS host
    meta = pd.read_parquet(tmp)
    out: dict[str, list[str]] = {}
    for drug, targets in zip(meta["drug"], meta["targets"], strict=True):
        if targets is None or (isinstance(targets, float) and np.isnan(targets)):
            continue
        genes = sorted({g.strip().upper() for g in re.split(r"[,;/|]", str(targets)) if g.strip()})
        if genes:
            out[str(drug)] = genes
    _OUT.write_text(json.dumps(out, indent=0))
    uniq = {g for v in out.values() for g in v}
    print(f"wrote {len(out)} drugs / {len(uniq)} unique target genes -> {_OUT}")


if __name__ == "__main__":
    main()
