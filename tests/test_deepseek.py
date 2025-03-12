import os
import pytest
import openai
from src.codebeaver.models.deepseek import DeepSeekProvider, DeepSeekModel

class TestDeepSeekProvider:
    """Tests for the DeepSeekProvider class."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch):
        """Fixture to set a dummy DEEPSEEK_API_KEY environment variable for tests."""
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key')

    def test_missing_api_key(self, monkeypatch):
        """Test that ValueError is raised when DEEPSEEK_API_KEY is not set."""
        monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
        with pytest.raises(ValueError) as excinfo:
            DeepSeekProvider()
        assert 'DEEPSEEK_API_KEY environment variable not set' in str(excinfo.value)
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key')  # Restore for subsequent tests.

    def test_invalid_model_in_init(self):
        """Test that a ValueError is raised when initialized with an invalid model string."""
        invalid_model = 'invalid-model-name'
        with pytest.raises(ValueError) as excinfo:
            DeepSeekProvider(model=invalid_model)
        assert 'Invalid model' in str(excinfo.value)

    def test_get_available_models(self):
        """Test that get_available_models returns the complete list of models."""
        models = DeepSeekProvider.get_available_models()
        expected_models = [m.value for m in DeepSeekModel]
        assert models == expected_models

    def test_get_model_info_valid(self):
        """Test that get_model_info returns accurate information for a valid model."""
        model_info = DeepSeekProvider.get_model_info(DeepSeekModel.CHAT.value)
        assert 'description' in model_info
        assert model_info['type'] == 'chat'

    def test_get_model_info_invalid(self):
        """Test that get_model_info returns default info for an unknown model."""
        model_info = DeepSeekProvider.get_model_info('non-existent-model')
        assert model_info == {'description': 'Model information not available'}

    def test_create_chat_completion_success(self, monkeypatch):
        """Test that create_chat_completion returns the expected response when OpenAI succeeds."""
        dummy_response = {'choices': [{'message': {'content': 'Hello, test!'}}]}

        def dummy_create(model, messages, **kwargs):
            return dummy_response

        monkeypatch.setattr(openai.ChatCompletion, 'create', dummy_create)
        provider = DeepSeekProvider()
        messages = [{'role': 'user', 'content': 'Test message'}]
        response = provider.create_chat_completion(messages)
        assert response == dummy_response

    def test_create_chat_completion_exception(self, monkeypatch):
        """Test that create_chat_completion raises an exception with a custom message when OpenAI fails."""

        def dummy_create_fail(model, messages, **kwargs):
            raise Exception('dummy error')

        monkeypatch.setattr(openai.ChatCompletion, 'create', dummy_create_fail)
        provider = DeepSeekProvider()
        messages = [{'role': 'user', 'content': 'Test message'}]
        with pytest.raises(Exception) as excinfo:
            provider.create_chat_completion(messages)
        assert 'dummy error' in str(excinfo.value)

    def test_valid_instantiation(self):
        """Test that upon valid instantiation, openai.api_key, openai.api_base, and model are set correctly."""
        provider = DeepSeekProvider(model=DeepSeekModel.CODE.value)
        # Check that the provider model is correctly set
        assert provider.model == DeepSeekModel.CODE.value
        # Check that global OpenAI configurations are set
        assert openai.api_key == 'test_key'
        assert openai.api_base == "https://api.deepseek.com/v1"

    def test_default_model(self):
        """Test that the default model used in DeepSeekProvider is DeepSeekModel.CHAT."""
        provider = DeepSeekProvider()
        assert provider.model == DeepSeekModel.CHAT.value

    def test_get_model_info_for_all_models(self):
        """Test that get_model_info returns correct information for every available model and a fallback for unknown models."""
        available_models = DeepSeekProvider.get_available_models()
        for model in available_models:
            info = DeepSeekProvider.get_model_info(model)
            assert isinstance(info, dict)
            assert 'description' in info
            # Verify the type matches based on the model name
            if model in [DeepSeekModel.CHAT.value, DeepSeekModel.CHAT_INSTRUCT.value]:
                assert info.get('type') == 'chat'
            elif model in [DeepSeekModel.CODE.value, DeepSeekModel.CODE_INSTRUCT.value]:
                assert info.get('type') == 'code'
            elif model in [DeepSeekModel.REASONER.value, DeepSeekModel.REASONER_INSTRUCT.value]:
                assert info.get('type') == 'reasoning'
            elif model in [DeepSeekModel.VISION.value, DeepSeekModel.VISION_INSTRUCT.value]:
                assert info.get('type') == 'vision'

        # Test for a model not present in the defined list
        fallback_info = DeepSeekProvider.get_model_info("non-existent-model")
        assert fallback_info == {"description": "Model information not available"}
    def test_create_chat_completion_forwards_kwargs(self, monkeypatch):
        """Test that extra kwargs are correctly forwarded to the OpenAI API call."""
        def dummy_create(model, messages, **kwargs):
            assert 'temperature' in kwargs and kwargs['temperature'] == 0.5
            return {'choices': [{'message': {'content': 'hello forwarded test'}}]}
        monkeypatch.setattr(openai.ChatCompletion, 'create', dummy_create)
        provider = DeepSeekProvider()
        messages = [{'role': 'user', 'content': 'Test message for forwarded kwargs'}]
        response = provider.create_chat_completion(messages, temperature=0.5)
        assert response == {'choices': [{'message': {'content': 'hello forwarded test'}}]}

    def test_get_model_info_capabilities(self):
        """Test that get_model_info returns the correct capabilities for the CODE_INSTRUCT model."""
        model_info = DeepSeekProvider.get_model_info(DeepSeekModel.CODE_INSTRUCT.value)
        expected_capabilities = ["code generation", "code completion", "code explanation", "instruction following"]
        assert 'capabilities' in model_info
        assert model_info['capabilities'] == expected_capabilities
    def test_create_chat_completion_exception_prefix(self, monkeypatch):
        """Test that create_chat_completion raises an exception with proper prefix when OpenAI fails."""
        def dummy_create_fail(model, messages, **kwargs):
            raise Exception("unexpected failure")
        monkeypatch.setattr(openai.ChatCompletion, 'create', dummy_create_fail)
        provider = DeepSeekProvider()
        messages = [{'role': 'user', 'content': 'Test message'}]
        with pytest.raises(Exception) as excinfo:
            provider.create_chat_completion(messages)
        assert str(excinfo.value).startswith("Error creating chat completion with DeepSeek:" )

    def test_create_chat_completion_empty_messages(self, monkeypatch):
        """Test that create_chat_completion handles an empty messages list correctly."""
        dummy_response = {'choices': [{'message': {'content': 'Empty chat test'}}]}
        def dummy_create(model, messages, **kwargs):
            # Verify that the messages argument is empty
            assert messages == []
            return dummy_response
        monkeypatch.setattr(openai.ChatCompletion, 'create', dummy_create)
        provider = DeepSeekProvider()
        response = provider.create_chat_completion([])
        assert response == dummy_response