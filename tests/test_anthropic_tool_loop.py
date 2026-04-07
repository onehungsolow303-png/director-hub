"""Unit tests for AnthropicProvider's tool-use loop.

Mocks the anthropic SDK so these tests run without an API key, network,
or token expiry concerns. Verifies:

  1. Tool schemas are generated for all 4 toolbelt entries
  2. The loop dispatches tool_use blocks to the registered tools
  3. tool_results are appended to the message history with correct shape
  4. session_id is auto-injected into game_state_read calls
  5. The loop terminates on end_turn and parses the final JSON
  6. The loop terminates with ProviderUnavailable if max_iterations is hit
  7. Unknown tool names produce a structured tool_result error

End-to-end behavior against the real Anthropic API is verified by the
operator running the live curl in docs/toolbelt-status.md; this test
file covers the dispatch + parse logic in isolation.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_anthropic_module():
    """A fake `anthropic` module that AnthropicProvider's lazy import resolves
    to. The module exposes an `Anthropic` class whose `messages.create` is a
    MagicMock the test can program to return tool_use / end_turn responses."""
    fake_module = MagicMock()
    fake_client = MagicMock()
    fake_module.Anthropic = MagicMock(return_value=fake_client)
    return fake_module, fake_client


def _text_block(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _tool_use_block(tool_id: str, name: str, tool_input: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = tool_input
    return block


def _response(stop_reason: str, content: list):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = content
    return resp


def test_provider_registers_all_four_tools(fake_anthropic_module, monkeypatch):
    fake_module, _ = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider

        p = AnthropicProvider()
        names = {t.name for t in p._registry.all()}
        assert names == {"dice_resolve", "narrative_write", "asset_request", "game_state_read"}


def test_tool_schemas_have_required_fields(fake_anthropic_module, monkeypatch):
    fake_module, _ = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider

        p = AnthropicProvider()
        schemas_by_name = {s["name"]: s for s in p._tool_schemas}
        assert set(schemas_by_name.keys()) == {
            "dice_resolve",
            "narrative_write",
            "asset_request",
            "game_state_read",
        }
        # Each must have description + input_schema with type=object
        for name, schema in schemas_by_name.items():
            assert schema["description"]
            assert schema["input_schema"]["type"] == "object"
        # dice_resolve requires spec
        assert "spec" in schemas_by_name["dice_resolve"]["input_schema"]["required"]
        # asset_request requires kind
        assert "kind" in schemas_by_name["asset_request"]["input_schema"]["required"]


def test_loop_dispatches_tool_then_parses_final_json(fake_anthropic_module, monkeypatch):
    fake_module, fake_client = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    # Iteration 1: return a tool_use block for dice_resolve
    iter1 = _response(
        stop_reason="tool_use",
        content=[_tool_use_block("toolu_1", "dice_resolve", {"spec": "1d20", "dc": 10})],
    )
    # Iteration 2: return the final JSON
    final_json = json.dumps({
        "success": True,
        "scale": 7,
        "narrative_text": "You rolled well.",
        "stat_effects": [],
        "fx_requests": [],
        "repetition_penalty": 0,
    })
    iter2 = _response(stop_reason="end_turn", content=[_text_block(final_json)])
    fake_client.messages.create.side_effect = [iter1, iter2]

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider

        p = AnthropicProvider()
        result = p.interpret({
            "session_id": "unit-1",
            "actor_stats": {"hp": 20, "max_hp": 20},
            "player_input": "I roll for sneak",
        })

    # Two API calls (the loop went one round)
    assert fake_client.messages.create.call_count == 2
    # Final result is the parsed JSON
    assert result["success"] is True
    assert result["scale"] == 7
    assert result["narrative_text"] == "You rolled well."

    # The implementation mutates the same messages list across iterations,
    # so MagicMock's call_args_list captures the FINAL state by reference.
    # Inspect by absolute index instead of [-1]:
    #   [0] initial user payload
    #   [1] assistant iter1 (tool_use)
    #   [2] user tool_result (what we care about)
    #   [3] assistant iter2 (final JSON, only present after the loop ends)
    final_messages = fake_client.messages.create.call_args_list[1].kwargs["messages"]
    user_tool_result = final_messages[2]
    assert user_tool_result["role"] == "user"
    tool_result_block = user_tool_result["content"][0]
    assert tool_result_block["type"] == "tool_result"
    assert tool_result_block["tool_use_id"] == "toolu_1"
    inner = json.loads(tool_result_block["content"])
    assert inner["ok"] is True
    assert "total" in inner  # dice_resolve always returns a total


def test_session_id_auto_injected_into_game_state_read(fake_anthropic_module, monkeypatch):
    fake_module, fake_client = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    # First the LLM calls game_state_read with NO session_id; the provider
    # must inject it. Then the LLM ends with the final JSON.
    iter1 = _response(
        stop_reason="tool_use",
        content=[_tool_use_block("toolu_gs", "game_state_read", {})],
    )
    iter2 = _response(
        stop_reason="end_turn",
        content=[_text_block('{"success": true, "scale": 5, "narrative_text": "ok"}')],
    )
    fake_client.messages.create.side_effect = [iter1, iter2]

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider
        from director_hub.toolbelt.game_state_tool import remember_request

        # Seed the cache so game_state_read returns 'found'
        remember_request({
            "session_id": "auto-inject-test",
            "actor_id": "player",
            "actor_stats": {"hp": 9, "max_hp": 20},
        })

        p = AnthropicProvider()
        result = p.interpret({
            "session_id": "auto-inject-test",
            "actor_stats": {"hp": 9, "max_hp": 20},
            "player_input": "How am I doing?",
        })

    assert result["success"] is True
    final_messages = fake_client.messages.create.call_args_list[1].kwargs["messages"]
    # See note in test_loop_dispatches_tool_then_parses_final_json: index [2]
    # is the user tool_result message at second-call time.
    tool_result_block = final_messages[2]["content"][0]
    inner = json.loads(tool_result_block["content"])
    # The cache lookup should have succeeded because session_id was injected
    assert inner["ok"] is True
    # When live endpoint is unreachable in test, falls back to cache, so:
    # snapshot may come from cache with the seeded actor_stats
    assert inner.get("found") is True


def test_max_iterations_raises(fake_anthropic_module, monkeypatch):
    fake_module, fake_client = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    # Always return tool_use, never end_turn
    fake_client.messages.create.return_value = _response(
        stop_reason="tool_use",
        content=[_tool_use_block("toolu_x", "dice_resolve", {"spec": "1d6"})],
    )

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import (
            AnthropicProvider,
            ProviderUnavailable,
        )

        p = AnthropicProvider(max_tool_iterations=3)
        with pytest.raises(ProviderUnavailable, match="exceeded 3 iterations"):
            p.interpret({"session_id": "loop-test", "player_input": "loop"})

    assert fake_client.messages.create.call_count == 3


def test_unknown_tool_returns_structured_error(fake_anthropic_module, monkeypatch):
    fake_module, fake_client = fake_anthropic_module
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    iter1 = _response(
        stop_reason="tool_use",
        content=[_tool_use_block("toolu_bad", "fictional_tool", {"foo": "bar"})],
    )
    iter2 = _response(
        stop_reason="end_turn",
        content=[_text_block('{"success": false, "scale": 1, "narrative_text": "tool missing"}')],
    )
    fake_client.messages.create.side_effect = [iter1, iter2]

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider

        p = AnthropicProvider()
        result = p.interpret({"session_id": "u", "player_input": "x"})

    assert result["success"] is False
    final_messages = fake_client.messages.create.call_args_list[1].kwargs["messages"]
    tool_result_block = final_messages[2]["content"][0]
    assert tool_result_block.get("is_error") is True
    inner = json.loads(tool_result_block["content"])
    assert "unknown tool" in inner["error"]
