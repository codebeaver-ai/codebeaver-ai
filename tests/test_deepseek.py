import os
import pytest
from codebeaver.models.deepseek import DeepSeekProvider, DeepSeekModel
import openai

class DummyResponse:
    """Dummy response for testing."""
    def __init__(self, data):
        self.data = data

    def __eq__(self, other):
        return isinstance(other, DummyResponse) and self.data == other.data

def dummy_chat_completion_create(model, messages, **kwargs):
    """Dummy function to simulate successful openai.ChatCompletion.create."""
    return DummyResponse({"model": model, "messages": messages, "extra": kwargs})

def dummy_chat_completion_create_error(*args, **kwargs):
    """Dummy function to simulate error in openai.ChatCompletion.create."""
    raise Exception("Simulated error")

def test_missing_api_key(monkeypatch):
    """Test that initializing DeepSeekProvider without an API key raises ValueError."""
    # Ensure the environment variable is not set.
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY environment variable not set"):
        DeepSeekProvider()

def test_valid_api_key(monkeypatch):
    """Test that DeepSeekProvider initializes correctly with a valid API key."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_api_key")
    provider = DeepSeekProvider()
    assert provider.api_key == "test_api_key"
    assert provider.model == DeepSeekModel.CHAT.value

def test_invalid_model(monkeypatch):
    """Test that initializing DeepSeekProvider with an invalid model raises ValueError."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_api_key")
    with pytest.raises(ValueError, match="Invalid model: invalid-model"):
        DeepSeekProvider(model="invalid-model")

def test_get_available_models():
    """Test that get_available_models returns all valid DeepSeek models."""
    models = DeepSeekProvider.get_available_models()
    expected = [m.value for m in DeepSeekModel]
    assert set(models) == set(expected)

def test_get_model_info_valid():
    """Test that get_model_info returns correct information for a valid model."""
    info = DeepSeekProvider.get_model_info(DeepSeekModel.CHAT.value)
    assert "description" in info
    assert info["type"] == "chat"

def test_get_model_info_invalid():
    """Test that get_model_info returns default info for an unknown model."""
    info = DeepSeekProvider.get_model_info("unknown-model")
    assert info["description"] == "Model information not available"

def test_create_chat_completion_success(monkeypatch):
    """Test that create_chat_completion returns a proper response on success."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_api_key")
    # patch the openai.ChatCompletion.create with our dummy function that simulates success.
    monkeypatch.setattr(openai.ChatCompletion, "create", dummy_chat_completion_create)
    provider = DeepSeekProvider()
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.create_chat_completion(messages, temperature=0.5)
    assert isinstance(response, DummyResponse)
    assert response.data["model"] == provider.model
    assert response.data["messages"] == messages
    assert response.data["extra"]["temperature"] == 0.5

def test_create_chat_completion_error(monkeypatch):
    """Test that create_chat_completion properly handles errors from openai.ChatCompletion.create."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_api_key")
    # patch the openai.ChatCompletion.create with our dummy function that simulates an error.
    monkeypatch.setattr(openai.ChatCompletion, "create", dummy_chat_completion_create_error)
    provider = DeepSeekProvider()
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(Exception, match="Error creating chat completion with DeepSeek: Simulated error"):
        provider.create_chat_completion(messages)