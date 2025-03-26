import openai
import pytest

from src.codebeaver.models.ollama import OllamaModel, OllamaProvider


# Dummy response and functions to simulate openai.ChatCompletion behavior
class DummyResponse:
    def __init__(self, content):
        self.content = content


def dummy_success(*args, **kwargs):
    return DummyResponse("success")


def dummy_failure(*args, **kwargs):
    raise Exception("OpenAI API error")


class TestOllamaProvider:
    """Tests for the OllamaProvider class."""

    @pytest.fixture
    def provider(self):
        """Provides an instance of OllamaProvider with the default model."""
        return OllamaProvider()

    def test_valid_model_init(self):
        """Test initialization with a valid model."""
        provider = OllamaProvider(model=OllamaModel.LLAMA2_7B.value)
        assert provider.model == OllamaModel.LLAMA2_7B.value
        assert "localhost" in provider.host

    def test_invalid_model_init(self):
        """Test initializing with an invalid model string raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            OllamaProvider(model="invalid_model")
        assert "Invalid model" in str(excinfo.value)

    def test_get_available_models(self):
        """Test that get_available_models returns all defined models."""
        models = OllamaProvider.get_available_models()
        # Check that a known model is in the list.
        assert OllamaModel.LLAMA2.value in models
        # Check that the list length equals number of enum members.
        assert len(models) == len(list(OllamaModel))

    def test_get_model_info_valid(self):
        """Test that get_model_info returns correct info for a known model."""
        info = OllamaProvider.get_model_info(OllamaModel.LLAMA2.value)
        assert "description" in info
        assert info["type"] == "general"
        assert info["context_window"] == 4096

    def test_get_model_info_unknown(self):
        """Test that get_model_info returns default info for an unknown model."""
        info = OllamaProvider.get_model_info("non_existent_model")
        assert info["description"] == "Model information not available"
        assert info["context_window"] is None

    def test_create_chat_completion_success(self, monkeypatch, provider):
        """Test create_chat_completion successfully returns a dummy response."""
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_success)
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages=messages)
        assert isinstance(response, DummyResponse)
        assert response.content == "success"

    def test_create_chat_completion_failure(self, monkeypatch, provider):
        """Test create_chat_completion raises an exception when openai.ChatCompletion.create fails."""
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_failure)
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception) as excinfo:
            provider.create_chat_completion(messages=messages)
        assert "Error creating chat completion with Ollama" in str(excinfo.value)
