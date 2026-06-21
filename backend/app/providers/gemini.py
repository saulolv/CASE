import os
import time

from ..schemas import IntentClassification
from .base import INTENT_SYSTEM_PROMPT, ProviderResult


class GeminiProvider:
    name = "gemini"

    def classify(self, content: str) -> ProviderResult:
        started = time.monotonic()
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            response = client.models.generate_content(
                model=model,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=INTENT_SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=180,
                    response_mime_type="application/json",
                    response_schema=IntentClassification,
                ),
            )
            value = IntentClassification.model_validate_json(response.text or "{}")
            usage = getattr(response, "usage_metadata", None)
            return ProviderResult(
                value=value,
                provider=self.name,
                model=model,
                latency_ms=int((time.monotonic() - started) * 1000),
                input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            )
        except Exception as exc:
            return ProviderResult(
                value=IntentClassification(intent="unknown", confidence=0, evidence=[]),
                provider=self.name,
                model=model,
                latency_ms=int((time.monotonic() - started) * 1000),
                error=type(exc).__name__,
                fallback=True,
            )
