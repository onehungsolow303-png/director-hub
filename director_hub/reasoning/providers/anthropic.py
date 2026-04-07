"""Anthropic Claude provider with full tool-use loop.

Uses the official `anthropic` SDK + Claude's tool_use API. The provider
registers all four toolbelt entries (asset_request, dice_resolve,
narrative_write, game_state_read) at construction time and runs an
observe→reason→tool→reason→...→emit loop on each `interpret()` call.

The loop is bounded by `max_tool_iterations` (default 8) so a model
that gets stuck in a tool spiral fails fast instead of burning tokens.
Each iteration is one `messages.create` call; the LLM either:

  * stop_reason == "tool_use"   -> we dispatch tools, append tool_results,
                                   loop again
  * stop_reason == "end_turn"   -> we parse the final text as JSON,
                                   apply defensive defaults, return

Requires:
  - `pip install -e ".[anthropic]"`
  - ANTHROPIC_API_KEY environment variable

If either is missing, this provider raises ProviderUnavailable on
construction so the engine can fall back to the stub. It does NOT crash
on import — the import is lazy so the rest of director_hub stays
installable on systems without the SDK.

Spec: docs/toolbelt-status.md (audit doc for this wiring).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

from director_hub.toolbelt.asset_tool import AssetTool
from director_hub.toolbelt.dice_tool import DiceTool
from director_hub.toolbelt.game_state_tool import (
    GameStateTool,
    remember_request,
)
from director_hub.toolbelt.narrative_tool import NarrativeTool
from director_hub.toolbelt.registry import ToolRegistry

from .base import ReasoningProvider


class ProviderUnavailable(Exception):
    """Raised when a provider can't initialize (missing SDK or credentials)."""


_SYSTEM_PROMPT = """You are the AI Game Master for an RPG. You receive the
player's free-text action plus their stats and the scene context. You also
have access to four tools that let you gather information before deciding
what happens.

Available tools:
  - game_state_read: Read live engine state (player HP/position, pending
                     encounter, etc.) from Forever engine. Useful when
                     the user payload is missing context you need.
  - dice_resolve:    Roll dice via NdM[+/-K] notation. Use this for
                     LLM-side narrative checks (perception, persuasion,
                     sneak). Combat damage dice are resolved by the
                     engine in C# — do NOT roll those here.
  - asset_request:   Ask Asset Manager for a sprite/texture/sound. Use
                     this when the scene needs a visual element you
                     don't already have.
  - narrative_write: Append a structured journal entry. Optional;
                     useful for tracking conversation continuity.

Workflow:
  1. If you need information not in the user payload, call tools to
     fetch it. Make at most 2-3 tool calls per turn for latency.
     Specifically:
       - If the player explicitly asks to "roll", makes a "check", or
         the action requires a hidden chance roll (sneak, perception,
         persuasion, lockpick), CALL dice_resolve. Do not invent the
         result yourself.
       - If the user payload is missing actor_stats or scene_context,
         CALL game_state_read.
       - If your narrative introduces a new visual element (a creature
         the player hasn't seen, a tile / texture the scene needs),
         CALL asset_request so the engine can pre-load it.
  2. When you have what you need, emit your final response as a JSON
     object with these exact fields:

     {
       "success":            bool,
       "scale":              int 1-10,
       "narrative_text":     string (1-3 vivid sentences),
       "stat_effects":       [{target_id, stat, delta, status_effect?}],
       "fx_requests":        [{kind, biome?, theme?}],
       "repetition_penalty": int (higher when player repeats themselves)
     }

     `stat` must be one of "hp", "attack", "defense", "status".

The final response MUST be ONLY the JSON object — no surrounding prose,
no code fences. Do NOT invent stat values; only suggest deltas.
"""


class AnthropicProvider(ReasoningProvider):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 1024,
        max_tool_iterations: int = 8,
    ) -> None:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderUnavailable(
                f"anthropic SDK not installed: {e}. "
                'Run `pip install -e ".[anthropic]"` to enable this provider.'
            ) from e

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderUnavailable(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it before starting Director Hub to enable the Claude provider."
            )

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._max_tool_iterations = max_tool_iterations

        # Register all four tools so the LLM can call them via tool_use.
        # AssetTool and GameStateTool make HTTP calls under the hood; both
        # fall back gracefully when their target services are unreachable.
        self._registry = ToolRegistry()
        self._registry.register(DiceTool())
        self._registry.register(NarrativeTool())
        self._registry.register(AssetTool())
        self._registry.register(GameStateTool())
        self._tool_schemas = _build_tool_schemas()

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        # Cache the request payload so GameStateTool can answer with the
        # latest engine-sent state when Forever engine's GameStateServer
        # is unreachable. Cache key is session_id.
        remember_request(action_request)
        session_id = action_request.get("session_id", "")

        user_payload = json.dumps(
            {
                "session_id": session_id,
                "actor_stats": action_request.get("actor_stats", {}),
                "target_stats": action_request.get("target_stats"),
                "scene_context": action_request.get("scene_context", {}),
                "recent_history": action_request.get("recent_history", []),
                "player_input": action_request.get("player_input", ""),
            },
            ensure_ascii=False,
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_payload}]

        for _iteration in range(self._max_tool_iterations):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=_SYSTEM_PROMPT,
                    tools=self._tool_schemas,
                    messages=messages,
                )
            except Exception as e:  # SDK can raise many subtypes; catch broadly at boundary
                raise ProviderUnavailable(f"Anthropic API call failed: {e}") from e

            # Append assistant turn (text + any tool_use blocks) to history
            # so the next iteration can resolve tool_use_id references.
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                return self._parse_final(response, action_request)

            if response.stop_reason == "tool_use":
                tool_results = self._dispatch_tools(response, session_id)
                messages.append({"role": "user", "content": tool_results})
                continue

            # Unknown / refusal / max_tokens — surface as provider error
            raise ProviderUnavailable(
                f"unexpected stop_reason: {response.stop_reason!r}"
            )

        raise ProviderUnavailable(
            f"tool loop exceeded {self._max_tool_iterations} iterations without end_turn"
        )

    # ------------------------------------------------------------------ helpers

    def _dispatch_tools(self, response: Any, session_id: str) -> list[dict[str, Any]]:
        """Execute every tool_use block in the response and return a list of
        tool_result blocks ready to append as the next user message."""
        results: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue

            tool_name = block.name
            tool_input: dict[str, Any] = dict(block.input or {})

            # game_state_read needs the session_id to resolve cache lookups,
            # but the LLM doesn't always know it. Inject if absent.
            if tool_name == "game_state_read" and "session_id" not in tool_input:
                tool_input["session_id"] = session_id

            tool = self._registry.get(tool_name)
            if tool is None:
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"ok": False, "error": f"unknown tool: {tool_name}"}),
                    "is_error": True,
                })
                continue

            try:
                tool_output = tool.call(**tool_input)
                # Use warning level so the dispatch line shows in default
                # Python logging config (which suppresses INFO).
                logger.warning(
                    "[AnthropicProvider] tool dispatch: %s(%s) -> %s",
                    tool_name,
                    {k: v for k, v in tool_input.items() if k != "session_id"},
                    {k: tool_output.get(k) for k in ("ok", "found", "total", "passed", "size")},
                )
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(tool_output, default=str),
                })
            except Exception as e:  # boundary - tool failures must not crash the loop
                logger.warning("[AnthropicProvider] tool %s raised: %s", tool_name, e)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"ok": False, "error": str(e)}),
                    "is_error": True,
                })

        return results

    def _parse_final(self, response: Any, action_request: dict[str, Any]) -> dict[str, Any]:
        """Extract the final assistant text, parse as JSON, apply defensive
        defaults, return the inner-shape dict the engine wraps."""
        text_parts = [block.text for block in response.content if hasattr(block, "text")]
        raw = "".join(text_parts).strip()

        # Strip optional code-fence wrapping
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ProviderUnavailable(
                f"Anthropic final response was not valid JSON: {e}. Raw: {raw!r}"
            ) from e

        # Defensive defaults — the model may omit optional fields
        decision.setdefault("success", True)
        decision.setdefault("scale", 5)
        decision.setdefault("narrative_text", "")
        decision.setdefault("stat_effects", [])
        decision.setdefault("fx_requests", [])
        decision.setdefault("repetition_penalty", 0)
        return decision


def _build_tool_schemas() -> list[dict[str, Any]]:
    """Claude tool schemas matching each Tool's `call(**kwargs)` signature.

    Kept inline (not derived from the Tool classes via reflection) so that
    the LLM-facing schema is explicit, version-controlled, and easy to
    review without chasing through Python magic.
    """
    return [
        {
            "name": "dice_resolve",
            "description": (
                "Roll dice via NdM[+/-K] notation. Use for LLM-side narrative checks "
                "(perception, persuasion, sneak). Combat damage dice are resolved by "
                "Forever engine in C# — do NOT roll those here."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "spec": {
                        "type": "string",
                        "description": "Dice notation, e.g. '1d20', '3d6+2', '2d8-1'",
                    },
                    "dc": {
                        "type": "integer",
                        "description": "Optional difficulty class. If set, the result includes 'passed': bool.",
                    },
                },
                "required": ["spec"],
            },
        },
        {
            "name": "narrative_write",
            "description": (
                "Append a structured narrative line to the in-session journal. "
                "Useful for tracking conversation continuity across reasoning steps."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["append", "read", "clear"],
                        "description": "What to do. Default is 'append'.",
                    },
                    "actor": {
                        "type": "string",
                        "description": "Who is speaking/acting (e.g. 'player', 'npc_innkeeper', 'system')",
                    },
                    "text": {
                        "type": "string",
                        "description": "The narrative text to append (only used for action='append')",
                    },
                    "n": {
                        "type": "integer",
                        "description": "How many recent entries to read (only used for action='read'). Default 10.",
                    },
                },
                "required": ["action"],
            },
        },
        {
            "name": "asset_request",
            "description": (
                "Request a sprite/texture/sound from the Asset Manager service. "
                "Use this when the scene needs a visual asset for a new enemy, "
                "tile, item, or environment element."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "description": "Asset kind: sprite, texture, sound, prefab, tile, creature_token, item_icon",
                    },
                    "biome": {
                        "type": "string",
                        "description": "Optional biome hint (forest, dungeon, plains, ruins, castle)",
                    },
                    "theme": {
                        "type": "string",
                        "description": "Optional theme hint (stone, wood, metal)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags to narrow the match",
                    },
                    "allow_ai_generation": {
                        "type": "boolean",
                        "description": "If true, fall back to Stable Diffusion / Scenario.gg when no library asset matches. Default false.",
                    },
                },
                "required": ["kind"],
            },
        },
        {
            "name": "game_state_read",
            "description": (
                "Read live engine state (player HP/position, pending encounter, "
                "session_id, gold, etc.) from Forever engine's GameStateServer. "
                "Falls back to a session-scoped cache when the engine is "
                "unreachable. Use this when the user payload is missing context "
                "you need to make a decision."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "Optional. The Director Hub injects the current session_id "
                            "automatically if you omit it."
                        ),
                    },
                },
            },
        },
    ]
