import pytest
from anthropic import Anthropic
from openai import OpenAI

import bio_reasoning.utils.llm_clients as lc

PROVIDER_ENV = "BIOREASONING_LLM_PROVIDER"


def test_default_provider_is_openai_compatible(monkeypatch):
    monkeypatch.delenv(PROVIDER_ENV, raising=False)
    assert lc.get_provider_name() == "openai_compatible"


@pytest.mark.parametrize(
    "name", ["openai_compatible", "ollama", "openai", "anthropic", "azure_openai"]
)
def test_provider_name_accepts_each_valid(monkeypatch, name):
    monkeypatch.setenv(PROVIDER_ENV, name.upper())  # case-insensitive
    assert lc.get_provider_name() == name


def test_invalid_provider_raises(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "bogus")
    with pytest.raises(ValueError, match="BIOREASONING_LLM_PROVIDER"):
        lc.get_provider_name()


def test_config_anthropic(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("BIOREASONING_ANTHROPIC_MODEL", "claude-x")
    cfg = lc.load_provider_config()
    assert cfg.provider == "anthropic"
    assert cfg.model == "claude-x"
    assert cfg.api_key == "sk-ant-test"


def test_config_openai_defaults(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
    monkeypatch.delenv("BIOREASONING_OPENAI_MODEL", raising=False)
    cfg = lc.load_provider_config()
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4.1-mini"
    assert cfg.api_base is None


def test_build_client_routes_to_anthropic(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert isinstance(lc.build_client(), Anthropic)


def test_build_client_routes_to_openai(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
    assert isinstance(lc.build_client(), OpenAI)


def test_build_client_routes_to_azure(monkeypatch):
    monkeypatch.setenv(PROVIDER_ENV, "azure_openai")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dep")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "az-key")
    sentinel = object()
    monkeypatch.setattr(lc, "build_azure_openai_client", lambda: sentinel)
    assert lc.build_client() is sentinel
