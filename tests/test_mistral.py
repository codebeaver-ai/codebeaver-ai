import os

import openai
import pytest

from codebeaver.models import mistral


@pytest.fixture(autouse=True)
def set_api_key_env(monkeypatch):
    """
    Fixture to set a dummy MISTRAL_API_KEY to ensure tests that require it pass.
    """
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")


class TestMistralProvider:
    """Tests for the MistralProvider and MistralModel classes."""

    def test_get_base_model_alias(self):
        """Test that get_base_model returns the correct base model for alias keys."""
        alias = "mistral-small-latest"
        expected = mistral.MistralModel.MISTRAL_SMALL.value
        result = mistral.MistralModel.get_base_model(alias)
        assert result == expected, "Alias translation failed."

    def test_get_base_model_non_alias(self):
        """Test that get_base_model returns the same string for non-alias models."""
        non_alias = "mistral-large-2411"
        result = mistral.MistralModel.get_base_model(non_alias)
        assert result == non_alias, "Non-alias model should return itself."

    def test_invalid_model_raises_error(self):
        """Test creating a provider with an invalid model raises a ValueError."""
        with pytest.raises(ValueError) as excinfo:
            mistral.MistralProvider(model="invalid-model")
        assert "Invalid model" in str(excinfo.value)

    def test_missing_api_key_raises_error(self, monkeypatch):
        """Test that missing MISTRAL_API_KEY environment variable raises ValueError."""
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        with pytest.raises(ValueError) as excinfo:
            mistral.MistralProvider()
        assert "MISTRAL_API_KEY environment variable not set" in str(excinfo.value)

    def test_create_chat_completion_success(self, monkeypatch):
        """Test successful chat completion creation using a dummy openai.ChatCompletion.create response."""

        dummy_response = {"dummy_key": "dummy_value"}

        def dummy_create(*args, **kwargs):
            return dummy_response

        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        provider = mistral.MistralProvider(model="mistral-small-latest")
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)
        assert (
            response == dummy_response
        ), "Chat completion response did not match expected dummy response."

    def test_create_chat_completion_exception(self, monkeypatch):
        """Test that an exception in openai.ChatCompletion.create is properly handled."""

        def dummy_create(*args, **kwargs):
            raise Exception("API failure")

        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        provider = mistral.MistralProvider(model="mistral-small-latest")
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception) as excinfo:
            provider.create_chat_completion(messages)
        assert "Error creating chat completion with Mistral" in str(excinfo.value)

    def test_get_available_models(self):
        """Test that get_available_models returns a list of all available Mistral models."""
        available_models = mistral.MistralProvider.get_available_models()
        expected_model = mistral.MistralModel.MISTRAL_SMALL.value
        assert (
            expected_model in available_models
        ), "Expected model not in available models."
        assert isinstance(available_models, list)

    def test_get_model_info_valid(self):
        """Test that get_model_info returns correct information for a valid model alias."""
        model_info = mistral.MistralProvider.get_model_info("mistral-small-latest")
        assert "description" in model_info, "Model info should contain a description."
        assert model_info["type"] == "free", "Model type mismatch for mistral-small."

    def test_get_model_info_invalid(self):
        """Test that get_model_info returns a default message for an invalid model."""
        model_info = mistral.MistralProvider.get_model_info("non-existent-model")
        assert (
            model_info["description"] == "Model information not available"
        ), "Should return default info for unknown model."
