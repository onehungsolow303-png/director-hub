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
        for _name, schema in schemas_by_name.items():
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
    final_json = json.dumps(
        {
            "success": True,
            "scale": 7,
            "narrative_text": "You rolled well.",
            "stat_effects": [],
            "fx_requests": [],
            "repetition_penalty": 0,
        }
    )
    iter2 = _response(stop_reason="end_turn", content=[_text_block(final_json)])
    fake_client.messages.create.side_effect = [iter1, iter2]

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        from director_hub.reasoning.providers.anthropic import AnthropicProvider

        p = AnthropicProvider()
        result = p.interpret(
            {
                "session_id": "unit-1",
                "actor_stats": {"hp": 20, "max_hp": 20},
                "player_input": "I roll for sneak",
            }
        )

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
        remember_request(
            {
                "session_id": "auto-inject-test",
                "actor_id": "player",
                "actor_stats": {"hp": 9, "max_hp": 20},
            }
        )

        p = AnthropicProvider()
        result = p.interpret(
            {
                "session_id": "auto-inject-test",
                "actor_stats": {"hp": 9, "max_hp": 20},
                "player_input": "How am I doing?",
            }
        )

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


def test_json_extractor_handles_bare_object():
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    result = _extract_json_object('{"success": true, "scale": 5}')
    assert result == {"success": True, "scale": 5}


def test_json_extractor_handles_code_fence():
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    raw = '```json\n{"narrative_text": "ok"}\n```'
    result = _extract_json_object(raw)
    assert result == {"narrative_text": "ok"}


def test_json_extractor_handles_prose_wrapped_fence():
    """The LLM sometimes adds prose before the JSON despite the prompt
    saying not to. The extractor must still find the object."""
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    raw = (
        "Here you go, the engine cache shows no scene so I'll improvise:\n\n"
        "```json\n"
        '{"success": true, "scale": 7, "narrative_text": "vivid scene"}\n'
        "```\n"
        "Let me know if you want changes."
    )
    result = _extract_json_object(raw)
    assert result is not None
    assert result["success"] is True
    assert result["scale"] == 7
    assert result["narrative_text"] == "vivid scene"


def test_json_extractor_skips_braces_inside_strings():
    """A '{' or '}' inside a string literal must not affect brace counting."""
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    raw = '{"narrative_text": "He said {hello} and walked away"}'
    result = _extract_json_object(raw)
    assert result == {"narrative_text": "He said {hello} and walked away"}


def test_json_extractor_handles_escaped_quotes():
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    raw = '{"narrative_text": "She whispered \\"begone\\" with venom"}'
    result = _extract_json_object(raw)
    assert result is not None
    assert result["narrative_text"] == 'She whispered "begone" with venom'


def test_json_extractor_returns_none_when_no_object():
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    assert _extract_json_object("just plain text with no braces") is None
    assert _extract_json_object("") is None
    assert _extract_json_object("[1, 2, 3]") is None  # array, not object


def test_json_extractor_handles_nested_objects():
    from director_hub.reasoning.providers.anthropic import _extract_json_object

    raw = '{"outer": {"inner": {"deeper": 1}}, "scale": 5}'
    result = _extract_json_object(raw)
    assert result == {"outer": {"inner": {"deeper": 1}}, "scale": 5}


def test_compose_system_prompt_no_persona_returns_default():
    from director_hub.reasoning.providers.anthropic import (
        _SYSTEM_PROMPT,
        _compose_system_prompt,
    )

    # No scene_context at all
    assert _compose_system_prompt({}) == _SYSTEM_PROMPT
    # Empty scene_context
    assert _compose_system_prompt({"scene_context": {}}) == _SYSTEM_PROMPT
    # scene_context with no persona key
    assert _compose_system_prompt({"scene_context": {"biome": "forest"}}) == _SYSTEM_PROMPT


def test_compose_system_prompt_with_persona_includes_role_block():
    from director_hub.reasoning.providers.anthropic import (
        _SYSTEM_PROMPT,
        _compose_system_prompt,
    )

    request = {
        "scene_context": {
            "npc_name": "Old Garth",
            "npc_role": "Camp leader",
            "npc_persona": "You are gruff and short-tempered.",
            "npc_knowledge": "The Hollow is dangerous.",
            "npc_behavior_rules": "RULE 1: never speak more than 3 sentences.",
        },
    }
    prompt = _compose_system_prompt(request)
    # The role-play frame should appear FIRST, before the standard rules
    assert prompt.index("ROLE-PLAY MODE") < prompt.index("standard game-master rules")
    # All persona fields should be embedded in the prompt
    assert "Old Garth" in prompt
    assert "Camp leader" in prompt
    assert "gruff and short-tempered" in prompt
    assert "Hollow is dangerous" in prompt
    assert "never speak more than 3 sentences" in prompt
    # The standard GM prompt should still be present at the bottom
    assert _SYSTEM_PROMPT in prompt


def test_compose_system_prompt_handles_partial_persona():
    """If only persona is set (no knowledge, no rules), still wrap it
    with the role-play frame and skip the empty optional sections."""
    from director_hub.reasoning.providers.anthropic import _compose_system_prompt

    request = {
        "scene_context": {
            "npc_persona": "You are a cheerful wandering bard.",
        },
    }
    prompt = _compose_system_prompt(request)
    assert "ROLE-PLAY MODE" in prompt
    assert "cheerful wandering bard" in prompt
    # Optional blocks shouldn't appear
    assert "WHAT YOU KNOW" not in prompt
    assert "BEHAVIOR RULES" not in prompt


def test_credential_resolver_prefers_credentials_file_over_env(monkeypatch, tmp_path):
    """When ~/.claude/.credentials.json exists with an OAuth token, the
    resolver should return it instead of the (likely stale) env var."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stale-env-value")

    creds_dir = tmp_path / ".claude"
    creds_dir.mkdir()
    creds_file = creds_dir / ".credentials.json"
    creds_file.write_text(
        json.dumps(
            {
                "claudeAiOauth": {
                    "accessToken": "fresh-oauth-token-from-disk",
                    "refreshToken": "rt",
                    "expiresAt": 9999999999999,
                }
            }
        )
    )

    import importlib

    from director_hub.reasoning.providers import anthropic as anthropic_provider

    importlib.reload(anthropic_provider)
    assert anthropic_provider._resolve_anthropic_key() == "fresh-oauth-token-from-disk"


def test_credential_resolver_falls_back_to_env_when_no_file(monkeypatch, tmp_path):
    """No credentials file at $HOME/.claude/ → use the env var."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-only-key")

    import importlib

    from director_hub.reasoning.providers import anthropic as anthropic_provider

    importlib.reload(anthropic_provider)
    assert anthropic_provider._resolve_anthropic_key() == "env-only-key"


def test_credential_resolver_returns_none_when_neither_source_present(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    import importlib

    from director_hub.reasoning.providers import anthropic as anthropic_provider

    importlib.reload(anthropic_provider)
    assert anthropic_provider._resolve_anthropic_key() is None


def test_provider_rebuilds_client_on_credential_rotation(
    fake_anthropic_module, monkeypatch, tmp_path
):
    """When the credentials file rotates between interpret() calls, the
    provider should rebuild its client with the new token."""
    fake_module, fake_client = fake_anthropic_module
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    creds_dir = tmp_path / ".claude"
    creds_dir.mkdir()
    creds_file = creds_dir / ".credentials.json"
    creds_file.write_text(
        json.dumps(
            {"claudeAiOauth": {"accessToken": "token-v1", "refreshToken": "r", "expiresAt": 9e12}}
        )
    )

    # End-turn response so the loop exits after one iteration
    iter_response = _response(
        stop_reason="end_turn",
        content=[_text_block('{"success": true, "scale": 5, "narrative_text": "ok"}')],
    )
    fake_client.messages.create.return_value = iter_response

    with patch.dict("sys.modules", {"anthropic": fake_module}):
        import importlib

        from director_hub.reasoning.providers import anthropic as anthropic_provider

        importlib.reload(anthropic_provider)

        p = anthropic_provider.AnthropicProvider()
        # Sanity: constructed with the v1 token
        assert p._current_key == "token-v1"
        first_call_kwargs = fake_module.Anthropic.call_args_list[0].kwargs
        assert first_call_kwargs["api_key"] == "token-v1"

        # First interpret() call: token unchanged, no rebuild expected
        p.interpret({"session_id": "rot-test", "player_input": "x"})
        assert fake_module.Anthropic.call_count == 1  # still just construction

        # Rotate the token on disk
        creds_file.write_text(
            json.dumps(
                {
                    "claudeAiOauth": {
                        "accessToken": "token-v2",
                        "refreshToken": "r",
                        "expiresAt": 9e12,
                    }
                }
            )
        )

        # Second interpret() call: should detect rotation and rebuild
        p.interpret({"session_id": "rot-test", "player_input": "y"})
        assert fake_module.Anthropic.call_count == 2  # construction + rebuild
        assert p._current_key == "token-v2"
        rebuild_kwargs = fake_module.Anthropic.call_args_list[1].kwargs
        assert rebuild_kwargs["api_key"] == "token-v2"


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
