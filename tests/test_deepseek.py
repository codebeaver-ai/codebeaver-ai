from unittest.mock import MagicMock, patch

import pytest

from src.codebeaver.models.deepseek import DeepSeekModel, DeepSeekProvider


@pytest.fixture
def mock_openai():
    with patch("src.codebeaver.models.deepseek.openai") as mock:
        yield mock


@pytest.fixture
def mock_os_getenv():
    with patch("src.codebeaver.models.deepseek.os.getenv") as mock:
        yield mock


class TestDeepSeekProvider:

    def test_init_with_valid_api_key(self, mock_os_getenv):
        """Test initialization with a valid API key."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider()
        assert provider.api_key == "test_api_key"
        assert provider.model == DeepSeekModel.CHAT.value

    def test_init_missing_api_key(self, mock_os_getenv):
        """Test initialization with a missing API key."""
        mock_os_getenv.return_value = None
        with pytest.raises(
            ValueError, match="DEEPSEEK_API_KEY environment variable not set"
        ):
            DeepSeekProvider()

    def test_init_invalid_model(self, mock_os_getenv):
        """Test initialization with an invalid model."""
        mock_os_getenv.return_value = "test_api_key"
        with pytest.raises(ValueError, match="Invalid model"):
            DeepSeekProvider(model="invalid_model")

    def test_create_chat_completion_success(self, mock_openai, mock_os_getenv):
        """Test successful chat completion creation."""
        mock_os_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_openai.ChatCompletion.create.return_value = mock_response

        provider = DeepSeekProvider()
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)

        assert response == mock_response
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model=DeepSeekModel.CHAT.value, messages=messages
        )

    def test_create_chat_completion_error(self, mock_openai, mock_os_getenv):
        """Test chat completion creation with API error."""
        mock_os_getenv.return_value = "test_api_key"
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")

        provider = DeepSeekProvider()
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(
            Exception, match="Error creating chat completion with DeepSeek: API Error"
        ):
            provider.create_chat_completion(messages)

    def test_get_available_models(self):
        """Test getting available models."""
        models = DeepSeekProvider.get_available_models()
        assert isinstance(models, list)
        assert len(models) == len(DeepSeekModel)
        assert all(isinstance(model, str) for model in models)

    def test_get_model_info_existing(self):
        """Test getting info for an existing model."""
        info = DeepSeekProvider.get_model_info(DeepSeekModel.CHAT.value)
        assert isinstance(info, dict)
        assert "description" in info
        assert "max_tokens" in info
        assert "type" in info
        assert "capabilities" in info

    def test_get_model_info_non_existing(self):
        """Test getting info for a non-existing model."""
        info = DeepSeekProvider.get_model_info("non_existing_model")
        assert info == {"description": "Model information not available"}

    @pytest.mark.parametrize("model", [model.value for model in DeepSeekModel])
    def test_init_with_all_models(self, mock_os_getenv, model):
        """Test initialization with all available DeepSeek models."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider(model=model)
        assert provider.model == model

    def test_create_chat_completion_with_kwargs(self, mock_openai, mock_os_getenv):
        """Test chat completion creation with additional kwargs."""
        mock_os_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_openai.ChatCompletion.create.return_value = mock_response

        provider = DeepSeekProvider()
        messages = [{"role": "user", "content": "Hello"}]
        kwargs = {"temperature": 0.7, "max_tokens": 100}
        response = provider.create_chat_completion(messages, **kwargs)

        assert response == mock_response
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model=DeepSeekModel.CHAT.value,
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

    @pytest.mark.parametrize("model", [model.value for model in DeepSeekModel])
    def test_get_model_info_for_all_models(self, model):
        """Test getting info for all available DeepSeek models."""
        info = DeepSeekProvider.get_model_info(model)
        assert isinstance(info, dict)
        assert "description" in info
        assert "max_tokens" in info
        assert "type" in info
        assert "capabilities" in info
        assert isinstance(info["capabilities"], list)
        assert len(info["capabilities"]) > 0

    def test_api_base_url_setting(self, mock_openai, mock_os_getenv):
        """Test that the API base URL is set correctly."""
        mock_os_getenv.return_value = "test_api_key"
        DeepSeekProvider()
        assert mock_openai.api_base == "https://api.deepseek.com/v1"

    @pytest.mark.parametrize("model", [model.value for model in DeepSeekModel])
    def test_create_chat_completion_with_all_models(
        self, mock_openai, mock_os_getenv, model
    ):
        """Test chat completion creation with all available DeepSeek models."""
        mock_os_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_openai.ChatCompletion.create.return_value = mock_response

        provider = DeepSeekProvider(model=model)
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)

        assert response == mock_response
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model=model, messages=messages
        )

    def test_create_chat_completion_with_empty_messages(
        self, mock_openai, mock_os_getenv
    ):
        """Test chat completion creation with empty messages list."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider()
        with pytest.raises(
            Exception, match="Error creating chat completion with DeepSeek"
        ):
            provider.create_chat_completion([])

    def test_create_chat_completion_with_invalid_message_format(
        self, mock_openai, mock_os_getenv
    ):
        """Test chat completion creation with invalid message format."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider()
        invalid_messages = [{"invalid_key": "content"}]
        with pytest.raises(
            Exception, match="Error creating chat completion with DeepSeek"
        ):
            provider.create_chat_completion(invalid_messages)

    @pytest.mark.parametrize("model", [model.value for model in DeepSeekModel])
    def test_model_info_consistency(self, model):
        """Test consistency of model information across all models."""
        info = DeepSeekProvider.get_model_info(model)
        assert isinstance(info, dict)
        assert "description" in info and isinstance(info["description"], str)
        assert "max_tokens" in info and isinstance(info["max_tokens"], int)
        assert "type" in info and isinstance(info["type"], str)
        assert "capabilities" in info and isinstance(info["capabilities"], list)
        assert all(isinstance(cap, str) for cap in info["capabilities"])

    def test_get_model_info_case_insensitivity(self):
        """Test that get_model_info is case-insensitive."""
        lower_case_info = DeepSeekProvider.get_model_info("deepseek-chat")
        upper_case_info = DeepSeekProvider.get_model_info("DEEPSEEK-CHAT")
        assert lower_case_info == upper_case_info

    def test_create_chat_completion_with_large_input(self, mock_openai, mock_os_getenv):
        """Test chat completion creation with a large input."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider()
        large_content = "A" * 10000  # 10,000 character string
        messages = [{"role": "user", "content": large_content}]
        mock_openai.ChatCompletion.create.return_value = MagicMock()
        response = provider.create_chat_completion(messages)
        assert response is not None
        mock_openai.ChatCompletion.create.assert_called_once()

    def test_create_chat_completion_retry_on_timeout(self, mock_openai, mock_os_getenv):
        """Test chat completion creation with retry on timeout."""
        mock_os_getenv.return_value = "test_api_key"
        provider = DeepSeekProvider()
        messages = [{"role": "user", "content": "Hello"}]
        mock_openai.ChatCompletion.create.side_effect = [
            Exception("Timeout"),
            MagicMock(),
        ]
        response = provider.create_chat_completion(messages)
        assert response is not None
        assert mock_openai.ChatCompletion.create.call_count == 2
