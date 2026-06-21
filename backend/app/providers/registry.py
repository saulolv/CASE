import os

from sqlalchemy.orm import Session

from ..models import AgentRun
from .anthropic import AnthropicProvider
from .base import IntentProvider
from .demo import DemoProvider
from .gemini import GeminiProvider

PROVIDERS: dict[str, type] = {
    "demo": DemoProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}

CREDENTIAL_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _call_limit() -> int:
    return int(os.getenv("AGENT_CALL_LIMIT", "20"))


def _has_credentials(mode: str) -> bool:
    key = CREDENTIAL_KEYS.get(mode)
    return bool(key and os.getenv(key))


def _limit_reached(db: Session, mode: str) -> bool:
    return db.query(AgentRun).filter_by(provider=mode).count() >= _call_limit()


def provider_for(db: Session) -> IntentProvider:
    mode = os.getenv("AGENT_MODE", "demo").lower()
    if mode == "demo":
        return DemoProvider()
    provider_cls = PROVIDERS.get(mode)
    if not provider_cls or not _has_credentials(mode) or _limit_reached(db, mode):
        return DemoProvider()
    return provider_cls()
