import requests
import structlog
from app.services.ai.provider import AIProvider

logger = structlog.get_logger()

class GeminiProvider:
    """
    Gemini API client implementing the AIProvider interface.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"

    def generate_explanation(self, prompt: str) -> str:
        try:
            logger.info("gemini_provider_call_start", model=self.model)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                resp_json = response.json()
                text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("gemini_provider_call_success")
                return text.strip()
            else:
                logger.warn("gemini_provider_api_error", status_code=response.status_code, body=response.text)
                raise RuntimeError(f"Gemini API error: Status {response.status_code}")
        except Exception as e:
            logger.error("gemini_provider_exception", error=str(e))
            raise RuntimeError(f"Gemini Provider failed: {str(e)}") from e
