from enum import Enum
from typing import Any
from .mistral import MistralProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .deepseek import DeepSeekProvider
from .ollama import OllamaProvider


class ProviderType(Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


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
        elif provider_type == ProviderType.OLLAMA:
            return OllamaProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
