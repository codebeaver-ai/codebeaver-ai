import os
from typing import List, Dict, Any
import openai
from enum import Enum

class OllamaModel(Enum):
    # Large Language Models - Llama Family
    LLAMA2 = "llama2"
    LLAMA2_7B = "llama2:7b"
    LLAMA2_13B = "llama2:13b"
    LLAMA2_70B = "llama2:70b"
    LLAMA3 = "llama3"
    LLAMA3_8B = "llama3:8b"
    LLAMA3_70B = "llama3:70b"
    LLAMA3_1 = "llama3.1"
    LLAMA3_1_8B = "llama3.1:8b"
    LLAMA3_1_70B = "llama3.1:70b"
    LLAMA3_1_405B = "lama3.1:405b"
    LLAMA3_2 = "llama3.2"
    LLAMA3_2_1B = "llama3.2:1b"
    LLAMA3_2_3B = "llama3.2:3b"
    LLAMA3_3 = "llama3.3"
    LLAMA3_3_70B = "llama3.3:70b"
    
    # Code Models
    CODELLAMA = "codellama"
    COMMAND_R = "command-r"
    DEEPSEEK_CODER_33B = "deepseek-coder:33b"
    
    # Mistral Models
    MISTRAL = "mistral"
    MISTRAL_SMALL = "mistral-small"
    MISTRAL_LARGE = "mistral-large"
    MISTRAL_OPENORCA = "mistral-openorca"
    
    # Mixtral Models
    MIXTRAL_8X22B_INSTRUCT = "mixtral:8x22b-instruct"
    
    # Phi Models
    PHI3_3_8B = "phi3:3.8b"
    PHI3_14B = "phi3:14b"
    
    # Qwen Models
    QWEN_0_5B = "qwen:0.5b"
    QWEN_1_8B = "qwen:1.8b"
    QWEN_4B = "qwen:4b"
    QWEN_14B = "qwen:14b"
    QWEN_32B = "qwen:32b"
    QWEN_72B = "qwen:72b"
    QWEN_110B = "qwen:110b"
    
    # Gemma Models
    GEMMA2 = "gemma2"
    GEMMA2_9B = "gemma2:9b"
    GEMMA2_27B = "gemma2:27b"
    
    # Other Models
    DBRX = "dbrx"
    FALCON = "falcon"
    GROK_1 = "grok-1"
    LLAVA = "llava"
    NOUS_HERMES2_34B = "nous-hermes2:34b"
    ORCA_MINI = "orca-mini"
    SCRAPEGRAPH = "scrapegraph"
    STABLELM_ZEPHYR = "stablelm-zephyr"
    WIZARDLM2_8X22B = "wizardlm2:8x22b"
    
    # Embedding Models
    DMETA_EMBEDDING_ZH_SMALL_Q4 = "shaw/dmeta-embedding-zh-small-q4"
    DMETA_EMBEDDING_ZH_Q4 = "shaw/dmeta-embedding-zh-q4"
    ACGE_TEXT_EMBEDDING = "chevalblanc/acge_text_embedding"
    DMETA_EMBEDDING_ZH = "martcreation/dmeta-embedding-zh"
    SNOWFLAKE_ARCTIC_EMBED = "snowflake-arctic-embed"
    NOMIC_EMBED_TEXT = "nomic-embed-text"
    MXBAI_EMBED_LARGE = "mxbai-embed-large"

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
            # Llama Family
            OllamaModel.LLAMA2.value: {
                "description": "Meta's Llama 2 base model",
                "type": "general",
                "capabilities": ["text generation", "conversation", "analysis"],
                "size": "7B parameters",
                "context_window": 4096
            },
            OllamaModel.LLAMA2_7B.value: {
                "description": "Meta's Llama 2 7B model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 4096
            },
            OllamaModel.LLAMA2_13B.value: {
                "description": "Larger version of Llama 2",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "13B parameters",
                "context_window": 4096
            },
            OllamaModel.LLAMA2_70B.value: {
                "description": "Largest version of Llama 2",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "70B parameters",
                "context_window": 4096
            },
            OllamaModel.LLAMA3.value: {
                "description": "Meta's Llama 3 base model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "8B parameters",
                "context_window": 8192
            },
            OllamaModel.LLAMA3_1.value: {
                "description": "Meta's Llama 3.1",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "8B parameters",
                "context_window": 128000
            },
            OllamaModel.LLAMA3_2.value: {
                "description": "Meta's Llama 3.2",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "1B-3B parameters",
                "context_window": 128000
            },
            OllamaModel.LLAMA3_3.value: {
                "description": "Meta's Llama 3.3",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "70B parameters",
                "context_window": 128000
            },
            # Code Models
            OllamaModel.CODELLAMA.value: {
                "description": "Specialized code generation model",
                "type": "code",
                "capabilities": ["code generation", "code completion"],
                "size": "7B parameters",
                "context_window": 16000
            },
            OllamaModel.COMMAND_R.value: {
                "description": "Specialized R programming model",
                "type": "code",
                "capabilities": ["R code generation", "data analysis"],
                "size": "7B parameters",
                "context_window": 12800
            },
            OllamaModel.DEEPSEEK_CODER_33B.value: {
                "description": "Large code generation model",
                "type": "code",
                "capabilities": ["code generation", "code completion"],
                "size": "33B parameters",
                "context_window": 16000
            },
            # Mistral Models
            OllamaModel.MISTRAL.value: {
                "description": "Efficient and powerful model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 128000
            },
            OllamaModel.MISTRAL_SMALL.value: {
                "description": "Small version of Mistral",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 128000
            },
            OllamaModel.MISTRAL_LARGE.value: {
                "description": "Large version of Mistral",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 128000
            },
            OllamaModel.MISTRAL_OPENORCA.value: {
                "description": "Mistral fine-tuned on OpenOrca dataset",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 32000
            },
            # Mixtral Models
            OllamaModel.MIXTRAL_8X22B_INSTRUCT.value: {
                "description": "Instruction-tuned Mixtral model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "176B parameters",
                "context_window": 65536
            },
            # Other Notable Models
            OllamaModel.DBRX.value: {
                "description": "Database-focused model",
                "type": "specialized",
                "capabilities": ["database operations", "SQL"],
                "size": "7B parameters",
                "context_window": 32768
            },
            OllamaModel.FALCON.value: {
                "description": "Efficient language model",
                "type": "general",
                "capabilities": ["text generation"],
                "size": "7B parameters",
                "context_window": 2048
            },
            OllamaModel.GROK_1.value: {
                "description": "xAI's Grok model",
                "type": "general",
                "capabilities": ["text generation", "conversation"],
                "size": "7B parameters",
                "context_window": 8192
            },
            OllamaModel.LLAVA.value: {
                "description": "Vision-language model",
                "type": "vision",
                "capabilities": ["image understanding", "visual analysis"],
                "size": "7B parameters",
                "context_window": 4096
            },
            OllamaModel.ORCA_MINI.value: {
                "description": "Small and fast model",
                "type": "general",
                "capabilities": ["text generation"],
                "size": "3B parameters",
                "context_window": 2048
            },
            # Embedding Models
            OllamaModel.NOMIC_EMBED_TEXT.value: {
                "description": "Text embedding model",
                "type": "embedding",
                "capabilities": ["text embeddings"],
                "size": "Not specified",
                "context_window": 8192
            },
            OllamaModel.MXBAI_EMBED_LARGE.value: {
                "description": "Large embedding model",
                "type": "embedding",
                "capabilities": ["text embeddings"],
                "size": "Not specified",
                "context_window": 512
            }
        }
        return model_info.get(model, {
            "description": "Model information not available",
            "type": "unknown",
            "capabilities": ["unknown"],
            "size": "Not specified",
            "context_window": None
        })
