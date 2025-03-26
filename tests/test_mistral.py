import os
from unittest.mock import MagicMock, patch

import openai
import pytest

from src.codebeaver.models.mistral import MistralModel, MistralProvider


def mock_mistral_provider():
    with patch("src.codebeaver.models.mistral.MistralProvider") as mock_provider:
        yield mock_provider


class TestMistralModel:
    @pytest.mark.parametrize(
        "alias, expected",
        [
            ("codestral-latest", "codestral-2501"),
            ("mistral-large-latest", "mistral-large-2411"),
            ("pixtral-large-latest", "pixtral-large-2411"),
            ("mistral-saba-latest", "mistral-saba-2502"),
            ("ministral-3b-latest", "ministral-3b-2410"),
            ("ministral-8b-latest", "ministral-8b-2410"),
            ("mistral-moderation-latest", "mistral-moderation-2411"),
            ("mistral-small-latest", "mistral-small-2501"),
            ("non-aliased-model", "non-aliased-model"),
        ],
    )
    def test_get_base_model(self, alias, expected):
        """Test the get_base_model class method for various aliases and non-aliases."""
        assert MistralModel.get_base_model(alias) == expected


class TestMistralProvider:

    def test_init_with_invalid_model(self, monkeypatch):
        """Test initialization with an invalid model."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        with pytest.raises(ValueError, match="Invalid model"):
            MistralProvider("invalid_model")

    def test_init_without_api_key(self, monkeypatch):
        """Test initialization without an API key set."""
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        with pytest.raises(
            ValueError, match="MISTRAL_API_KEY environment variable not set"
        ):
            MistralProvider()

    def test_create_chat_completion_success(self, monkeypatch):
        """Test successful chat completion creation."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        mock_response = MagicMock()
        monkeypatch.setattr(
            openai.ChatCompletion, "create", lambda **kwargs: mock_response
        )

        provider = MistralProvider()
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)

        assert response == mock_response
        # Note: We can't easily assert the exact call parameters due to the mocking approach

    def test_create_chat_completion_error(self, monkeypatch):
        """Test chat completion creation with an error."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        monkeypatch.setattr(
            openai.ChatCompletion,
            "create",
            lambda **kwargs: (_ for _ in ()).throw(Exception("API Error")),
        )

        provider = MistralProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(
            Exception, match="Error creating chat completion with Mistral: API Error"
        ):
            provider.create_chat_completion(messages)

    def test_get_available_models(self):
        """Test getting available models."""
        models = MistralProvider.get_available_models()
        assert isinstance(models, list)
        assert all(isinstance(model, str) for model in models)
        assert MistralModel.MISTRAL_SMALL.value in models

    def test_get_model_info_valid_model(self):
        """Test getting info for a valid model."""
        info = MistralProvider.get_model_info(MistralModel.MISTRAL_SMALL.value)
        assert isinstance(info, dict)
        assert "description" in info
        assert "max_tokens" in info
        assert "version" in info
        assert "type" in info

    def test_get_model_info_invalid_model(self):
        """Test getting info for an invalid model."""
        info = MistralProvider.get_model_info("invalid_model")
        assert info == {"description": "Model information not available"}

    def test_get_model_info_latest_alias(self):
        """Test getting info for a 'latest' model alias."""
        info_latest = MistralProvider.get_model_info(
            MistralModel.MISTRAL_SMALL_LATEST.value
        )
        info_base = MistralProvider.get_model_info(MistralModel.MISTRAL_SMALL.value)
        assert info_latest == info_base

    def test_create_chat_completion_with_kwargs(self, monkeypatch):
        """Test creating a chat completion with additional kwargs."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        mock_response = MagicMock()
        monkeypatch.setattr(
            openai.ChatCompletion, "create", lambda **kwargs: mock_response
        )

        provider = MistralProvider()
        messages = [{"role": "user", "content": "Hello"}]
        kwargs = {"temperature": 0.7, "max_tokens": 100}
        response = provider.create_chat_completion(messages, **kwargs)

        assert response == mock_response
        # Note: We can't easily assert the exact call parameters due to the mocking approach

    def test_init_with_different_models(self, monkeypatch):
        """Test initialization with different valid models."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        for model in MistralModel:
            provider = MistralProvider(model.value)
            assert provider.model == MistralModel.get_base_model(model.value)

    def test_create_chat_completion_with_all_models(self, monkeypatch):
        """Test creating chat completions with all available models."""
        monkeypatch.setenv("MISTRAL_API_KEY", "dummy_key")
        mock_response = MagicMock()
        monkeypatch.setattr(
            openai.ChatCompletion, "create", lambda **kwargs: mock_response
        )

        messages = [{"role": "user", "content": "Hello"}]
        for model in MistralModel:
            provider = MistralProvider(model.value)
            response = provider.create_chat_completion(messages)
            assert response == mock_response

    def test_api_key_security(self, monkeypatch):
        """Test that the API key is securely handled."""
        test_key = "test_api_key"
        monkeypatch.setenv("MISTRAL_API_KEY", test_key)

        # Create a new MistralProvider instance to pick up the new API key
        provider = MistralProvider()

        # Verify that the API key is set correctly in the openai module
        assert openai.api_key == test_key

        # Ensure the API key is not directly accessible as an attribute
        assert not hasattr(
            provider, "api_key"
        ), "API key should not be directly accessible as a public attribute"

        # Verify that the API key is being used correctly without exposing it
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = MagicMock()
            provider.create_chat_completion([{"role": "user", "content": "Test"}])
            mock_create.assert_called_once()
            # Check that the API key was used in the call, but don't expose it in the assertion
            assert mock_create.call_args[1]["api_key"] == test_key

        # Test that changing the environment variable affects new instances
        new_test_key = "new_test_api_key"
        monkeypatch.setenv("MISTRAL_API_KEY", new_test_key)
        new_provider = MistralProvider()

        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = MagicMock()
            new_provider.create_chat_completion([{"role": "user", "content": "Test"}])
            mock_create.assert_called_once()
            assert mock_create.call_args[1]["api_key"] == new_test_key
