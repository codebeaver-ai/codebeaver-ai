import os

import openai
import pytest

from src.codebeaver.models.deepseek import DeepSeekModel, DeepSeekProvider


# Fixture to set a dummy API key for tests
@pytest.fixture(autouse=True)
def set_dummy_api_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy_api_key")


def dummy_chat_completion(**kwargs):
    """Dummy function to simulate openai.ChatCompletion.create success response."""
    return {"dummy": "response", "input": kwargs}


def failing_chat_completion(**kwargs):
    """Dummy function to simulate openai.ChatCompletion.create error scenario."""
    raise Exception("Simulated API error")


def test_init_without_api_key(monkeypatch):
    """Test initialization of DeepSeekProvider without DEEPSEEK_API_KEY."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(
        ValueError, match="DEEPSEEK_API_KEY environment variable not set"
    ):
        DeepSeekProvider()


def test_invalid_model():
    """Test that initializing with an invalid model raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        # "invalid-model" is not a valid model.
        DeepSeekProvider(model="invalid-model")
    assert "Invalid model" in str(exc_info.value)


def test_get_available_models():
    """Test that get_available_models returns all defined models."""
    models = DeepSeekProvider.get_available_models()
    expected_models = [model.value for model in DeepSeekModel]
    assert set(models) == set(expected_models)


def test_get_model_info_known():
    """Test get_model_info returns correct information for a known model."""
    info = DeepSeekProvider.get_model_info(DeepSeekModel.CHAT.value)
    assert "description" in info
    assert info["description"] == "General-purpose chat model"


def test_get_model_info_unknown():
    """Test get_model_info returns default info for an unknown model."""
    info = DeepSeekProvider.get_model_info("nonexistent-model")
    assert info == {"description": "Model information not available"}


def test_create_chat_completion_success(monkeypatch):
    """Test create_chat_completion successfully returns a response."""
    monkeypatch.setattr(openai.ChatCompletion, "create", dummy_chat_completion)
    provider = DeepSeekProvider()
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.create_chat_completion(messages=messages, temperature=0.5)
    # Ensure dummy function was used and response matches dummy response
    assert "dummy" in response


def test_create_chat_completion_error(monkeypatch):
    """Test create_chat_completion raises an exception when openai.ChatCompletion.create fails."""
    monkeypatch.setattr(openai.ChatCompletion, "create", failing_chat_completion)
    provider = DeepSeekProvider()
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(
        Exception, match="Error creating chat completion with DeepSeek:"
    ):
        provider.create_chat_completion(messages=messages, temperature=0.5)
