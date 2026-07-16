"""Classify a perturbation gene as housekeeping / immune / other from GO:BP.

The Track A prior rests on the EDA finding that perturbation *category* drives
direction: housekeeping-gene knockdowns skew targets up, immune/myeloid ones
skew them down (`docs/track-a-eda.md`). We label the perturbed gene by keyword
matching over its Gene Ontology biological-process terms (mygene.info, mouse),
caching results so repeated runs are offline.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

_API = "https://mygene.info/v3/query?q=symbol:{sym}&species=mouse" "&fields=go.BP.term&size=1"

# Keyword sets over GO:BP term names. Heuristic (as in the EDA) — category
# claims are hypothesis-grade.
_HOUSEKEEPING = (
    "translation",
    "ribosom",
    "proteasom",
    "splic",
    "spliceosome",
    "rrna",
    "trna",
    "mrna processing",
    "rna processing",
    "chromatin",
    "cell cycle",
    "dna replication",
    "dna repair",
    "rna polymerase",
    "mitochond",
    "protein folding",
    "ubiquitin",
    "nucleocytoplasmic",
)
_IMMUNE = (
    "immune",
    "inflammat",
    "cytokine",
    "interferon",
    "interleukin",
    "defense response",
    "leukocyte",
    "macrophage",
    "toll-like",
    "chemokine",
    "antigen",
    "response to virus",
    "response to bacterium",
    "nf-kappab",
    "innate immune",
    "t cell",
    "b cell",
    "phagocyt",
)


def _fetch_go_bp(symbol: str) -> list[str]:
    url = _API.format(sym=urllib.parse.quote(symbol))
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode())
    hits = data.get("hits", [])
    if not hits:
        return []
    bp = hits[0].get("go", {}).get("BP", [])
    if isinstance(bp, dict):
        bp = [bp]
    return [t.get("term", "") for t in bp if isinstance(t, dict)]


def classify(symbol: str, terms: list[str]) -> str:
    text = " ".join(terms).lower()
    hk = sum(kw in text for kw in _HOUSEKEEPING)
    im = sum(kw in text for kw in _IMMUNE)
    if hk == 0 and im == 0:
        return "other"
    return "housekeeping" if hk > im else "immune" if im > hk else "other"


def annotate_perts(symbols, cache_path: str | Path) -> dict[str, str]:
    """Return {symbol: category} for unique symbols, caching GO terms to disk."""
    cache_path = Path(cache_path)
    cache: dict[str, list[str]] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())

    out: dict[str, str] = {}
    dirty = False
    for sym in dict.fromkeys(symbols):  # unique, order-preserving
        if sym not in cache:
            try:
                cache[sym] = _fetch_go_bp(sym)
            except Exception:
                cache[sym] = []
            dirty = True
        out[sym] = classify(sym, cache[sym])

    if dirty:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=0))
    return out
