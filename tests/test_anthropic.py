import os

import pytest

from codebeaver.models.anthropic import AnthropicProvider, ClaudeModel

# Dummy response to simulate successful calls to the API.
DUMMY_RESPONSE = {"id": "dummy", "object": "chat.completion", "choices": []}


class DummyChatCompletion:
    """A dummy class to simulate openai.ChatCompletion.create calls."""

    @staticmethod
    def create(*args, **kwargs):
        return DUMMY_RESPONSE


class DummyChatCompletionCapture:
    """A dummy class to capture kwargs for testing extended thinking header injection."""

    def __init__(self):
        self.called_kwargs = None

    def create(self, *args, **kwargs):
        self.called_kwargs = kwargs
        return DUMMY_RESPONSE


def dummy_failure_create(*args, **kwargs):
    raise Exception("Simulated API failure")


def test_constructor_valid(monkeypatch):
    """Test that the provider initializes correctly when API key is set and valid model is provided."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    provider = AnthropicProvider()  # uses default model
    assert provider.api_key == "dummy_key"
    # Ensure the model attribute is set to the default ClaudeModel
    assert provider.model == ClaudeModel.CLAUDE_3_5_SONNET_V2.value


def test_constructor_invalid_model(monkeypatch):
    """Test that the provider initialization fails with an invalid model string."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    with pytest.raises(ValueError) as excinfo:
        AnthropicProvider(model="invalid-model")
    assert "Invalid model" in str(excinfo.value)


def test_missing_api_key(monkeypatch):
    """Test that missing the API key in the environment results in a ValueError."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        AnthropicProvider()
    assert "ANTHROPIC_API_KEY environment variable not set" in str(excinfo.value)


def test_create_chat_completion_success(monkeypatch):
    """Test that create_chat_completion returns the dummy response on success."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    monkeypatch.setattr(
        "codebeaver.models.anthropic.openai.ChatCompletion", DummyChatCompletion
    )
    provider = AnthropicProvider(model=ClaudeModel.CLAUDE_3_5_SONNET_V2.value)
    messages = [{"role": "user", "content": "Hello"}]
    response = provider.create_chat_completion(messages)
    assert response == DUMMY_RESPONSE


def test_create_chat_completion_extended_header(monkeypatch):
    """Test that when extended_thinking is True for Claude 3.7 Sonnet models, the header is injected."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    # Use extended thinking compatible model
    provider = AnthropicProvider(model=ClaudeModel.CLAUDE_3_7_SONNET.value)
    capture = DummyChatCompletionCapture()
    monkeypatch.setattr("codebeaver.models.anthropic.openai.ChatCompletion", capture)
    messages = [{"role": "user", "content": "Think deeply"}]
    # Pass extra parameter extended_thinking=True
    response = provider.create_chat_completion(messages, extended_thinking=True)
    # Check that the header was added and extended_thinking removed from kwargs
    assert response == DUMMY_RESPONSE
    headers = capture.called_kwargs.get("headers")
    assert headers is not None
    assert headers.get("output-128k-2025-02-19") == "true"


def test_create_chat_completion_failure(monkeypatch):
    """Test that create_chat_completion raises an exception if openai.ChatCompletion.create fails."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    monkeypatch.setattr(
        "codebeaver.models.anthropic.openai.ChatCompletion",
        type("Dummy", (), {"create": staticmethod(dummy_failure_create)}),
    )
    provider = AnthropicProvider()
    messages = [{"role": "user", "content": "Cause failure"}]
    with pytest.raises(Exception) as excinfo:
        provider.create_chat_completion(messages)
    assert "Simulated API failure" in str(excinfo.value)


def test_get_available_models(monkeypatch):
    """Test that get_available_models returns a list of valid model strings."""
    available = AnthropicProvider.get_available_models()
    # Ensure that the list is not empty and contains known model values.
    assert isinstance(available, list)
    assert ClaudeModel.CLAUDE_3_5_SONNET_V2.value in available


def test_get_model_info_normal():
    """Test that get_model_info returns the right information for a normal model."""
    info = AnthropicProvider.get_model_info(ClaudeModel.CLAUDE_3_5_SONNET_V2.value)
    # Check some keys expected for this model
    assert "description" in info
    assert info.get("cost_input_per_1m") == 3.00


def test_get_model_info_latest():
    """Test that get_model_info returns the correct info for a latest alias by resolving to the base model."""
    # Use a latest alias model which ends with _LATEST
    latest = ClaudeModel.CLAUDE_3_7_SONNET_LATEST.value
    info = AnthropicProvider.get_model_info(latest)
    # The base model for claude-3-7-sonnet should be claude-3-7-sonnet-20250219 which is in our model_info dict.
    assert info.get("description") == "Our most intelligent model"


def test_get_model_info_invalid():
    """Test that get_model_info raises a ValueError for an invalid model name."""
    with pytest.raises(ValueError) as excinfo:
        AnthropicProvider.get_model_info("non-existent-model")
    assert "Invalid model" in str(excinfo.value)
