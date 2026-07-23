from abc import ABC, abstractmethod

class IAIProvider(ABC):
    """
    Polymorphic interface to support multiple LLM models and fallback routes.
    """
    @abstractmethod
    def generate_response(self, prompt: str, system_instructions: str = "") -> str:
        pass


class IAIEmbeddingProvider(ABC):
    """
    Polymorphic interface for generating embedding search vectors.
    """
    @abstractmethod
    def get_embedding(self, text: str) -> list:
        pass
