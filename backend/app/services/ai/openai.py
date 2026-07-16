import requests
import structlog
from app.services.ai.provider import AIProvider

logger = structlog.get_logger()

class OpenAIProvider:
    """
    OpenAI API client implementing the AIProvider interface.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4o-mini"

    def generate_explanation(self, prompt: str) -> str:
        try:
            logger.info("openai_provider_call_start", model=self.model)
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                resp_json = response.json()
                text = resp_json["choices"][0]["message"]["content"]
                logger.info("openai_provider_call_success")
                return text.strip()
            else:
                logger.warn("openai_provider_api_error", status_code=response.status_code, body=response.text)
                raise RuntimeError(f"OpenAI API error: Status {response.status_code}")
        except Exception as e:
            logger.error("openai_provider_exception", error=str(e))
            raise RuntimeError(f"OpenAI Provider failed: {str(e)}") from e
