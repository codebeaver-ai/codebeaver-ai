import os

import openai
import pytest

from src.codebeaver.models.mistral import MistralModel, MistralProvider


def test_missing_api_key(monkeypatch):
    """Test that initializing MistralProvider without API key raises a ValueError."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(
        ValueError, match="MISTRAL_API_KEY environment variable not set"
    ):
        MistralProvider()


def test_invalid_model(monkeypatch):
    """Test that initializing with an invalid model name raises a ValueError."""
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy_api_key")
    with pytest.raises(ValueError, match="Invalid model"):
        MistralProvider("invalid-model")


def test_get_base_model_alias():
    """Test that get_base_model correctly maps alias names to base models."""
    base = MistralModel.get_base_model("codestral-latest")
    assert base == MistralModel.CODESTRAL.value
    base2 = MistralModel.get_base_model("unknown-model")
    assert base2 == "unknown-model"


def test_get_available_models():
    """Test that get_available_models returns a list of model names."""
    models = MistralProvider.get_available_models()
    assert isinstance(models, list)
    assert MistralModel.MISTRAL_SMALL.value in models


def test_get_model_info_valid():
    """Test that get_model_info returns correct information for a valid model alias."""
    info = MistralProvider.get_model_info("codestral-latest")
    assert "description" in info
    assert info["description"] == "Cutting-edge language model for coding"


def test_get_model_info_invalid():
    """Test that get_model_info returns the default info dict for an unknown model."""
    info = MistralProvider.get_model_info("nonexistent-model")
    assert info == {"description": "Model information not available"}


def test_create_chat_completion(monkeypatch):
    """Test that create_chat_completion returns a successful response when the API call works."""
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy_api_key")
    provider = MistralProvider()  # Default model is used
    fake_response = {"choices": [{"message": {"content": "Hello world"}}]}

    def fake_create(**kwargs):
        return fake_response

    # Replace the openai.ChatCompletion.create with our fake_create function
    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.create_chat_completion(messages)
    assert response == fake_response


def test_create_chat_completion_exception(monkeypatch):
    """Test that create_chat_completion re-raises exceptions from the API with an appropriate error message."""
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy_api_key")
    provider = MistralProvider()

    def fake_create(**kwargs):
        raise Exception("API failure")

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(
        Exception, match="Error creating chat completion with Mistral: API failure"
    ):
        provider.create_chat_completion(messages)
