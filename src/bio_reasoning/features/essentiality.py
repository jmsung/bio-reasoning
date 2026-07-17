"""DepMap gene essentiality — a leak-free per-gene marginal responsiveness feature.

The pairwise DE channels failed because DE for a specific unseen pair is
context-dominated and doesn't transfer. Essentiality is a *marginal* per-gene
property: essential / housekeeping genes are broadly responsive across contexts
(knowledge/wiki/findings/housekeeping-transfer-hypothesis.md), so it survives the
dual-OOD split where a train-derived DE rate would leak.

DepMap's continuous gene-effect matrix (``CRISPRGeneEffect.csv``) is ~450 MB; its
common-essential list and nonessential controls are a few KB each, so we use a
ternary score (essential +1 / nonessential -1 / unknown 0). Mouse symbols map to the
human ortholog by uppercasing (``Anxa2`` → ``ANXA2``).

Files (DepMap Public 23Q4, figshare mirror — the portal is behind a bot wall):
- common essentials:  https://ndownloader.figshare.com/files/43346706
- nonessential ctrls: https://ndownloader.figshare.com/files/43346370
"""

from __future__ import annotations

import json
import os
import urllib.request

ESSENTIAL_URL = "https://ndownloader.figshare.com/files/43346706"
NONESSENTIAL_URL = "https://ndownloader.figshare.com/files/43346370"


def parse_depmap_gene_list(text: str) -> set[str]:
    """Parse a DepMap gene-control file (``SYMBOL (ENTREZ)`` per line) → uppercase symbols.

    Tolerates a ``Gene`` header, blank lines, and entries without an Entrez suffix.
    """
    out: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower() == "gene":
            continue
        sym = line.split("(")[0].strip().upper()
        if sym:
            out.add(sym)
    return out


def ternary_essentiality(essential: set[str], nonessential: set[str]) -> dict[str, float]:
    """Map symbol → +1 (common-essential) / -1 (nonessential control).

    Symbols in neither set are absent (looked up as 0.0 = unknown downstream). On the
    rare overlap, essential wins (a gene flagged common-essential is essential).
    """
    m: dict[str, float] = {s: -1.0 for s in nonessential}
    m.update({s: 1.0 for s in essential})
    return m


def load_essentiality(cache_path: str) -> dict[str, float]:
    """Ternary essentiality map (UPPER symbol → +1/-1), fetched from DepMap and cached.

    Cached as JSON at ``cache_path`` on first call; offline thereafter.
    """
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    def _fetch(url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.read().decode(errors="replace")

    essential = parse_depmap_gene_list(_fetch(ESSENTIAL_URL))
    nonessential = parse_depmap_gene_list(_fetch(NONESSENTIAL_URL))
    m = ternary_essentiality(essential, nonessential)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(m, f)
    return m
