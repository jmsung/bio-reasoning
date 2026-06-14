from __future__ import annotations

import os

from anthropic import Anthropic


def build_anthropic_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    api_base = os.getenv("BIOREASONING_ANTHROPIC_API_BASE") or None
    kwargs = {"api_key": api_key}
    if api_base:
        kwargs["base_url"] = api_base
    return Anthropic(**kwargs)
