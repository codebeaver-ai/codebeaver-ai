import os
from typing import List, Dict, Any
import openai
from enum import Enum


class ClaudeModel(Enum):
    # Latest models with aliases
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    CLAUDE_3_7_SONNET_LATEST = "claude-3-7-sonnet-latest"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_5_HAIKU_LATEST = "claude-3-5-haiku-latest"
    CLAUDE_3_5_SONNET_V2 = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_SONNET_LATEST = "claude-3-5-sonnet-latest"
    CLAUDE_3_5_SONNET_V1 = "claude-3-5-sonnet-20240620"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_OPUS_LATEST = "claude-3-opus-latest"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class AnthropicProvider:
    def __init__(self, model: str = ClaudeModel.CLAUDE_3_5_SONNET_V2.value):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        openai.api_key = self.api_key
        openai.api_base = "https://api.anthropic.com/v1"
        self.model = model

        # Validate model
        try:
            ClaudeModel(model)
        except ValueError:
            valid_models = [m.value for m in ClaudeModel]
            raise ValueError(
                f"Invalid model: {model}. Valid models are: {valid_models}"
            )

    def create_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        try:
            # Handle extended thinking for Claude 3.7 Sonnet
            if self.model in [
                ClaudeModel.CLAUDE_3_7_SONNET.value,
                ClaudeModel.CLAUDE_3_7_SONNET_LATEST.value,
            ]:
                if kwargs.get("extended_thinking", False):
                    kwargs["headers"] = kwargs.get("headers", {})
                    kwargs["headers"]["output-128k-2025-02-19"] = "true"
                    # Remove extended_thinking from kwargs as it's not a valid parameter for the API
                    kwargs.pop("extended_thinking", None)

            response = openai.ChatCompletion.create(
                model=self.model, messages=messages, **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"Error creating chat completion with Anthropic: {str(e)}")

    @staticmethod
    def get_available_models() -> List[str]:
        """Returns a list of all available Claude models."""
        return [model.value for model in ClaudeModel]

    @staticmethod
    def get_model_info(model: str) -> Dict[str, Any]:
        """Returns information about a specific model."""
        model_info = {
            ClaudeModel.CLAUDE_3_7_SONNET.value: {
                "description": "Our most intelligent model",
                "context_window": 200000,
                "max_tokens_normal": 8192,
                "max_tokens_extended": 64000,
                "supports_extended_thinking": True,
                "cost_input_per_1m": 3.00,
                "cost_output_per_1m": 15.00,
            },
            ClaudeModel.CLAUDE_3_5_HAIKU.value: {
                "description": "Our fastest model",
                "context_window": 200000,
                "max_tokens": 8192,
                "supports_extended_thinking": False,
                "cost_input_per_1m": 0.80,
                "cost_output_per_1m": 4.00,
            },
            ClaudeModel.CLAUDE_3_5_SONNET_V2.value: {
                "description": "High level of intelligence and capability",
                "context_window": 200000,
                "max_tokens": 8192,
                "supports_extended_thinking": False,
                "cost_input_per_1m": 3.00,
                "cost_output_per_1m": 15.00,
            },
            ClaudeModel.CLAUDE_3_OPUS.value: {
                "description": "Powerful model for complex tasks",
                "context_window": 200000,
                "max_tokens": 4096,
                "supports_extended_thinking": False,
                "cost_input_per_1m": 15.00,
                "cost_output_per_1m": 75.00,
            },
            # Add other models with their respective information
        }

        try:
            model_enum = ClaudeModel(model)
            # Handle latest aliases
            if model_enum.name.endswith("_LATEST"):
                # First, find the corresponding non-latest model name
                base_model_name = next(
                    m.value
                    for m in ClaudeModel
                    if not m.name.endswith("_LATEST")
                    and m.value.split("-")[1] == model_enum.value.split("-")[1]
                )
                # Then look up the model info using the base model name
                return model_info.get(
                    base_model_name, {"description": "Latest version of the model"}
                )
            return model_info.get(
                model, {"description": "Model information not available"}
            )
        except ValueError:
            raise ValueError(f"Invalid model: {model}")
