import os
import pytest
from typing import Any, Dict, List
from codebeaver.models import mistral
import openai

class TestMistralProvider:
    def setup_method(self):
        """Setup a dummy API key for tests"""
        os.environ['MISTRAL_API_KEY'] = 'dummy_api_key'

    def teardown_method(self):
        """Teardown: remove the dummy API key environment variable"""
        if 'MISTRAL_API_KEY' in os.environ:
            del os.environ['MISTRAL_API_KEY']

    def test_missing_api_key(self, monkeypatch):
        """Test that initializing MistralProvider raises an error if API key is missing"""
        monkeypatch.delenv('MISTRAL_API_KEY', raising=False)
        with pytest.raises(ValueError, match="MISTRAL_API_KEY environment variable not set"):
            _ = mistral.MistralProvider()

    def test_invalid_model(self):
        """Test that providing an invalid model raises a ValueError"""
        with pytest.raises(ValueError, match="Invalid model"):
            _ = mistral.MistralProvider(model='non-existing-model')

    def test_get_available_models(self):
        """Test that get_available_models returns all available models from the enum"""
        available = mistral.MistralProvider.get_available_models()
        assert isinstance(available, list)
        enum_models = [m.value for m in mistral.MistralModel]
        assert set(available) == set(enum_models)

    def test_get_model_info_valid(self):
        """Test that get_model_info returns the correct info for a known model"""
        info = mistral.MistralProvider.get_model_info(mistral.MistralModel.MISTRAL_SMALL.value)
        assert 'description' in info
        assert info['description'] == "Leader in small models category"

    def test_get_model_info_invalid(self):
        """Test that get_model_info returns a default message for an unknown model"""
        info = mistral.MistralProvider.get_model_info("unknown-model")
        assert info['description'] == "Model information not available"

    def test_create_chat_completion(self, monkeypatch):
        """Test that create_chat_completion correctly calls openai.ChatCompletion.create and returns the expected response"""
        provider = mistral.MistralProvider()
        messages = [{'role': 'system', 'content': 'Test'}]
        dummy_response = {'id': 'dummy', 'object': 'chat.completion', 'choices': []}

        def dummy_create(*args, **kwargs):
            # Ensure messages are passed correctly.
            assert kwargs.get('messages') == messages
            return dummy_response

        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        response = provider.create_chat_completion(messages)
        assert response == dummy_response

    def test_get_base_model_alias(self):
        """Test that get_base_model correctly resolves the latest alias to its base model"""
        alias = "mistral-small-latest"
        base = mistral.MistralModel.get_base_model(alias)
        assert base == mistral.MistralModel.MISTRAL_SMALL.value
    def test_create_chat_completion_exception(self, monkeypatch):
        """Test that create_chat_completion correctly propagates exceptions from openai.ChatCompletion.create."""
        provider = mistral.MistralProvider()
        messages = [{'role': 'user', 'content': 'Test message'}]
        def dummy_create_raise(*args, **kwargs):
            raise Exception("OpenAI API error")
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create_raise)
        with pytest.raises(Exception, match="Error creating chat completion with Mistral: OpenAI API error"):
            provider.create_chat_completion(messages)

    def test_provider_alias_resolution(self):
        """Test that initializing MistralProvider with a latest alias sets the model to its base model."""
        provider = mistral.MistralProvider(model='mistral-small-latest')
        assert provider.model == mistral.MistralModel.MISTRAL_SMALL.value

    def test_get_model_info_alias(self):
        """Test that get_model_info correctly resolves a model alias to its base model and returns correct model info."""
        info = mistral.MistralProvider.get_model_info("mistral-small-latest")
        expected_info = {
            "description": "Leader in small models category",
            "max_tokens": 32000,
            "version": "25.01",
            "type": "free",
        }
        assert info == expected_info

    def test_get_base_model_non_alias(self):
        """Test that get_base_model returns the model itself if it is not an alias."""
        model_str = "mistral-large-2411"
        base = mistral.MistralModel.get_base_model(model_str)
        assert base == model_str
    def test_create_chat_completion_with_additional_kwargs(self, monkeypatch):
        """Test that additional kwargs are passed through to openai.ChatCompletion.create."""
        provider = mistral.MistralProvider()
        messages = [{'role': 'user', 'content': 'Hello'}]
        expected_response = {'id': 'test123', 'object': 'chat.completion', 'choices': [{'message': {'role': 'assistant', 'content': 'Hi'}}]}

        def dummy_create(*args, **kwargs):
            # Ensure the extra keyword argument 'temperature' is present and correct.
            assert kwargs.get('temperature') == 0.7
            return expected_response

        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        response = provider.create_chat_completion(messages, temperature=0.7)
        assert response == expected_response

    def test_api_base_set_in_provider(self):
        """Test that initializing MistralProvider sets openai.api_base correctly."""
        provider = mistral.MistralProvider()
        assert openai.api_base == "https://api.mistral.ai/v1"

    def test_get_model_info_research(self):
        """Test that get_model_info returns correct info for a research model."""
        info = mistral.MistralProvider.get_model_info(mistral.MistralModel.MISTRAL_NEMO.value)
        expected_info = {
            "description": "Best multilingual open source model",
            "max_tokens": 131000,
            "version": "24.07",
            "type": "research",
        }
        assert info == expected_info

    def test_get_model_info_alias_codestral(self):
        """Test that get_model_info correctly resolves the 'codestral-latest' alias to its base model info."""
        info = mistral.MistralProvider.get_model_info("codestral-latest")
        expected_info = {
            "description": "Cutting-edge language model for coding",
            "max_tokens": 256000,
            "version": "25.01",
            "type": "premier",
        }
        assert info == expected_info
    def test_api_key_set_correctly(self):
        """Test that the provider and openai.api_key are properly set using the environment variable."""
        provider = mistral.MistralProvider()
        # Check that provider.api_key equals the dummy API key defined in setup_method
        assert provider.api_key == 'dummy_api_key'
        # Confirm that openai.api_key is also set to the dummy API key
        assert openai.api_key == 'dummy_api_key'

    def test_provider_alias_resolution_moderation(self):
        """Test that initializing MistralProvider with 'mistral-moderation-latest' resolves to its base model."""
        provider = mistral.MistralProvider(model='mistral-moderation-latest')
        # The base model for 'mistral-moderation-latest' should be mistral-moderation-2411
        assert provider.model == mistral.MistralModel.MISTRAL_MODERATION.value

    def test_get_model_info_alias_pixtral_large(self):
        """Test that get_model_info correctly resolves the 'pixtral-large-latest' alias to its base model info."""
        info = mistral.MistralProvider.get_model_info("pixtral-large-latest")
        expected_info = {
            "description": "Frontier-class multimodal model",
            "max_tokens": 131000,
            "version": "24.11",
            "type": "premier",
        }
        assert info == expected_info