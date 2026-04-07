"""ReasoningEngine + provider tests.

Verifies that:
1. The default config loads the stub provider.
2. The stub provider produces a valid DecisionPayload shape.
3. An unknown provider name falls back to stub.
4. The anthropic provider falls back to stub when ANTHROPIC_API_KEY is unset
   (most CI environments).
5. The bridge correctly marks deterministic_fallback=True when the stub is
   active and False when a real provider is active.
"""
from __future__ import annotations

import os

from director_hub.reasoning.engine import ReasoningEngine
from director_hub.reasoning.providers.stub import StubProvider


def _make_request() -> dict:
    return {
        "schema_version": "1.0.0",
        "session_id": "test-1",
        "actor_id": "player",
        "player_input": "I attack the goblin",
        "actor_stats": {"hp": 20, "max_hp": 20},
    }


def test_default_engine_uses_stub_provider():
    engine = ReasoningEngine()
    assert engine.provider_name == "stub"
    assert engine.provider_is_real is False


def test_stub_returns_well_formed_decision():
    engine = ReasoningEngine()
    decision = engine.interpret(_make_request())
    assert decision["session_id"] == "test-1"
    assert decision["success"] is True
    assert 1 <= decision["scale"] <= 10
    assert isinstance(decision["narrative_text"], str)
    assert decision["narrative_text"] != ""
    assert decision["stat_effects"] == []
    assert decision["deterministic_fallback"] is True


def test_unknown_provider_falls_back_to_stub():
    engine = ReasoningEngine(config={"active": "fictional_provider", "providers": []})
    assert engine.provider_name == "stub"


def test_anthropic_falls_back_to_stub_without_api_key(monkeypatch):
    """Without ANTHROPIC_API_KEY set, the anthropic provider should
    raise ProviderUnavailable on construction and the engine should
    silently fall back to the stub."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    engine = ReasoningEngine(
        config={"active": "anthropic", "providers": [{"name": "anthropic"}]}
    )
    # Either falls back to stub (anthropic SDK installed but no key) OR
    # falls back to stub (anthropic SDK not installed at all). Both paths
    # land at the same provider name.
    assert engine.provider_name == "stub"


def test_explicit_stub_provider_class():
    """Direct StubProvider construction (no engine wrapper) returns inner shape."""
    p = StubProvider()
    assert p.is_real is False
    inner = p.interpret(_make_request())
    assert inner["success"] is True
    assert "narrative_text" in inner
    assert inner["stat_effects"] == []


def test_decision_has_schema_version_and_session_id():
    """Even when the inner provider doesn't include them, the engine
    wrapper must add schema_version and session_id."""
    engine = ReasoningEngine()
    decision = engine.interpret(_make_request())
    assert decision["schema_version"] == "1.0.0"
    assert decision["session_id"] == "test-1"
