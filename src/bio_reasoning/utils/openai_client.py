from __future__ import annotations

import os

from openai import OpenAI


def build_openai_client() -> OpenAI:
    api_key = os.getenv("BIOREASONING_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    api_base = os.getenv("BIOREASONING_OPENAI_API_BASE") or None
    kwargs = {"api_key": api_key}
    if api_base:
        kwargs["base_url"] = api_base
    return OpenAI(**kwargs)


def get_openai_model_name(default: str = "gpt-4.1-mini") -> str:
    return os.getenv("BIOREASONING_OPENAI_MODEL", default)
