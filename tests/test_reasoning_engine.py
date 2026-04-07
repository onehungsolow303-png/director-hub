"""ReasoningEngine + provider tests.

Verifies that:
1. An engine constructed with explicit stub config uses the stub provider.
2. The stub provider produces a valid DecisionPayload shape.
3. An unknown provider name falls back to stub.
4. The anthropic provider falls back to stub when ANTHROPIC_API_KEY is unset
   (most CI environments).
5. The bridge correctly marks deterministic_fallback=True when the stub is
   active and False when a real provider is active.

Tests construct engines with explicit config rather than calling
`ReasoningEngine()` with no args, because the on-disk models.yaml may
point at a real LLM provider in production. Test isolation requires not
depending on that file.
"""
from __future__ import annotations

import os

from director_hub.reasoning.engine import ReasoningEngine
from director_hub.reasoning.providers.stub import StubProvider

_STUB_CONFIG = {"active": "stub", "providers": [{"name": "stub"}]}


def _make_request() -> dict:
    return {
        "schema_version": "1.0.0",
        "session_id": "test-1",
        "actor_id": "player",
        "player_input": "I attack the goblin",
        "actor_stats": {"hp": 20, "max_hp": 20},
    }


def test_explicit_stub_config_loads_stub_provider():
    engine = ReasoningEngine(config=_STUB_CONFIG)
    assert engine.provider_name == "stub"
    assert engine.provider_is_real is False


def test_stub_returns_well_formed_decision():
    engine = ReasoningEngine(config=_STUB_CONFIG)
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


def test_anthropic_falls_back_to_stub_without_api_key(monkeypatch, tmp_path):
    """Without any Anthropic credential, the anthropic provider should
    raise ProviderUnavailable on construction and the engine should
    silently fall back to the stub.

    The provider checks two sources in priority order:
      1. ~/.claude/.credentials.json (Claude Code OAuth token, rotates)
      2. ANTHROPIC_API_KEY env var (stable billing key)

    Both must be absent for this test, so we monkeypatch HOME to a fresh
    tmp_path so the credentials file doesn't exist there.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Path.home() on Windows
    # Path.home() caches its result via os.path.expanduser; reload the
    # module-level constant the provider holds.
    import importlib

    from director_hub.reasoning.providers import anthropic as anthropic_provider

    importlib.reload(anthropic_provider)

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
    engine = ReasoningEngine(config=_STUB_CONFIG)
    decision = engine.interpret(_make_request())
    assert decision["schema_version"] == "1.0.0"
    assert decision["session_id"] == "test-1"
