import os
from typing import List, Dict, Any
import openai
from enum import Enum

class OllamaModel(Enum):
    # Large Language Models
    LLAMA2 = "llama2"
    LLAMA2_UNCENSORED = "llama2-uncensored"
    LLAMA2_13B = "llama2:13b"
    LLAMA2_70B = "llama2:70b"
    
    # Code Models
    CODELLAMA = "codellama"
    CODELLAMA_INSTRUCT = "codellama:instruct"
    CODELLAMA_PYTHON = "codellama:python"
    
    # Multilingual Models
    NEURAL_CHAT = "neural-chat"
    STARLING_LM = "starling-lm"
    VICUNA = "vicuna"
    
    # Small/Fast Models
    MISTRAL = "mistral"
    MISTRAL_OPENORCA = "mistral-openorca"
    ORCA_MINI = "orca-mini"
    
    # Specialized Models
    STABLE_LM = "stable-lm"
    DOLPHIN_MISTRAL = "dolphin-mistral"
    WIZARD_MATH = "wizard-math"
    PHIND_CODELLAMA = "phind-codellama"
    
    # Vision Models
    LLAVA = "llava"
    BAKLLAVA = "bakllava"

class OllamaProvider:
    def __init__(self, model: str = OllamaModel.LLAMA2.value, host: str = "localhost", port: int = 11434):
        self.api_key = "ollama"  # Required by OpenAI client but not used
        self.host = host
        self.port = port
        self.model = model
        
        openai.api_key = self.api_key
        openai.api_base = f"http://{self.host}:{self.port}/v1"

        # Validate model
        try:
            if not any(self.model == m.value for m in OllamaModel):
                valid_models = [m.value for m in OllamaModel]
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
            raise Exception(f"Error creating chat completion with Ollama: {str(e)}")

    @staticmethod
    def get_available_models() -> List[str]:
        """Returns a list of all available Ollama models."""
        return [model.value for model in OllamaModel]

    @staticmethod
    def get_model_info(model: str) -> Dict[str, Any]:
        """Returns information about a specific model."""
        model_info = {
            OllamaModel.LLAMA2.value: {
                "description": "Meta's Llama 2 base model",
                "type": "general",
                "capabilities": ["text generation", "conversation", "analysis"],
                "size": "7B parameters",
            },
            OllamaModel.LLAMA2_UNCENSORED.value: {
                "description": "Uncensored version of Llama 2",
                "type": "general",
                "capabilities": ["text generation", "conversation", "analysis"],
                "size": "7B parameters",
            },
            OllamaModel.LLAMA2_13B.value: {
                "description": "Larger version of Llama 2",
                "type": "general",
                "capabilities": ["text generation", "conversation", "analysis"],
                "size": "13B parameters",
            },
            OllamaModel.LLAMA2_70B.value: {
                "description": "Largest version of Llama 2",
                "type": "general",
                "capabilities": ["text generation", "conversation", "analysis"],
                "size": "70B parameters",
            },
            OllamaModel.CODELLAMA.value: {
                "description": "Specialized code generation model",
                "type": "code",
                "capabilities": ["code generation", "code completion", "code explanation"],
                "size": "7B parameters",
            },
            OllamaModel.CODELLAMA_INSTRUCT.value: {
                "description": "Instruction-tuned CodeLlama",
                "type": "code",
                "capabilities": ["code generation", "code completion", "instruction following"],
                "size": "7B parameters",
            },
            OllamaModel.CODELLAMA_PYTHON.value: {
                "description": "Python-specialized CodeLlama",
                "type": "code",
                "capabilities": ["python code", "code completion", "code explanation"],
                "size": "7B parameters",
            },
            OllamaModel.NEURAL_CHAT.value: {
                "description": "Optimized chat model",
                "type": "chat",
                "capabilities": ["conversation", "instruction following"],
                "size": "7B parameters",
            },
            OllamaModel.STARLING_LM.value: {
                "description": "High-quality instruction following model",
                "type": "chat",
                "capabilities": ["conversation", "instruction following"],
                "size": "7B parameters",
            },
            OllamaModel.VICUNA.value: {
                "description": "ChatGPT-like assistant",
                "type": "chat",
                "capabilities": ["conversation", "instruction following"],
                "size": "7B parameters",
            },
            OllamaModel.MISTRAL.value: {
                "description": "Efficient and powerful model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
            },
            OllamaModel.MISTRAL_OPENORCA.value: {
                "description": "Mistral fine-tuned on OpenOrca dataset",
                "type": "general",
                "capabilities": ["text generation", "conversation", "instruction following"],
                "size": "7B parameters",
            },
            OllamaModel.ORCA_MINI.value: {
                "description": "Small and fast model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "3B parameters",
            },
            OllamaModel.STABLE_LM.value: {
                "description": "Stable and reliable model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
            },
            OllamaModel.DOLPHIN_MISTRAL.value: {
                "description": "Uncensored Mistral variant",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
            },
            OllamaModel.WIZARD_MATH.value: {
                "description": "Specialized mathematics model",
                "type": "specialized",
                "capabilities": ["mathematics", "problem solving", "calculation"],
                "size": "7B parameters",
            },
            OllamaModel.PHIND_CODELLAMA.value: {
                "description": "Enhanced CodeLlama for development",
                "type": "code",
                "capabilities": ["code generation", "code completion", "technical discussion"],
                "size": "34B parameters",
            },
            OllamaModel.LLAVA.value: {
                "description": "Vision-language model",
                "type": "vision",
                "capabilities": ["image understanding", "visual analysis", "image description"],
                "size": "7B parameters",
            },
            OllamaModel.BAKLLAVA.value: {
                "description": "Alternative vision-language model",
                "type": "vision",
                "capabilities": ["image understanding", "visual analysis", "image description"],
                "size": "7B parameters",
            },
        }
        return model_info.get(model, {"description": "Model information not available"})
