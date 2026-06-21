import os
import time

from ..schemas import IntentClassification
from .base import INTENT_SYSTEM_PROMPT, ProviderResult


class AnthropicProvider:
    name = "anthropic"

    def classify(self, content: str) -> ProviderResult:
        started = time.monotonic()
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=8.0)
            message = client.messages.create(
                model=model,
                max_tokens=180,
                temperature=0,
                system=INTENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
            )
            text = next((block.text for block in message.content if hasattr(block, "text")), "")
            value = IntentClassification.model_validate_json(text)
            return ProviderResult(
                value=value,
                provider=self.name,
                model=model,
                latency_ms=int((time.monotonic() - started) * 1000),
                input_tokens=getattr(message.usage, "input_tokens", 0),
                output_tokens=getattr(message.usage, "output_tokens", 0),
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
