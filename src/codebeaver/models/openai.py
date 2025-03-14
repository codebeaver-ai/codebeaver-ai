import os
from typing import List, Dict, Any
import openai
from enum import Enum


class GPTModel(Enum):
    # GPT-4 Series
    GPT4 = "gpt-4"
    GPT4_ALIAS_1 = "4"
    GPT4_ALIAS_2 = "gpt4"

    GPT4_32K = "gpt-4-32k"

    GPT4_TURBO = "gpt-4-turbo"
    GPT4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GPT4_TURBO_ALIAS_1 = "4-turbo"
    GPT4_TURBO_ALIAS_2 = "4t"

    GPT4_5_PREVIEW = "gpt-4.5-preview"

    GPT4_OPTIMIZED = "gpt-4o"
    GPT4_OPTIMIZED_MINI = "gpt-4o-mini"

    O3_MINI = "o3-mini"

    @classmethod
    def get_base_model(cls, model: str) -> str:
        """Get the base model for any alias."""
        alias_mapping = {
            "4": cls.GPT4.value,
            "gpt4": cls.GPT4.value,
            "4-turbo": cls.GPT4_TURBO.value,
            "4t": cls.GPT4_TURBO.value,
            "gpt-4-turbo-preview": cls.GPT4_TURBO.value,
            "o3-mini": cls.O3_MINI.value,
        }
        return alias_mapping.get(model, model)


class OpenAIProvider:
    def __init__(self, model: str = GPTModel.O3_MINI.value):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        openai.api_key = self.api_key
        self.model = GPTModel.get_base_model(model)

        # Validate model
        try:
            # Check if the model is a valid enum value or alias
            if not any(self.model == m.value for m in GPTModel):
                valid_models = [m.value for m in GPTModel]
                raise ValueError(
                    f"Invalid model: {model}. Valid models are: {valid_models}"
                )
        except ValueError as e:
            raise ValueError(str(e))

    def create_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        try:
            response = openai.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"Error creating chat completion with OpenAI: {str(e)}")

    @staticmethod
    def get_available_models() -> List[str]:
        """Returns a list of all available GPT models."""
        return [model.value for model in GPTModel]

    @staticmethod
    def get_model_info(model: str) -> Dict[str, Any]:
        """Returns information about a specific model."""
        model_info = {
            GPTModel.GPT4.value: {
                "description": "Most capable GPT-4 model for general use",
                "context_window": 8192,
                "training_cutoff": "2023-04",
                "cost_input_per_1k": 0.03,
                "cost_output_per_1k": 0.06,
            },
            GPTModel.GPT4_32K.value: {
                "description": "GPT-4 with extended context window",
                "context_window": 32768,
                "training_cutoff": "2023-04",
                "cost_input_per_1k": 0.06,
                "cost_output_per_1k": 0.12,
            },
            GPTModel.GPT4_TURBO.value: {
                "description": "Faster and cheaper version of GPT-4",
                "context_window": 128000,
                "training_cutoff": "2024-04",
                "cost_input_per_1k": 0.01,
                "cost_output_per_1k": 0.03,
            },
            GPTModel.GPT4_5_PREVIEW.value: {
                "description": "Latest preview model with enhanced capabilities",
                "context_window": 128000,
                "training_cutoff": "2024-04",
                "cost_input_per_1k": 0.01,
                "cost_output_per_1k": 0.03,
            },
            GPTModel.GPT4_OPTIMIZED.value: {
                "description": "Optimized for speed and cost",
                "context_window": 128000,
                "training_cutoff": "2024-04",
                "cost_input_per_1k": 0.01,
                "cost_output_per_1k": 0.02,
            },
            GPTModel.GPT4_OPTIMIZED_MINI.value: {
                "description": "Smaller, faster version of GPT-4 Optimized",
                "context_window": 128000,
                "training_cutoff": "2024-04",
                "cost_input_per_1k": 0.008,
                "cost_output_per_1k": 0.016,
            },
            GPTModel.O3_MINI.value: {
                "description": "Smallest and fastest GPT-4 model",
                "context_window": 128000,
                "training_cutoff": "2024-04",
                "cost_input_per_1k": 0.001,
                "cost_output_per_1k": 0.002,
            },
        }

        # Handle aliases
        base_model = GPTModel.get_base_model(model)
        return model_info.get(
            base_model, {"description": "Model information not available"}
        )
