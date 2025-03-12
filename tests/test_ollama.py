import pytest
from src.codebeaver.models.ollama import OllamaProvider, OllamaModel
import openai

    
class TestOllamaProvider:
    def test_invalid_model(self):
        """Test that an invalid model in the constructor raises a ValueError."""
        invalid_model = "invalid-model"
        with pytest.raises(ValueError) as exc_info:
            OllamaProvider(model=invalid_model)
        assert "Invalid model" in str(exc_info.value)

    def test_get_available_models(self):
        """Test that get_available_models returns all valid model identifiers."""
        models = OllamaProvider.get_available_models()
        # Verify that some known models are in the returned list
        assert OllamaModel.LLAMA2.value in models
        assert OllamaModel.CODELLAMA.value in models

    def test_get_model_info_existing(self):
        """Test that get_model_info returns correct details for a known model."""
        info = OllamaProvider.get_model_info(OllamaModel.LLAMA2.value)
        assert "description" in info
        assert info["description"] == "Meta's Llama 2 base model"

    def test_get_model_info_non_existent(self):
        """Test that get_model_info returns default information for an unknown model."""
        unknown_model = "non-existent-model"
        info = OllamaProvider.get_model_info(unknown_model)
        assert info["description"] == "Model information not available"
        assert info["type"] == "unknown"

    def test_create_chat_completion_success(self, monkeypatch):
        """Test successful chat completion creation by faking openai.ChatCompletion.create."""

        # Define a dummy response for the chat completion API
        dummy_response = {"id": "dummy", "object": "chat.completion", "choices": []}
        
        def dummy_create(**kwargs):
            return dummy_response
        # Monkey-patch the openai.ChatCompletion.create method with our dummy_create
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)

        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)
        assert response == dummy_response

    def test_create_chat_completion_failure(self, monkeypatch):
        """Test that create_chat_completion properly raises an exception on failure."""

        def failing_create(**kwargs):
            raise Exception("Dummy error")
        monkeypatch.setattr(openai.ChatCompletion, "create", failing_create)

        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception) as exc_info:
            provider.create_chat_completion(messages)
        assert "Error creating chat completion with Ollama" in str(exc_info.value)
    def test_constructor_sets_attributes(self):
        """Test that constructor sets model, host, and port attributes and adjusts openai.api_base."""
        custom_model = OllamaModel.MISTRAL.value
        custom_host = "127.0.0.1"
        custom_port = 12345
        provider = OllamaProvider(model=custom_model, host=custom_host, port=custom_port)
        assert provider.model == custom_model
        assert provider.host == custom_host
        assert provider.port == custom_port
        expected_api_base = f"http://{custom_host}:{custom_port}/v1"
        assert openai.api_base == expected_api_base

    def test_get_model_info_vision(self):
        """Test that get_model_info returns the correct details for a vision model (LLAVA)."""
        info = OllamaProvider.get_model_info(OllamaModel.LLAVA.value)
        assert info["type"] == "vision"
        assert info["description"] == "Vision-language model"
        assert info["context_window"] == 4096

    def test_get_model_info_embedding(self):
        """Test that get_model_info returns correct details for an embedding model (NOMIC_EMBED_TEXT)."""
        info = OllamaProvider.get_model_info(OllamaModel.NOMIC_EMBED_TEXT.value)
        assert info["type"] == "embedding"
        assert info["description"] == "Text embedding model"
        assert info["capabilities"] == ["text embeddings"]
        assert info["context_window"] == 8192
    def test_get_model_info_not_defined_model(self):
        """Test that get_model_info returns default info for a valid enum model not defined in the info dictionary."""
        # OllamaModel.LLAMA3_1_8B is defined in the enum but not in model_info so should return the default
        info = OllamaProvider.get_model_info(OllamaModel.LLAMA3_1_8B.value)
        assert info["description"] == "Model information not available"
        assert info["type"] == "unknown"
        assert info["capabilities"] == ["unknown"]

    def test_create_chat_completion_empty_messages(self, monkeypatch):
        """Test that create_chat_completion returns a valid response even when provided an empty messages list."""
        dummy_response = {"id": "dummy_empty", "object": "chat.completion", "choices": []}
        monkeypatch.setattr(openai.ChatCompletion, "create", lambda **kwargs: dummy_response)
        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        messages = []
        response = provider.create_chat_completion(messages)
        assert response == dummy_response

    def test_create_chat_completion_extra_kwargs(self, monkeypatch):
        """Test that extra keyword arguments are correctly forwarded to openai.ChatCompletion.create."""
        def dummy_create(**kwargs):
            # Validate that temperature is passed as an extra kwarg
            assert kwargs.get("temperature") == 0.7
            return {"id": "dummy_extra", "object": "chat.completion", "choices": []}
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        messages = [{"role": "user", "content": "Hello extra"}]
        response = provider.create_chat_completion(messages, temperature=0.7)
        assert response["id"] == "dummy_extra"
    def test_get_model_info_falcon(self):
        """Test that get_model_info returns correct details for model FALCON."""
        info = OllamaProvider.get_model_info(OllamaModel.FALCON.value)
        assert info["description"] == "Efficient language model"
        assert info["type"] == "general"
        assert info["context_window"] == 2048

    def test_get_model_info_deepseek(self):
        """Test that get_model_info returns correct details for model DEEPSEEK_CODER_33B."""
        info = OllamaProvider.get_model_info(OllamaModel.DEEPSEEK_CODER_33B.value)
        assert info["description"] == "Large code generation model"
        assert info["capabilities"] == ["code generation", "code completion"]
        assert info["size"] == "33B parameters"
        assert info["context_window"] == 16000

    def test_api_key_set(self):
        """Test that the constructor sets openai.api_key to 'ollama'."""
        provider = OllamaProvider(model=OllamaModel.LLAMA2.value)
        assert openai.api_key == "ollama"

    def test_all_available_models_have_info(self):
        """Test that get_model_info returns a dictionary with a description for every available model."""
        models = OllamaProvider.get_available_models()
        for model in models:
            info = OllamaProvider.get_model_info(model)
            assert isinstance(info, dict)
            # Ensure that a description exists even if it's the default message
            assert "description" in info
