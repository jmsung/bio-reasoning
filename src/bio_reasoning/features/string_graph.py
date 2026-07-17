"""Mouse STRING interaction-partner graph (cached), the neighbour-retrieval graph source.

``fetch_string_partners`` returns ``{symbol: {partner, …}}`` from string-db.org
(mouse, taxid 10090; public API, no key), caching to disk so repeated runs and a
fresh worktree are offline. Shared by every submission/eval that builds a
neighbour graph (Track A/B ``*_de_dir_*`` scripts) so the fetch lives in one place.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Sequence
from pathlib import Path

_API = "https://string-db.org/api/json/interaction_partners"


def fetch_string_partners(
    symbols: Sequence[str],
    cache_path: str | Path,
    species: int = 10090,
    batch: int = 60,
) -> dict[str, set[str]]:
    """Return ``{symbol: partners}`` from mouse STRING, cached to ``cache_path``.

    Cache-hit is offline. On a miss, symbols are queried in batches of ``batch``
    (1s between calls, per STRING's fair-use); a failed batch is skipped (its
    symbols get no partners) rather than aborting the whole fetch.
    """
    cache_path = Path(cache_path)
    if cache_path.exists():
        return {k: set(v) for k, v in json.loads(cache_path.read_text()).items()}

    syms = [str(s) for s in symbols]
    out: dict[str, set[str]] = {}
    for i in range(0, len(syms), batch):
        data = urllib.parse.urlencode(
            {"identifiers": "\n".join(syms[i : i + batch]), "species": species, "limit": 500}
        ).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(_API, data=data), timeout=90) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001 — a flaky batch shouldn't abort the run
            print("STRING fetch err", i, repr(e), flush=True)
            rows = []
        for row in rows:
            out.setdefault(row["preferredName_A"], set()).add(row["preferredName_B"])
        time.sleep(1)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({k: sorted(v) for k, v in out.items()}))
    return out
