"""Minimal OpenAI-compatible chat client (stdlib only).

Shared by any script that calls a chat/completions endpoint — local vLLM/Ollama
gpt-oss-120b or hosted gpt-oss-120b via OpenRouter. Kept dependency-free (urllib)
so it works in the Kaggle-upload zip and the trial-loop alike.
"""

from __future__ import annotations

import json
import urllib.request


def post_chat_completion(
    api_base: str,
    api_key: str,
    model: str,
    prompt: str,
    seed: int,
    max_tokens: int,
    timeout_s: int,
    reasoning_effort: str = "low",
) -> tuple[str, dict[str, float]]:
    """Call an OpenAI-compatible chat endpoint and return (text, token_stats).

    ``text`` concatenates any ``reasoning`` and ``content`` fields (reasoning
    models expose both); empty string if the response has no choices.
    """
    url = api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
        "top_p": 1.0,
        "seed": seed,
        "max_completion_tokens": max_tokens,
        "reasoning_effort": reasoning_effort,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        out = json.loads(resp.read().decode())

    usage = out.get("usage", {}) or {}
    token_stats = {
        "prompt_tokens": float(usage.get("prompt_tokens", 0)),
        "completion_tokens": float(usage.get("completion_tokens", 0)),
        "total_tokens": float(usage.get("total_tokens", 0)),
    }

    choices = out.get("choices", [])
    if choices:
        msg = choices[0].get("message", {}) or {}
        reasoning = msg.get("reasoning", "") or ""
        content = msg.get("content", "") or ""
        if isinstance(content, list):
            content = "\n".join(
                str(c.get("text", c.get("content", ""))) for c in content if isinstance(c, dict)
            )
        parts = [p for p in (str(reasoning).strip(), str(content).strip()) if p]
        return "\n\n".join(parts), token_stats

    return "", token_stats
