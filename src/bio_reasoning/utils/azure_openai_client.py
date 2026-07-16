from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from openai import AzureOpenAI, OpenAI

try:  # pragma: no cover
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
except Exception:  # pragma: no cover
    DefaultAzureCredential = None
    get_bearer_token_provider = None


@dataclass(frozen=True)
class AzureOpenAIConfig:
    azure_endpoint: str
    api_version: str
    deployment: str
    auth_mode: str
    api_key: str | None = None
    use_openai_base_url: bool = False
    openai_base_url: str | None = None


def _normalize_azure_endpoint(endpoint: str) -> tuple[bool, str | None, str]:
    """Return (use_openai_base_url, openai_base_url, azure_endpoint).

    Supports both classic Azure OpenAI resource endpoints like:
    - https://<resource>.openai.azure.com/

    and Azure AI Foundry / OpenAI-compatible endpoints like:
    - https://<host>/openai/v1
    - https://<host>/openai/v1/
    - https://<host>/openai/v1/responses
    """

    cleaned = endpoint.strip().rstrip("/")
    lower = cleaned.lower()
    if lower.endswith("/openai/v1/responses"):
        return True, cleaned[: -len("/responses")], cleaned
    if lower.endswith("/openai/v1"):
        return True, cleaned, cleaned

    parsed = urlsplit(cleaned)
    if "/openai/v1/" in parsed.path.lower():
        path = parsed.path
        idx = path.lower().index("/openai/v1/")
        base_path = path[: idx + len("/openai/v1")]
        base_url = urlunsplit((parsed.scheme, parsed.netloc, base_path, "", "")).rstrip("/")
        return True, base_url, cleaned

    return False, None, cleaned


def load_azure_openai_config() -> AzureOpenAIConfig:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21").strip()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
    auth_mode = os.getenv("AZURE_OPENAI_MODE", "key").strip().lower()
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip() or None

    if auth_mode not in {"key", "entra"}:
        raise ValueError("AZURE_OPENAI_MODE must be 'key' or 'entra'.")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI.")
    if not deployment:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT is required for Azure OpenAI.")
    if auth_mode == "key" and not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is required when AZURE_OPENAI_MODE=key.")

    use_openai_base_url, openai_base_url, normalized_endpoint = _normalize_azure_endpoint(endpoint)

    return AzureOpenAIConfig(
        azure_endpoint=normalized_endpoint,
        api_version=api_version,
        deployment=deployment,
        auth_mode=auth_mode,
        api_key=api_key,
        use_openai_base_url=use_openai_base_url,
        openai_base_url=openai_base_url,
    )


def build_azure_openai_client() -> AzureOpenAI | OpenAI:
    config = load_azure_openai_config()

    if config.use_openai_base_url:
        if config.auth_mode != "key":
            raise ValueError(
                "Foundry/OpenAI-compatible Azure endpoints currently require "
                "AZURE_OPENAI_MODE=key."
            )
        return OpenAI(api_key=config.api_key, base_url=config.openai_base_url)

    kwargs: dict[str, Any] = {
        "azure_endpoint": config.azure_endpoint,
        "api_version": config.api_version,
    }

    if config.auth_mode == "entra":
        if DefaultAzureCredential is None or get_bearer_token_provider is None:
            raise ImportError(
                "azure-identity is required for AZURE_OPENAI_MODE=entra. "
                "Install the optional 'azure' dependency group."
            )
        credential = DefaultAzureCredential()
        kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default",
        )
    else:
        kwargs["api_key"] = config.api_key

    return AzureOpenAI(**kwargs)
