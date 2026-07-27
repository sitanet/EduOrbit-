from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    Abstract Enterprise Provider Interface for LLMs, Embeddings, and AI Copilots.
    """
    @abstractmethod
    def generate_response(self, prompt, system_instruction=""):
        pass

    @abstractmethod
    def generate_embedding(self, text):
        pass


class GoogleGeminiProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "Google Gemini",
            "model": "gemini-1.5-pro",
            "output_text": f"Gemini response to: '{prompt}'",
            "tokens_used": 150,
            "latency_ms": 320
        }

    def generate_embedding(self, text):
        return [0.012, 0.456, -0.789, 0.123]


class OpenAIProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "OpenAI",
            "model": "gpt-4o",
            "output_text": f"GPT-4 response to: '{prompt}'",
            "tokens_used": 180,
            "latency_ms": 410
        }

    def generate_embedding(self, text):
        return [0.098, -0.321, 0.654, -0.111]


class ClaudeProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "Anthropic",
            "model": "claude-3-5-sonnet",
            "output_text": f"Claude response to: '{prompt}'",
            "tokens_used": 160,
            "latency_ms": 380
        }

    def generate_embedding(self, text):
        return [0.045, 0.222, -0.555, 0.888]


class DeepSeekProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "DeepSeek",
            "model": "deepseek-coder-v2",
            "output_text": f"DeepSeek response to: '{prompt}'",
            "tokens_used": 140,
            "latency_ms": 290
        }

    def generate_embedding(self, text):
        return [0.111, 0.333, -0.444, 0.777]


class AzureOpenAIProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "Azure OpenAI",
            "model": "gpt-4o-azure",
            "output_text": f"Azure OpenAI response to: '{prompt}'",
            "tokens_used": 175,
            "latency_ms": 390
        }

    def generate_embedding(self, text):
        return [0.088, -0.311, 0.644, -0.100]


class LocalLLMProvider(BaseAIProvider):
    def generate_response(self, prompt, system_instruction=""):
        return {
            "status": "success",
            "provider": "Local Llama 3",
            "model": "llama-3-8b-instruct",
            "output_text": f"Local Llama 3 response to: '{prompt}'",
            "tokens_used": 130,
            "latency_ms": 210
        }

    def generate_embedding(self, text):
        return [0.010, 0.020, -0.030, 0.040]


class AIProviderFactory:
    """
    Zero-Code Change Provider Factory Engine.
    """
    @classmethod
    def get_provider(cls, provider_name="Gemini"):
        p_name = str(provider_name).lower()
        if 'openai' in p_name:
            return OpenAIProvider()
        elif 'claude' in p_name or 'anthropic' in p_name:
            return ClaudeProvider()
        elif 'deepseek' in p_name:
            return DeepSeekProvider()
        elif 'azure' in p_name:
            return AzureOpenAIProvider()
        elif 'local' in p_name or 'llama' in p_name:
            return LocalLLMProvider()
        return GoogleGeminiProvider()


def get_ai_provider(provider_name='Gemini'):
    return AIProviderFactory.get_provider(provider_name)
