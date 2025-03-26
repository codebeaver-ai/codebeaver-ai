import os

import openai
import pytest

from codebeaver.models.openai import GPTModel, OpenAIProvider


def dummy_create(model, messages, **kwargs):
    """Dummy function to simulate successful OpenAI API call"""
    return {"id": "dummy", "object": "chat.completion", "model": model, "choices": []}


class DummyException(Exception):
    """Custom exception for dummy error simulation."""

    pass


def dummy_create_exception(model, messages, **kwargs):
    """Dummy function to simulate an exception during OpenAI API call"""
    raise DummyException("Dummy failure")


def set_api_key_env(key="dummy_key"):
    os.environ["OPENAI_API_KEY"] = key


def remove_api_key_env():
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]


def test_invalid_api_key():
    """Test that initializing OpenAIProvider without API key raises ValueError."""
    remove_api_key_env()
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
        OpenAIProvider(model="gpt-4")


def test_valid_provider_default_model(monkeypatch):
    """Test valid initialization of OpenAIProvider with default model (O3_MINI)."""
    set_api_key_env("dummy_key")
    provider = OpenAIProvider()
    # The default model is O3_MINI
    assert provider.model == GPTModel.O3_MINI.value


def test_valid_provider_with_alias(monkeypatch):
    """Test valid initialization with an alias for gpt-4."""
    set_api_key_env("dummy_key")
    provider = OpenAIProvider(model="4")
    # Should map to GPT4
    assert provider.model == GPTModel.GPT4.value


def test_invalid_model(monkeypatch):
    """Test initializing with an invalid model should raise ValueError."""
    set_api_key_env("dummy_key")
    with pytest.raises(ValueError, match="Invalid model"):
        OpenAIProvider(model="invalid-model")


def test_create_chat_completion_success(monkeypatch):
    """Test create_chat_completion returns correct response when OpenAI API call succeeds."""
    set_api_key_env("dummy_key")
    provider = OpenAIProvider(model="gpt-4")
    monkeypatch.setattr(openai.chat.completions, "create", dummy_create)
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.create_chat_completion(messages)
    assert response["id"] == "dummy"
    assert response["model"] == GPTModel.GPT4.value


def test_create_chat_completion_exception(monkeypatch):
    """Test create_chat_completion raises exception when OpenAI API call fails."""
    set_api_key_env("dummy_key")
    provider = OpenAIProvider(model="gpt-4")
    monkeypatch.setattr(openai.chat.completions, "create", dummy_create_exception)
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(Exception, match="Error creating chat completion with OpenAI:"):
        provider.create_chat_completion(messages)


def test_get_available_models():
    """Test get_available_models returns all models as defined in GPTModel enum."""
    models_available = OpenAIProvider.get_available_models()
    expected_models = [model.value for model in GPTModel]
    assert set(models_available) == set(expected_models)


def test_get_model_info_known_model():
    """Test get_model_info returns correct info for a known model and alias mapping."""
    info = OpenAIProvider.get_model_info("4")
    expected_info = OpenAIProvider.get_model_info(GPTModel.GPT4.value)
    assert info == expected_info


def test_get_model_info_unknown_model():
    """Test get_model_info returns default info for an unknown model."""
    info = OpenAIProvider.get_model_info("nonexistent")
    assert info.get("description") == "Model information not available"


def test_gpt_model_get_base_model():
    """Test GPTModel.get_base_model for different aliases and non-alias values."""
    # Test known alias
    assert GPTModel.get_base_model("4") == GPTModel.GPT4.value
    # Test non alias: should return same string
    assert GPTModel.get_base_model("gpt-4-32k") == "gpt-4-32k"


def teardown_module(module):
    """Cleanup environment variable after tests."""
    remove_api_key_env()
