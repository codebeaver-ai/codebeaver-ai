import os
import pytest
from src.codebeaver.models.mistral import MistralProvider, MistralModel
import openai

class TestMistral:
    """Tests for the MistralProvider and MistralModel functionalities."""

    def setup_method(self):
        # Set a dummy API key for tests that require it.
        os.environ["MISTRAL_API_KEY"] = "dummy-api-key"

    def teardown_method(self):
        # Clean up the environment variable.
        if "MISTRAL_API_KEY" in os.environ:
            del os.environ["MISTRAL_API_KEY"]

    def test_missing_api_key(self, monkeypatch):
        """Test that initialization fails if MISTRAL_API_KEY is not set."""
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        with pytest.raises(ValueError, match="MISTRAL_API_KEY environment variable not set"):
            MistralProvider()

    def test_invalid_model(self):
        """Test that providing an invalid model string raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid model: invalid-model"):
            MistralProvider(model="invalid-model")

    def test_create_chat_completion(self, monkeypatch):
        """Test that create_chat_completion returns the dummy response when openai.ChatCompletion.create is mocked."""

        # Prepare a dummy response and a dummy chat completion function.
        dummy_response = {"id": "dummy", "object": "chat.completion", "choices": [{"message": {"role": "assistant", "content": "Hello, world!"}}]}

        def dummy_create(**kwargs):
            return dummy_response

        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)

        provider = MistralProvider(model=MistralModel.MISTRAL_SMALL.value)
        messages = [{"role": "user", "content": "Say hello"}]
        response = provider.create_chat_completion(messages=messages)
        assert response == dummy_response

    def test_get_available_models(self):
        """Test that get_available_models returns exactly all the defined models."""
        available_models = MistralProvider.get_available_models()
        # Compare lengths since the model enum defines all expected models.
        expected_models = [m.value for m in MistralModel]
        assert set(available_models) == set(expected_models)

    def test_get_model_info_valid_and_alias(self):
        """Test that get_model_info returns proper info for a valid model and handles alias mapping properly."""
        # For a known valid model
        model_info_direct = MistralProvider.get_model_info(MistralModel.MISTRAL_SMALL.value)
        assert model_info_direct.get("description") == "Leader in small models category"

        # For the alias version
        model_info_alias = MistralProvider.get_model_info("mistral-small-latest")
        assert model_info_alias == model_info_direct

        # For an unknown model, should return the default message.
        unknown_info = MistralProvider.get_model_info("non-existent-model")
        assert unknown_info.get("description") == "Model information not available"

    def test_get_base_model(self):
        """Test that the get_base_model class method returns the base model for known aliases and defaults otherwise."""
        # Test for a known alias mapping
        base_model = MistralModel.get_base_model("mistral-large-latest")
        assert base_model == MistralModel.MISTRAL_LARGE.value

        # When model is not an alias it should return itself.
        base_model_same = MistralModel.get_base_model("pixtral-12b-2409")
        assert base_model_same == "pixtral-12b-2409"

    def test_create_chat_completion_exception(self, monkeypatch):
        """Test that create_chat_completion properly wraps exceptions when openai.ChatCompletion.create fails."""
        def dummy_create(**kwargs):
            raise Exception("Simulated error")
        monkeypatch.setattr(openai.ChatCompletion, "create", dummy_create)
        provider = MistralProvider(model=MistralModel.MISTRAL_SMALL.value)
        messages = [{"role": "user", "content": "Test"}]
        with pytest.raises(Exception, match="Error creating chat completion with Mistral: Simulated error"):
            provider.create_chat_completion(messages=messages)

    def test_provider_alias_initialization(self):
        """Test that initializing MistralProvider with an alias correctly maps to the base model."""
        provider = MistralProvider(model="mistral-small-latest")
        assert provider.model == MistralModel.MISTRAL_SMALL.value
    def test_provider_properties(self):
        """Test that MistralProvider sets correct API properties on initialization."""
        provider = MistralProvider(model=MistralModel.CODESTRAL.value)
        # Assert that openai.api_key is set correctly
        assert openai.api_key == "dummy-api-key"
        # Assert that openai.api_base is set correctly
        assert openai.api_base == "https://api.mistral.ai/v1"
        # Check that provider.model is set as expected (using alias mapping if needed)
        expected_model = MistralModel.get_base_model(MistralModel.CODESTRAL.value)
        assert provider.model == expected_model

    def test_loop_get_model_info(self):
        """Test get_model_info for all models in MistralModel enum to ensure correct info or fallback."""
        # The model_info in mistral.py defines info for these base keys
        valid_info_keys = {
            "codestral-2501", "mistral-large-2411", "pixtral-large-2411", "mistral-saba-2502",
            "ministral-3b-2410", "ministral-8b-2410", "mistral-embed", "mistral-moderation-2411",
            "mistral-small-2501", "pixtral-12b-2409", "open-mistral-nemo", "open-codestral-mamba"
        }
        for model_enum in MistralModel:
            info = MistralProvider.get_model_info(model_enum.value)
            base_model = MistralModel.get_base_model(model_enum.value)
            if base_model in valid_info_keys:
                # Verify that the info contains all expected keys and is not the fallback message
                assert "description" in info
                assert "max_tokens" in info
                assert "version" in info
                assert "type" in info
                assert info["description"] != "Model information not available"
            else:
                # If the base model is not in our defined info, it should return the fallback message
                assert info.get("description") == "Model information not available"
    def test_get_model_info_alias_mapping_more(self):
        """Test that model info is consistent for alias and direct model mappings for all known aliases."""
        alias_mapping = {
            "codestral-latest": MistralModel.CODESTRAL.value,
            "mistral-large-latest": MistralModel.MISTRAL_LARGE.value,
            "pixtral-large-latest": MistralModel.PIXTRAL_LARGE.value,
            "mistral-saba-latest": MistralModel.MISTRAL_SABA.value,
            "ministral-3b-latest": MistralModel.MINISTRAL_3B.value,
            "ministral-8b-latest": MistralModel.MINISTRAL_8B.value,
            "mistral-moderation-latest": MistralModel.MISTRAL_MODERATION.value,
            "mistral-small-latest": MistralModel.MISTRAL_SMALL.value,
        }
        for alias, base in alias_mapping.items():
            info_alias = MistralProvider.get_model_info(alias)
            info_direct = MistralProvider.get_model_info(base)
            assert info_alias == info_direct, f"Alias mapping for {alias} should equal direct for {base}"

    def test_get_model_info_research_models(self):
        """Test that research models return the correct model information."""
        # Test for open-mistral-nemo
        info_nemo = MistralProvider.get_model_info(MistralModel.MISTRAL_NEMO.value)
        assert info_nemo.get("description") == "Best multilingual open source model"

        # Test for open-codestral-mamba
        info_mamba = MistralProvider.get_model_info(MistralModel.CODESTRAL_MAMBA.value)
        assert info_mamba.get("description") == "First mamba 2 open source model"
# If using pytest execution, no need for an explicit main.