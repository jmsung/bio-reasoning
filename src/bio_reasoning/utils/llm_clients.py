from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from anthropic import Anthropic
from openai import AzureOpenAI, OpenAI

from .azure_openai_client import build_azure_openai_client, load_azure_openai_config

ProviderName = Literal["openai_compatible", "ollama", "openai", "anthropic", "azure_openai"]


@dataclass(frozen=True)
class ProviderConfig:
    provider: ProviderName
    model: str
    api_key: str
    api_base: str | None = None


def get_provider_name() -> ProviderName:
    provider = os.getenv("BIOREASONING_LLM_PROVIDER", "openai_compatible").strip().lower()
    allowed = {"openai_compatible", "ollama", "openai", "anthropic", "azure_openai"}
    if provider not in allowed:
        raise ValueError(
            "BIOREASONING_LLM_PROVIDER must be one of " f"{sorted(allowed)}, got {provider!r}."
        )
    return provider  # type: ignore[return-value]


def load_provider_config() -> ProviderConfig:
    provider = get_provider_name()
    if provider == "azure_openai":
        azure = load_azure_openai_config()
        return ProviderConfig(
            provider=provider,
            model=azure.deployment,
            api_key=azure.api_key or "",
            api_base=azure.azure_endpoint,
        )
    if provider == "anthropic":
        return ProviderConfig(
            provider=provider,
            model=os.getenv("BIOREASONING_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            api_base=os.getenv("BIOREASONING_ANTHROPIC_API_BASE") or None,
        )
    if provider == "openai":
        return ProviderConfig(
            provider=provider,
            model=os.getenv("BIOREASONING_OPENAI_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            api_base=os.getenv("BIOREASONING_OPENAI_API_BASE") or None,
        )
    if provider == "ollama":
        return ProviderConfig(
            provider=provider,
            model=os.getenv(
                "BIOREASONING_OLLAMA_MODEL", os.getenv("BIOREASONING_OPENAI_MODEL", "gpt-oss:120b")
            ),
            api_key=os.getenv("BIOREASONING_OLLAMA_API_KEY", "ollama"),
            api_base=os.getenv("BIOREASONING_OLLAMA_API_BASE", "http://localhost:11434/v1"),
        )
    return ProviderConfig(
        provider=provider,
        model=os.getenv("BIOREASONING_OPENAI_MODEL", "openai/gpt-oss-120b"),
        api_key=os.getenv(
            "BIOREASONING_OPENAI_API_KEY",
            os.getenv("OPENAI_API_KEY", "local-vllm-placeholder-key"),
        ),
        api_base=os.getenv("BIOREASONING_OPENAI_API_BASE", "http://localhost:8000/v1"),
    )


def build_client() -> OpenAI | Anthropic | AzureOpenAI:
    config = load_provider_config()
    if config.provider == "azure_openai":
        return build_azure_openai_client()
    if config.provider == "anthropic":
        kwargs: dict[str, Any] = {"api_key": config.api_key}
        if config.api_base:
            kwargs["base_url"] = config.api_base
        return Anthropic(**kwargs)

    kwargs = {"api_key": config.api_key}
    if config.api_base:
        kwargs["base_url"] = config.api_base
    return OpenAI(**kwargs)
