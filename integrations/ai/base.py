from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AIGatewayAdapter(ABC):
    """
    Interface for LLM and cognitive service providers (e.g. Google Gemini, OpenAI, Anthropic).
    """
    @abstractmethod
    def generate_text(self, 
                      prompt: str, 
                      system_instruction: str = None, 
                      temperature: float = 0.2, 
                      max_tokens: int = 1000) -> str:
        """Query LLM prompt generation."""
        pass

    @abstractmethod
    def analyze_structure(self, 
                          data: Dict[str, Any], 
                          schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert unstructured JSON / text inputs to structured schema responses."""
        pass
