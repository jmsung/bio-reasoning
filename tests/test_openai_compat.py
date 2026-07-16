"""Offline tests for the shared OpenAI-compatible client (no network; fake urlopen)."""

from __future__ import annotations

import contextlib
import io
import json

import bio_reasoning.utils.openai_compat as oc


def _fake_urlopen(payload: dict):
    """Return a context-manager stand-in for urllib.request.urlopen(...)."""

    @contextlib.contextmanager
    def _cm(req, timeout=None):
        yield io.BytesIO(json.dumps(payload).encode())

    return _cm


def _call(monkeypatch, payload):
    monkeypatch.setattr(oc.urllib.request, "urlopen", _fake_urlopen(payload))
    return oc.post_chat_completion(
        api_base="http://x/v1",
        api_key="k",
        model="m",
        prompt="p",
        seed=0,
        max_tokens=8,
        timeout_s=1,
    )


def test_reasoning_and_content_are_concatenated(monkeypatch):
    text, tok = _call(
        monkeypatch,
        {
            "usage": {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8},
            "choices": [{"message": {"reasoning": "because", "content": "upregulated"}}],
        },
    )
    assert text == "because\n\nupregulated"
    assert tok == {"prompt_tokens": 3.0, "completion_tokens": 5.0, "total_tokens": 8.0}


def test_list_content_is_flattened(monkeypatch):
    text, _ = _call(
        monkeypatch,
        {"choices": [{"message": {"content": [{"text": "a"}, {"text": "b"}]}}]},
    )
    assert text == "a\nb"


def test_no_choices_returns_empty(monkeypatch):
    text, tok = _call(monkeypatch, {"choices": []})
    assert text == ""
    assert tok["total_tokens"] == 0.0
