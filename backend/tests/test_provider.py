import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_provider.db")

from app.models import AgentRun, Base
from app.providers import provider_for
from app.providers.anthropic import AnthropicProvider
from app.providers.demo import DemoProvider
from app.providers.gemini import GeminiProvider
from app.schemas import IntentClassification


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_provider_for_demo_mode(db):
    with patch.dict(os.environ, {"AGENT_MODE": "demo"}, clear=False):
        assert isinstance(provider_for(db), DemoProvider)


def test_provider_for_gemini_without_key_falls_back(db):
    with patch.dict(os.environ, {"AGENT_MODE": "gemini", "GEMINI_API_KEY": ""}, clear=False):
        assert isinstance(provider_for(db), DemoProvider)


def test_provider_for_gemini_with_key(db):
    with patch.dict(os.environ, {"AGENT_MODE": "gemini", "GEMINI_API_KEY": "test-key", "AGENT_CALL_LIMIT": "20"}, clear=False):
        assert isinstance(provider_for(db), GeminiProvider)


def test_provider_for_anthropic_with_key(db):
    with patch.dict(os.environ, {"AGENT_MODE": "anthropic", "ANTHROPIC_API_KEY": "test-key", "AGENT_CALL_LIMIT": "20"}, clear=False):
        assert isinstance(provider_for(db), AnthropicProvider)


def test_provider_for_limit_reached_falls_back(db):
    for _ in range(3):
        db.add(AgentRun(lead_id=None, trigger="reply", decision={}, mode="gemini", provider="gemini"))
    db.commit()
    with patch.dict(os.environ, {"AGENT_MODE": "gemini", "GEMINI_API_KEY": "test-key", "AGENT_CALL_LIMIT": "3"}, clear=False):
        assert isinstance(provider_for(db), DemoProvider)


def test_demo_provider_classifies_confirm():
  result = DemoProvider().classify("Confirmo minha presenca no evento")
  assert result.value.intent == "confirm"
  assert result.provider == "demo"


def test_gemini_provider_parses_json():
  mock_response = MagicMock()
  mock_response.text = '{"intent":"confirm","confidence":0.95,"evidence":["yes"]}'
  mock_response.usage_metadata = MagicMock(prompt_token_count=10, candidates_token_count=5)
  mock_client = MagicMock()
  mock_client.models.generate_content.return_value = mock_response
  with patch.dict(os.environ, {"GEMINI_API_KEY": "test", "GEMINI_MODEL": "gemini-2.0-flash"}, clear=False):
    with patch("google.genai.Client", return_value=mock_client):
      result = GeminiProvider().classify("Confirmo")
  assert result.value.intent == "confirm"
  assert result.provider == "gemini"
  assert not result.fallback


def test_gemini_provider_fallback_on_error():
  with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}, clear=False):
    with patch("google.genai.Client", side_effect=RuntimeError("network")):
      result = GeminiProvider().classify("Confirmo")
  assert result.fallback
  assert result.value.intent == "unknown"


def test_anthropic_provider_parses_json():
  mock_block = MagicMock()
  mock_block.text = '{"intent":"opt_out","confidence":0.99,"evidence":["stop"]}'
  mock_message = MagicMock()
  mock_message.content = [mock_block]
  mock_message.usage.input_tokens = 8
  mock_message.usage.output_tokens = 4
  mock_client = MagicMock()
  mock_client.messages.create.return_value = mock_message
  with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}, clear=False):
    with patch("anthropic.Anthropic", return_value=mock_client):
      result = AnthropicProvider().classify("Nao quero mais contato")
  assert result.value.intent == "opt_out"
  assert result.provider == "anthropic"
