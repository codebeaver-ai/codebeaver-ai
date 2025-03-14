import os
from typing import List, Dict, Any
import openai
from enum import Enum

class MistralModel(Enum):
    # Premier Models
    CODESTRAL = "codestral-2501"
    CODESTRAL_LATEST = "codestral-latest"
    
    MISTRAL_LARGE = "mistral-large-2411"
    MISTRAL_LARGE_LATEST = "mistral-large-latest"
    
    PIXTRAL_LARGE = "pixtral-large-2411"
    PIXTRAL_LARGE_LATEST = "pixtral-large-latest"
    
    MISTRAL_SABA = "mistral-saba-2502"
    MISTRAL_SABA_LATEST = "mistral-saba-latest"
    
    MINISTRAL_3B = "ministral-3b-2410"
    MINISTRAL_3B_LATEST = "ministral-3b-latest"
    
    MINISTRAL_8B = "ministral-8b-2410"
    MINISTRAL_8B_LATEST = "ministral-8b-latest"
    
    MISTRAL_EMBED = "mistral-embed"
    MISTRAL_MODERATION = "mistral-moderation-2411"
    MISTRAL_MODERATION_LATEST = "mistral-moderation-latest"
    
    # Free Models
    MISTRAL_SMALL = "mistral-small-2501"
    MISTRAL_SMALL_LATEST = "mistral-small-latest"
    
    PIXTRAL = "pixtral-12b-2409"
    
    # Research Models
    MISTRAL_NEMO = "open-mistral-nemo"
    CODESTRAL_MAMBA = "open-codestral-mamba"

    @classmethod
    def get_base_model(cls, model: str) -> str:
        """Get the base model for any alias."""
        alias_mapping = {
            # Map latest aliases to their current versions
            "codestral-latest": cls.CODESTRAL.value,
            "mistral-large-latest": cls.MISTRAL_LARGE.value,
            "pixtral-large-latest": cls.PIXTRAL_LARGE.value,
            "mistral-saba-latest": cls.MISTRAL_SABA.value,
            "ministral-3b-latest": cls.MINISTRAL_3B.value,
            "ministral-8b-latest": cls.MINISTRAL_8B.value,
            "mistral-moderation-latest": cls.MISTRAL_MODERATION.value,
            "mistral-small-latest": cls.MISTRAL_SMALL.value,
        }
        return alias_mapping.get(model, model)

class MistralProvider:
    def __init__(self, model: str = MistralModel.MISTRAL_SMALL_LATEST.value):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        
        openai.api_key = self.api_key
        openai.api_base = "https://api.mistral.ai/v1"
        self.model = MistralModel.get_base_model(model)

        # Validate model
        try:
            if not any(self.model == m.value for m in MistralModel):
                valid_models = [m.value for m in MistralModel]
                raise ValueError(f"Invalid model: {model}. Valid models are: {valid_models}")
        except ValueError as e:
            raise ValueError(str(e))

    def create_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"Error creating chat completion with Mistral: {str(e)}")

    @staticmethod
    def get_available_models() -> List[str]:
        """Returns a list of all available Mistral models."""
        return [model.value for model in MistralModel]

    @staticmethod
    def get_model_info(model: str) -> Dict[str, Any]:
        """Returns information about a specific model."""
        model_info = {
            MistralModel.CODESTRAL.value: {
                "description": "Cutting-edge language model for coding",
                "max_tokens": 256000,
                "version": "25.01",
                "type": "premier",
            },
            MistralModel.MISTRAL_LARGE.value: {
                "description": "Top-tier reasoning model for high-complexity tasks",
                "max_tokens": 131000,
                "version": "24.11",
                "type": "premier",
            },
            MistralModel.PIXTRAL_LARGE.value: {
                "description": "Frontier-class multimodal model",
                "max_tokens": 131000,
                "version": "24.11",
                "type": "premier",
            },
            MistralModel.MISTRAL_SABA.value: {
                "description": "Powerful model for Middle East and South Asia languages",
                "max_tokens": 32000,
                "version": "25.02",
                "type": "premier",
            },
            MistralModel.MINISTRAL_3B.value: {
                "description": "World's best edge model",
                "max_tokens": 131000,
                "version": "24.10",
                "type": "premier",
            },
            MistralModel.MINISTRAL_8B.value: {
                "description": "Powerful edge model with high performance/price ratio",
                "max_tokens": 131000,
                "version": "24.10",
                "type": "premier",
            },
            MistralModel.MISTRAL_EMBED.value: {
                "description": "State-of-the-art semantic text representation",
                "max_tokens": 8000,
                "version": "23.12",
                "type": "premier",
            },
            MistralModel.MISTRAL_MODERATION.value: {
                "description": "Moderation service for harmful content detection",
                "max_tokens": 8000,
                "version": "24.11",
                "type": "premier",
            },
            MistralModel.MISTRAL_SMALL.value: {
                "description": "Leader in small models category",
                "max_tokens": 32000,
                "version": "25.01",
                "type": "free",
            },
            MistralModel.PIXTRAL.value: {
                "description": "12B model with image understanding capabilities",
                "max_tokens": 131000,
                "version": "24.09",
                "type": "free",
            },
            MistralModel.MISTRAL_NEMO.value: {
                "description": "Best multilingual open source model",
                "max_tokens": 131000,
                "version": "24.07",
                "type": "research",
            },
            MistralModel.CODESTRAL_MAMBA.value: {
                "description": "First mamba 2 open source model",
                "max_tokens": 256000,
                "version": "v0.1",
                "type": "research",
            },
        }

        # Handle latest aliases
        base_model = MistralModel.get_base_model(model)
        return model_info.get(base_model, {"description": "Model information not available"}) 