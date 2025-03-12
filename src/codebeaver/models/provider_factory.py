from enum import Enum
from typing import Any
from .mistral import MistralProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .deepseek import DeepSeekProvider

class ProviderType(Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"

class ProviderFactory:
    @staticmethod
    def get_provider(provider_type: ProviderType) -> Any:
        if provider_type == ProviderType.MISTRAL:
            return MistralProvider()
        elif provider_type == ProviderType.OPENAI:
            return OpenAIProvider()
        elif provider_type == ProviderType.ANTHROPIC:
            return AnthropicProvider()
        elif provider_type == ProviderType.DEEPSEEK:
            return DeepSeekProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}") 