from unittest.mock import MagicMock, patch

import pytest

from src.codebeaver.models.ollama import OllamaModel, OllamaProvider


class TestOllamaProvider:
    @pytest.fixture
    def mock_openai(self):
        with patch("src.codebeaver.models.ollama.openai") as mock:
            yield mock

    def test_init_valid_model(self):
        """Test initialization with a valid model."""
        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        assert provider.model == OllamaModel.LLAMA2.value
        assert provider.host == "localhost"
        assert provider.port == 11434

    def test_init_invalid_model(self):
        """Test initialization with an invalid model."""
        with pytest.raises(ValueError, match="Invalid model"):
            OllamaProvider(model="invalid_model")

    def test_init_custom_host_port(self):
        """Test initialization with custom host and port."""
        provider = OllamaProvider(
            model=OllamaModel.LLAMA2.value, host="example.com", port=8080
        )
        assert provider.host == "example.com"
        assert provider.port == 8080

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_success(self, mock_create):
        """Test successful chat completion creation."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_create.return_value = mock_response

        provider = OllamaProvider()
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)

        assert response.choices[0].message.content == "Test response"
        mock_create.assert_called_once_with(
            model=OllamaModel.LLAMA2.value, messages=messages
        )

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_error(self, mock_create):
        """Test error handling in chat completion creation."""
        mock_create.side_effect = Exception("API Error")

        provider = OllamaProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(
            Exception, match="Error creating chat completion with Ollama: API Error"
        ):
            provider.create_chat_completion(messages)

    def test_get_available_models(self):
        """Test getting available models."""
        models = OllamaProvider.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert OllamaModel.LLAMA2.value in models

    def test_get_model_info_existing(self):
        """Test getting info for an existing model."""
        info = OllamaProvider.get_model_info(OllamaModel.LLAMA2.value)
        assert isinstance(info, dict)
        assert "description" in info
        assert "type" in info
        assert "capabilities" in info
        assert "size" in info
        assert "context_window" in info

    def test_get_model_info_nonexistent(self):
        """Test getting info for a non-existent model."""
        info = OllamaProvider.get_model_info("nonexistent_model")
        assert isinstance(info, dict)
        assert info["description"] == "Model information not available"
        assert info["type"] == "unknown"
        assert info["capabilities"] == ["unknown"]
        assert info["size"] == "Not specified"
        assert info["context_window"] is None

    def test_init_with_all_models(self):
        """Test initialization with all available models."""
        for model in OllamaModel:
            provider = OllamaProvider(model=model.value)
            assert provider.model == model.value

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_with_kwargs(self, mock_create):
        """Test chat completion creation with additional kwargs."""
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        provider = OllamaProvider()
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(
            messages, temperature=0.7, max_tokens=100
        )

        mock_create.assert_called_once_with(
            model=OllamaModel.LLAMA2.value,
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

    def test_get_model_info_all_models(self):
        """Test getting info for all available models."""
        for model in OllamaModel:
            info = OllamaProvider.get_model_info(model.value)
            assert isinstance(info, dict)
            assert all(
                key in info
                for key in [
                    "description",
                    "type",
                    "capabilities",
                    "size",
                    "context_window",
                ]
            )

    def test_init_with_embedding_model(self):
        """Test initialization with an embedding model."""
        provider = OllamaProvider(model=OllamaModel.NOMIC_EMBED_TEXT.value)
        assert provider.model == OllamaModel.NOMIC_EMBED_TEXT.value
        assert provider.get_model_info(provider.model)["type"] == "embedding"

    def test_init_with_code_model(self):
        """Test initialization with a code model."""
        provider = OllamaProvider(model=OllamaModel.CODELLAMA.value)
        assert provider.model == OllamaModel.CODELLAMA.value
        assert provider.get_model_info(provider.model)["type"] == "code"

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_network_error(self, mock_create):
        """Test network error handling in chat completion creation."""
        mock_create.side_effect = ConnectionError("Network Error")

        provider = OllamaProvider()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(
            Exception, match="Error creating chat completion with Ollama: Network Error"
        ):
            provider.create_chat_completion(messages)

    def test_get_model_info_detailed(self):
        """Test getting detailed info for various model types."""
        models_to_test = [
            OllamaModel.LLAMA2.value,
            OllamaModel.CODELLAMA.value,
            OllamaModel.MISTRAL.value,
        ]
        for model in models_to_test:
            info = OllamaProvider.get_model_info(model)
            assert isinstance(info, dict)
            assert info["description"] != "Model information not available"
            assert info["type"] != "unknown"
            assert info["capabilities"] != ["unknown"]
            assert info["size"] != "Not specified"
            assert info["context_window"] is not None

    def test_get_model_info_embedding(self):
        """Test getting info for embedding models."""
        embedding_models = [
            OllamaModel.NOMIC_EMBED_TEXT.value,
            OllamaModel.MXBAI_EMBED_LARGE.value,
        ]
        for model in embedding_models:
            info = OllamaProvider.get_model_info(model)
            assert isinstance(info, dict)
            assert info["description"] != "Model information not available"
            assert info["type"] == "embedding"
            assert "text embeddings" in info["capabilities"]
            # Size might be "Not specified" for embedding models
            assert info["context_window"] is not None

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_with_multiple_messages(self, mock_create):
        """Test chat completion creation with multiple messages."""
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        provider = OllamaProvider()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you?"},
            {"role": "user", "content": "What's the weather like today?"},
        ]
        provider.create_chat_completion(messages)

        mock_create.assert_called_once_with(
            model=OllamaModel.LLAMA2.value, messages=messages
        )

    def test_get_model_info_consistency(self):
        """Test consistency of model info across all models."""
        for model in OllamaModel:
            info = OllamaProvider.get_model_info(model.value)
            assert isinstance(info, dict)
            assert all(
                key in info
                for key in [
                    "description",
                    "type",
                    "capabilities",
                    "size",
                    "context_window",
                ]
            )
            assert isinstance(info["capabilities"], list)
            assert len(info["capabilities"]) > 0

    @patch("src.codebeaver.models.ollama.openai.ChatCompletion.create")
    def test_create_chat_completion_with_streaming(self, mock_create):
        """Test chat completion creation with streaming option."""
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        provider = OllamaProvider()
        messages = [{"role": "user", "content": "Hello"}]
        provider.create_chat_completion(messages, stream=True)

        mock_create.assert_called_once_with(
            model=OllamaModel.LLAMA2.value, messages=messages, stream=True
        )

    def test_init_with_custom_api_base(self):
        """Test initialization with a custom API base URL."""
        custom_host = "api.example.com"
        custom_port = 8080
        provider = OllamaProvider(host=custom_host, port=custom_port)
        assert provider.host == custom_host
        assert provider.port == custom_port
        assert provider.api_key == "ollama"  # Ensure the API key is still set
        assert provider.model == OllamaModel.LLAMA2.value  # Default model
