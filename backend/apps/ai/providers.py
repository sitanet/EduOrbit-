from backend.apps.ai.interfaces import IAIProvider

class OpenAIProvider(IAIProvider):
    def generate_response(self, prompt: str, system_instructions: str = "") -> str:
        return f"[OpenAI Response]: Output for prompt: '{prompt}'"


class GeminiProvider(IAIProvider):
    def generate_response(self, prompt: str, system_instructions: str = "") -> str:
        return f"[Gemini Response]: Output for prompt: '{prompt}'"


class ClaudeProvider(IAIProvider):
    def generate_response(self, prompt: str, system_instructions: str = "") -> str:
        return f"[Claude Response]: Output for prompt: '{prompt}'"
