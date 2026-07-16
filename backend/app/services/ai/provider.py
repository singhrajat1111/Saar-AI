from typing import Protocol

class AIProvider(Protocol):
    """
    Protocol/Interface defining the contract for AI explanation providers.
    """
    def generate_explanation(self, prompt: str) -> str:
        """
        Sends the formatted prompt to the LLM and returns the raw response text.
        """
        ...
