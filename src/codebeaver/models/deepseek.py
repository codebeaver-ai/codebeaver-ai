import os
from typing import List, Dict, Any
import openai
from enum import Enum

class DeepSeekModel(Enum):
    # Chat Models
    CHAT = "deepseek-chat"
    CHAT_INSTRUCT = "deepseek-chat-instruct"
    
    # Code Models
    CODE = "deepseek-code"
    CODE_INSTRUCT = "deepseek-code-instruct"
    
    # Reasoning Models
    REASONER = "deepseek-reasoner"
    REASONER_INSTRUCT = "deepseek-reasoner-instruct"
    
    # Vision Models
    VISION = "deepseek-vision"
    VISION_INSTRUCT = "deepseek-vision-instruct"

class DeepSeekProvider:
    def __init__(self, model: str = DeepSeekModel.CHAT.value):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        
        openai.api_key = self.api_key
        openai.api_base = "https://api.deepseek.com/v1"
        self.model = model

        # Validate model
        try:
            if not any(self.model == m.value for m in DeepSeekModel):
                valid_models = [m.value for m in DeepSeekModel]
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
            raise Exception(f"Error creating chat completion with DeepSeek: {str(e)}")

    @staticmethod
    def get_available_models() -> List[str]:
        """Returns a list of all available DeepSeek models."""
        return [model.value for model in DeepSeekModel]

    @staticmethod
    def get_model_info(model: str) -> Dict[str, Any]:
        """Returns information about a specific model."""
        model_info = {
            DeepSeekModel.CHAT.value: {
                "description": "General-purpose chat model",
                "max_tokens": 8192,
                "type": "chat",
                "capabilities": ["text generation", "conversation"],
            },
            DeepSeekModel.CHAT_INSTRUCT.value: {
                "description": "Instruction-tuned chat model",
                "max_tokens": 8192,
                "type": "chat",
                "capabilities": ["text generation", "conversation", "instruction following"],
            },
            DeepSeekModel.CODE.value: {
                "description": "Specialized code generation model",
                "max_tokens": 8192,
                "type": "code",
                "capabilities": ["code generation", "code completion", "code explanation"],
            },
            DeepSeekModel.CODE_INSTRUCT.value: {
                "description": "Instruction-tuned code generation model",
                "max_tokens": 8192,
                "type": "code",
                "capabilities": ["code generation", "code completion", "code explanation", "instruction following"],
            },
            DeepSeekModel.REASONER.value: {
                "description": "Advanced reasoning and problem-solving model",
                "max_tokens": 8192,
                "type": "reasoning",
                "capabilities": ["logical reasoning", "problem solving", "analysis"],
            },
            DeepSeekModel.REASONER_INSTRUCT.value: {
                "description": "Instruction-tuned reasoning model",
                "max_tokens": 8192,
                "type": "reasoning",
                "capabilities": ["logical reasoning", "problem solving", "analysis", "instruction following"],
            },
            DeepSeekModel.VISION.value: {
                "description": "Vision and image understanding model",
                "max_tokens": 8192,
                "type": "vision",
                "capabilities": ["image understanding", "visual analysis", "image description"],
            },
            DeepSeekModel.VISION_INSTRUCT.value: {
                "description": "Instruction-tuned vision model",
                "max_tokens": 8192,
                "type": "vision",
                "capabilities": ["image understanding", "visual analysis", "image description", "instruction following"],
            },
        }
        return model_info.get(model, {"description": "Model information not available"})



