from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

from bio_reasoning.utils import build_client, get_provider_name, load_provider_config  # noqa: E402


PROVIDER_ALIASES = {
    "gpt_oss": "openai_compatible",
    "openai_compatible": "openai_compatible",
    "ollama": "ollama",
    "openai": "openai",
    "azure": "azure_openai",
    "azure_openai": "azure_openai",
    "anthropic": "anthropic",
}


@dataclass
class SmokeResponse:
    provider: str
    model: str
    text: str
    raw: Any
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def normalize_provider(name: str | None) -> str | None:
    if name is None:
        return None
    key = name.strip().lower()
    if key not in PROVIDER_ALIASES:
        raise ValueError(f"Unsupported provider {name!r}. Expected one of: {sorted(PROVIDER_ALIASES)}")
    return PROVIDER_ALIASES[key]


def set_provider_override(provider: str | None) -> None:
    normalized = normalize_provider(provider)
    if normalized is not None:
        os.environ["BIOREASONING_LLM_PROVIDER"] = normalized


def _join_openai_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if text:
                    parts.append(str(text))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts)
    return str(content or "")


def run_chat_completion(
    *,
    prompt: str,
    provider: str | None = None,
    system_prompt: str | None = None,
    max_tokens: int = 256,
    reasoning_effort: str = "low",
    temperature: float | None = None,
) -> SmokeResponse:
    set_provider_override(provider)
    config = load_provider_config()
    client = build_client()
    actual_provider = get_provider_name()

    if actual_provider == "anthropic":
        kwargs: dict[str, Any] = {
            "model": config.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = client.messages.create(**kwargs)
        text = "\n".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        total_tokens = prompt_tokens + completion_tokens
        return SmokeResponse(
            provider=actual_provider,
            model=config.model,
            text=text,
            raw=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    kwargs = {
        "model": config.model,
        "messages": messages,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    use_reasoning_budget = actual_provider == "openai_compatible"
    if actual_provider == "azure_openai":
        api_base = (config.api_base or "").rstrip("/").lower()
        model_name = config.model.lower()
        use_reasoning_budget = api_base.endswith("/openai/v1") or model_name.startswith("gpt-5")

    if use_reasoning_budget:
        kwargs["max_completion_tokens"] = max_tokens
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    choice = response.choices[0].message
    reasoning = getattr(choice, "reasoning", None)
    content = _join_openai_message_content(getattr(choice, "content", ""))
    text = "\n\n".join(part for part in [str(reasoning or "").strip(), content.strip()] if part)
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens))
    return SmokeResponse(
        provider=actual_provider,
        model=config.model,
        text=text,
        raw=response,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
