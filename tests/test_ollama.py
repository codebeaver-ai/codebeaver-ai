import pytest
from codebeaver.models.ollama import OllamaProvider, OllamaModel
import openai
from unittest.mock import patch

def test_valid_model_initialization():
    """Test initialization with a valid model (LLAMA2)."""
    provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
    assert provider.model == OllamaModel.LLAMA2.value
    assert provider.host == "localhost"
    assert provider.port == 11434

def test_invalid_model_initialization():
    """Test initialization with an invalid model should raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OllamaProvider(model="invalid_model")
    assert "Invalid model" in str(exc_info.value)

@patch("openai.ChatCompletion.create")
def test_create_chat_completion_success(mock_create):
    """Test successful create_chat_completion call."""
    # Arrange: set up the mocked response
    expected_response = {"id": "chatcmpl-123", "object": "chat.completion", "choices": []}
    mock_create.return_value = expected_response

    provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
    messages = [{"role": "user", "content": "Hello"}]

    # Act: call create_chat_completion
    response = provider.create_chat_completion(messages, temperature=0.7)

    # Assert: check if returned response equals expected
    assert response == expected_response
    mock_create.assert_called_once_with(model=OllamaModel.LLAMA2.value, messages=messages, temperature=0.7)

@patch("openai.ChatCompletion.create", side_effect=Exception("API error"))
def test_create_chat_completion_failure(mock_create):
    """Test create_chat_completion raises exception on API error."""
    provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(Exception) as exc_info:
        provider.create_chat_completion(messages)
    assert "Error creating chat completion with Ollama" in str(exc_info.value)
    mock_create.assert_called_once()

def test_get_available_models():
    """Test get_available_models returns a list of available models."""
    models = OllamaProvider.get_available_models()
    assert isinstance(models, list)
    # Check that one example model is in the list
    assert OllamaModel.LLAMA2.value in models

def test_get_model_info_known():
    """Test get_model_info returns correct info for a known model."""
    info = OllamaProvider.get_model_info(OllamaModel.LLAMA2.value)
    assert isinstance(info, dict)
    assert "description" in info
    # Check content details
    assert info["type"] == "general"
    assert info["context_window"] == 4096

def test_get_model_info_unknown():
    """Test get_model_info returns the fallback for an unknown model."""
    info = OllamaProvider.get_model_info("non_existent_model")
    assert isinstance(info, dict)
    assert info["description"] == "Model information not available"
    assert info["type"] == "unknown"
    assert info["capabilities"] == ["unknown"]
    assert info["size"] == "Not specified"
    assert info["context_window"] is None
def test_custom_host_port():
    """Test provider initialization with custom host and port, and check openai.api_base configuration."""
    custom_host = "127.0.0.1"
    custom_port = 9999
    provider = OllamaProvider(model=OllamaModel.LLAMA2.value, host=custom_host, port=custom_port)
    expected_api_base = f"http://{custom_host}:{custom_port}/v1"
    assert openai.api_base == expected_api_base

def test_get_model_info_all_models():
    """Test that get_model_info returns a dict with the expected keys for each available model."""
    all_models = OllamaProvider.get_available_models()
    known_info_keys = {"description", "type", "capabilities", "size", "context_window"}
    for model in all_models:
        info = OllamaProvider.get_model_info(model)
        assert isinstance(info, dict)
        # Check that all expected keys exist in the returned dictionary
        assert known_info_keys.issubset(info.keys())
        # If the description is unknown, then type should be unknown as well
        if info["description"] == "Model information not available":
            assert info["type"] == "unknown"
        else:
            assert info["type"] != "unknown"

def test_get_model_info_codellama():
    """Test that get_model_info returns correct info for the CODELLAMA model."""
    info = OllamaProvider.get_model_info(OllamaModel.CODELLAMA.value)
    assert info["description"] == "Specialized code generation model"
    assert info["type"] == "code"
    assert "code generation" in info["capabilities"]
    assert info["context_window"] == 16000
def test_get_model_info_fallback_unknown_model_in_enum():
    """Test that get_model_info returns fallback information for a valid enum model that is not defined in the model_info mapping."""
    # OllamaModel.PHI3_3_8B is not defined in the model_info dict, so fallback should be returned.
    info = OllamaProvider.get_model_info(OllamaModel.PHI3_3_8B.value)
    assert info["description"] == "Model information not available"
    assert info["type"] == "unknown"
    assert info["capabilities"] == ["unknown"]
    assert info["size"] == "Not specified"
    assert info["context_window"] is None

def test_create_chat_completion_with_additional_kwargs():
    """Test that create_chat_completion correctly passes additional keyword arguments to the OpenAI ChatCompletion.create method."""
    with patch("openai.ChatCompletion.create") as mock_create:
        expected_response = {"id": "chatcmpl-456", "object": "chat.completion", "choices": []}
        mock_create.return_value = expected_response

        # Use a model that is in the mapping (FALCON)
        provider = OllamaProvider(model=OllamaModel.FALCON.value)
        messages = [{"role": "user", "content": "Test additional kwargs"}]
        # Provide extra kwargs such as max_tokens and stop sequence that should be forwarded to the API call.
        response = provider.create_chat_completion(messages, max_tokens=50, stop=["\n"])

        assert response == expected_response
        mock_create.assert_called_once_with(model=OllamaModel.FALCON.value, messages=messages, max_tokens=50, stop=["\n"])

def test_openai_api_key_default():
    """Test that initializing OllamaProvider sets openai.api_key to the default value 'ollama'."""
    provider = OllamaProvider(model=OllamaModel.LLAMA2_13B.value)
    assert openai.api_key == "ollama"

def test_multiple_instances_do_not_override_api_base():
    """Test that creating multiple OllamaProvider instances with different hosts and ports updates openai.api_base accordingly."""
    # First instance uses default host and port.
    provider1 = OllamaProvider(model=OllamaModel.LLAMA2_7B.value)
    default_api_base = f"http://localhost:11434/v1"
    assert openai.api_base == default_api_base

    # Create a second instance with different host and port. openai.api_base is global so it will change.
    custom_host = "192.168.1.100"
    custom_port = 8888
    provider2 = OllamaProvider(model=OllamaModel.MISTRAL.value, host=custom_host, port=custom_port)
    new_api_base = f"http://{custom_host}:{custom_port}/v1"
    assert openai.api_base == new_api_base

    # Re-initialize provider1: It will reset the openai.api_base to default.
    provider1 = OllamaProvider(model=OllamaModel.LLAMA2_7B.value)
    assert openai.api_base == default_api_base
@patch("openai.ChatCompletion.create")
def test_create_chat_completion_empty_messages(mock_create):
    """Test create_chat_completion with an empty messages list."""
    expected_response = {"id": "chatcmpl-empty", "object": "chat.completion", "choices": []}
    mock_create.return_value = expected_response
    provider = OllamaProvider(model=OllamaModel.LLAMA2_70B.value)
    response = provider.create_chat_completion([])
    assert response == expected_response
    mock_create.assert_called_once_with(model=OllamaModel.LLAMA2_70B.value, messages=[])

@patch("openai.ChatCompletion.create", return_value=None)
def test_create_chat_completion_none_response(mock_create):
    """Test that create_chat_completion handles a None API response correctly."""
    provider = OllamaProvider(model=OllamaModel.MISTRAL_OPENORCA.value)
    messages = [{"role": "user", "content": "None response test"}]
    response = provider.create_chat_completion(messages)
    assert response is None
    mock_create.assert_called_once_with(model=OllamaModel.MISTRAL_OPENORCA.value, messages=messages)

def test_get_model_info_for_embedding_model():
    """Test that get_model_info returns correct info for embedding models."""
    # Test embedding model: NOMIC_EMBED_TEXT
    info_nomic = OllamaProvider.get_model_info(OllamaModel.NOMIC_EMBED_TEXT.value)
    assert info_nomic["description"] == "Text embedding model"
    assert info_nomic["type"] == "embedding"
    assert info_nomic["capabilities"] == ["text embeddings"]
    assert info_nomic["context_window"] == 8192

    # Test embedding model: MXBAI_EMBED_LARGE
    info_mxbai = OllamaProvider.get_model_info(OllamaModel.MXBAI_EMBED_LARGE.value)
    assert info_mxbai["description"] == "Large embedding model"
    assert info_mxbai["type"] == "embedding"
    assert info_mxbai["capabilities"] == ["text embeddings"]
    assert info_mxbai["context_window"] == 512