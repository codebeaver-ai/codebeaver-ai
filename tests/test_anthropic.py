from unittest.mock import MagicMock, patch

import pytest

from src.codebeaver.models.anthropic import AnthropicProvider, ClaudeModel


class TestAnthropicProvider:
    @pytest.fixture
    def mock_env(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"}):
            yield

    @pytest.fixture
    def provider(self, mock_env):
        return AnthropicProvider()

    def test_init_default_model(self, mock_env):
        """Test initialization with default model"""
        provider = AnthropicProvider()
        assert provider.model == ClaudeModel.CLAUDE_3_5_SONNET_V2.value
        assert provider.api_key == "test_key"

    def test_init_custom_model(self, mock_env):
        """Test initialization with custom model"""
        provider = AnthropicProvider(model=ClaudeModel.CLAUDE_3_OPUS.value)
        assert provider.model == ClaudeModel.CLAUDE_3_OPUS.value

    def test_init_invalid_model(self, mock_env):
        """Test initialization with invalid model"""
        with pytest.raises(ValueError, match="Invalid model"):
            AnthropicProvider(model="invalid_model")

    def test_init_missing_api_key(self):
        """Test initialization with missing API key"""
        with patch.dict("os.environ", clear=True):
            with pytest.raises(
                ValueError, match="ANTHROPIC_API_KEY environment variable not set"
            ):
                AnthropicProvider()

    @patch("openai.ChatCompletion.create")
    def test_create_chat_completion(self, mock_create, provider):
        """Test create_chat_completion method"""
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages)

        mock_create.assert_called_once_with(model=provider.model, messages=messages)
        assert response == mock_response

    @patch("openai.ChatCompletion.create")
    def test_create_chat_completion_extended_thinking(self, mock_create, mock_env):
        """Test create_chat_completion method with extended thinking"""
        provider = AnthropicProvider(model=ClaudeModel.CLAUDE_3_7_SONNET.value)
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages, extended_thinking=True)

        mock_create.assert_called_once_with(
            model=provider.model,
            messages=messages,
            headers={"output-128k-2025-02-19": "true"},
        )
        assert response == mock_response

        # Test with CLAUDE_3_7_SONNET_LATEST
        provider_latest = AnthropicProvider(
            model=ClaudeModel.CLAUDE_3_7_SONNET_LATEST.value
        )
        response_latest = provider_latest.create_chat_completion(
            messages, extended_thinking=True
        )

        mock_create.assert_called_with(
            model=provider_latest.model,
            messages=messages,
            headers={"output-128k-2025-02-19": "true"},
        )
        assert response_latest == mock_response
        models = AnthropicProvider.get_available_models()

    @patch("openai.ChatCompletion.create")
    def test_create_chat_completion_error(self, mock_create, provider):
        """Test error handling in create_chat_completion method"""
        mock_create.side_effect = Exception("API Error")
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(
            Exception, match="Error creating chat completion with Anthropic: API Error"
        ):
            provider.create_chat_completion(messages)

    def test_get_available_models_comprehensive(self):
        """Test get_available_models method comprehensively"""
        models = AnthropicProvider.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(model, str) for model in models)
        # Check for specific models
        assert ClaudeModel.CLAUDE_3_7_SONNET.value in models
        assert ClaudeModel.CLAUDE_3_5_HAIKU.value in models
        assert ClaudeModel.CLAUDE_3_OPUS.value in models
        # Check for latest aliases
        assert ClaudeModel.CLAUDE_3_7_SONNET_LATEST.value in models
        assert ClaudeModel.CLAUDE_3_5_HAIKU_LATEST.value in models
        assert ClaudeModel.CLAUDE_3_OPUS_LATEST.value in models

    def test_get_model_info_comprehensive(self):
        """Test get_model_info method for various models"""
        # Test CLAUDE_3_7_SONNET
        info_3_7 = AnthropicProvider.get_model_info(ClaudeModel.CLAUDE_3_7_SONNET.value)
        assert info_3_7["description"] == "Our most intelligent model"
        assert info_3_7["context_window"] == 200000
        assert info_3_7["max_tokens_normal"] == 8192
        assert info_3_7["max_tokens_extended"] == 64000
        assert info_3_7["supports_extended_thinking"] is True
        assert info_3_7["cost_input_per_1m"] == 3.00
        assert info_3_7["cost_output_per_1m"] == 15.00

        # Test CLAUDE_3_5_HAIKU
        info_3_5_haiku = AnthropicProvider.get_model_info(
            ClaudeModel.CLAUDE_3_5_HAIKU.value
        )
        assert info_3_5_haiku["description"] == "Our fastest model"
        assert info_3_5_haiku["context_window"] == 200000
        assert info_3_5_haiku["max_tokens"] == 8192
        assert info_3_5_haiku["supports_extended_thinking"] is False
        assert info_3_5_haiku["cost_input_per_1m"] == 0.80
        assert info_3_5_haiku["cost_output_per_1m"] == 4.00

        # Test CLAUDE_3_OPUS_LATEST (alias)
        info_opus_latest = AnthropicProvider.get_model_info(
            ClaudeModel.CLAUDE_3_OPUS_LATEST.value
        )
        assert "description" in info_opus_latest
        assert info_opus_latest["context_window"] == 200000
        assert info_opus_latest["max_tokens"] == 4096
        assert info_opus_latest["supports_extended_thinking"] is False
        assert info_opus_latest["cost_input_per_1m"] == 15.00
        assert info_opus_latest["cost_output_per_1m"] == 75.00

    @patch("openai.ChatCompletion.create")
    def test_create_chat_completion_no_extended_thinking(self, mock_create, mock_env):
        """Test create_chat_completion method with extended thinking for unsupported model"""
        provider = AnthropicProvider(model=ClaudeModel.CLAUDE_3_5_HAIKU.value)
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        response = provider.create_chat_completion(messages, extended_thinking=True)

        mock_create.assert_called_once_with(model=provider.model, messages=messages)
        assert response == mock_response
        assert "headers" not in mock_create.call_args[1]
        assert isinstance(models, list)
        assert all(isinstance(model, str) for model in models)
        assert ClaudeModel.CLAUDE_3_7_SONNET.value in models

    def test_get_model_info(self):
        """Test get_model_info static method"""
        info = AnthropicProvider.get_model_info(ClaudeModel.CLAUDE_3_7_SONNET.value)
        assert isinstance(info, dict)
        assert "description" in info
        assert "context_window" in info
        assert "max_tokens_normal" in info
        assert "max_tokens_extended" in info
        assert "supports_extended_thinking" in info
        assert "cost_input_per_1m" in info
        assert "cost_output_per_1m" in info

    def test_get_model_info_latest(self):
        """Test get_model_info static method with latest model alias"""
        info = AnthropicProvider.get_model_info(
            ClaudeModel.CLAUDE_3_7_SONNET_LATEST.value
        )
        assert isinstance(info, dict)
        assert "description" in info

    def test_get_model_info_invalid_model(self):
        """Test get_model_info static method with invalid model"""
        with pytest.raises(ValueError, match="Invalid model"):
            AnthropicProvider.get_model_info("invalid_model")
