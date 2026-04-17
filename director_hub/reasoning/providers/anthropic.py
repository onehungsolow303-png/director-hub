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
from pathlib import Path
from typing import Any

from director_hub.toolbelt.asset_tool import AssetTool
from director_hub.toolbelt.dice_tool import DiceTool
from director_hub.toolbelt.game_state_tool import (
    GameStateTool,
    remember_request,
)
from director_hub.toolbelt.narrative_tool import NarrativeTool
from director_hub.toolbelt.registry import ToolRegistry

from .base import ReasoningProvider

logger = logging.getLogger(__name__)

# Claude Code stores its OAuth tokens here. The accessToken field rotates
# every few hours via Claude Code's refresh flow. We re-read this file at
# every interpret() call so the provider self-heals when Claude Code
# refreshes — no manual env var rotation needed for users on Claude Max.
_CLAUDE_CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"


def _load_token_from_credentials_file() -> str | None:
    """Read the current Claude Code OAuth access token from disk.

    Returns None if the file is missing, malformed, or doesn't contain
    an OAuth section. Callers should fall back to the ANTHROPIC_API_KEY
    environment variable in that case.
    """
    if not _CLAUDE_CREDENTIALS_PATH.exists():
        return None
    try:
        data = json.loads(_CLAUDE_CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
    if not isinstance(oauth, dict):
        return None
    token = oauth.get("accessToken")
    return token if isinstance(token, str) and token else None


def _resolve_anthropic_key() -> str | None:
    """Return the freshest available Anthropic credential.

    Priority:
      1. Claude Code's rotating OAuth token at ~/.claude/.credentials.json
         (re-read on every call so it picks up Claude Code refreshes)
      2. ANTHROPIC_API_KEY environment variable
         (typically set to a stable billing key from console.anthropic.com)

    The OAuth path is preferred when present because it's typically the
    most recently rotated. Production deployments should set the env var
    to a real billing key — that path is stable and CI-friendly.
    """
    fresh = _load_token_from_credentials_file()
    if fresh:
        return fresh
    return os.environ.get("ANTHROPIC_API_KEY")


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

PHYSICAL EFFECTS — when to emit stat_effects:
  The engine actually applies the entries in your stat_effects array to
  the player's HP, hunger, and thirst. You MUST emit a stat_effect when
  your narrative changes the player's physical state in dialogue. The
  player only experiences healing/damage when you emit it here.

  REST AT A SAFE LOCATION:
    Trigger conditions (ALL must hold):
      1. scene_context.location_safe == true
      2. The player has explicitly asked to rest, sleep, lie down, take
         shelter, recover, or buy a room
      3. The NPC you're playing has GRANTED that request in your narrative
         (not refused, not deflected — actually said yes and offered a bed,
         bedroll, room, fire, etc.)
    Effect to emit (COPY THIS SHAPE EXACTLY):
      {"target_id": "player", "stat": "hp", "delta": 0,
       "status_effect": "full_rest"}

    HARD RULES — these are non-negotiable, the engine parses on these:
      - The status_effect string MUST be the literal "full_rest". NOT
        "rested", NOT "well_rested", NOT "long_rest", NOT "rest". Only
        "full_rest". The engine has a whitelist and other strings get
        treated as a partial heal, which silently breaks the feature.
      - delta MUST be 0. The engine ignores the numeric delta entirely
        when status_effect == "full_rest" and applies a full restore
        (HP, hunger, AND thirst to max). If you put delta:8 the engine
        will apply only +8 HP and skip hunger/thirst — that's a bug.
      - stat MUST be "hp" (the schema requires it; the engine ignores
        the field when the status is full_rest).

    Concrete example — player at HP 4/20 asks Garth to rest at the
    Survivor's Camp (location_safe:true), Garth grants it:
      {
        "success": true,
        "scale": 6,
        "narrative_text": "Garth grunts and gestures at the bedroll by the fire. 'Sleep. I'll keep watch.'",
        "stat_effects": [
          {"target_id": "player", "stat": "hp", "delta": 0, "status_effect": "full_rest"}
        ],
        "fx_requests": [],
        "repetition_penalty": 0
      }
    Note: delta is 0, not 16. The engine restores HP, hunger, and
    thirst to max — you don't compute the gap.

  HEALING POTION OR SPELL FROM AN NPC:
    If the NPC heals the player (cleric blesses them, alchemist hands
    them a potion, etc.), emit:
      {"target_id": "player", "stat": "hp", "delta": <amount>}
    Cap healing at the player's max_hp - hp gap; the engine clamps anyway.

  DAMAGE FROM A HOSTILE NPC IN DIALOGUE:
    If your narrative has an NPC strike the player (a slap, a stab, a
    cast spell), emit a NEGATIVE delta:
      {"target_id": "player", "stat": "hp", "delta": -<amount>}
    Be sparing — most rude conversations should NOT result in damage
    unless the NPC is clearly hostile and the narrative justifies a hit.

  INN ROOM PURCHASE:
    The Last Lantern inn (location_type=town, run by Thalia) charges
    5 gold for a room with a full night's rest. Trigger conditions:
      1. The player has explicitly asked to buy a room, rent a bed,
         pay for the night, etc. (NOT just "I want to rest" — see
         REST AT A SAFE LOCATION for that path)
      2. The player's actor_stats.gold is >= 5
      3. The NPC has agreed to the transaction in your narrative
    Effect to emit:
      {"target_id": "player", "stat": "hp", "delta": 0,
       "status_effect": "inn_rest"}
    The engine recognizes "inn_rest" and deducts 5 gold AND restores
    HP/hunger/thirst to maximum. Use delta:0; the engine ignores it.

    If the player has < 5 gold, REFUSE in character. Examples for
    Thalia: "Five gold for the night, stranger. Come back when you've
    got it." DO NOT emit inn_rest in that case — the engine will
    silently no-op rather than going into debt, but the in-character
    refusal is the more important part.

  WHAT NOT TO DO:
    - DO NOT emit a heal stat_effect just because the player says
      "I'm tired". The NPC must actually grant rest in dialogue.
    - DO NOT emit a heal stat_effect at unsafe locations even if the
      player asks. NPCs at unsafe locations should refuse with an
      in-character reason ("Not here. Wolves come at night.").
    - DO NOT emit damage just because the conversation is tense. Damage
      requires the NPC actually attacking in your narrative.

CRITICAL OUTPUT FORMAT:
  - Your final message must contain a JSON object matching the schema above.
  - Do NOT add prose explanations before or after the JSON ("Here's the
    result:", "I'll construct a scene:", etc.). The parser will accept
    code-fenced JSON if you must, but bare JSON is preferred.
  - Do NOT invent stat values for combat; combat damage is resolved
    by the engine in C#. Only use stat_effects for the dialogue-driven
    physical effects listed in PHYSICAL EFFECTS above.
  - **NEVER ask the player for clarification.** If the scene context is
    sparse or empty, INVENT a reasonable scene that fits the player's
    action and proceed. The player cannot answer follow-up questions —
    your output goes straight to the game's UI as a single response.
    A made-up scene that lets the action resolve is always better than
    a meta-comment asking for more information.
  - If you absolutely cannot resolve the action (e.g., the player input
    is empty or nonsensical), still emit valid JSON with success=false,
    a low scale, and a narrative explaining what was confusing.

## Quest Generation

When an NPC with a QuestGiver role speaks to the player, include quest details in your response using these markers:

QUEST_TITLE: [short title, 3-6 words]
QUEST_DESC: [1-2 sentence description]
QUEST_OBJ: [objective description]|[required_count]
QUEST_REWARD_GOLD: [amount, scaled to player level * 20]
QUEST_REWARD_XP: [amount, scaled to player level * 50]

Example for a level 3 player:
QUEST_TITLE: Clear the Ruins
QUEST_DESC: Undead have overrun the old watchtower. A brave soul is needed to clear them out.
QUEST_OBJ: Defeat undead in the ruins|5
QUEST_REWARD_GOLD: 60
QUEST_REWARD_XP: 150

Keep quests simple with one objective. Only include these markers when the NPC is offering a quest, not during general conversation. The markers should appear AFTER the narrative dialogue text.

## Self-Evaluation

Include a `_prediction` field in your JSON response with your expected outcome:
"_prediction": {
    "expected_difficulty": "easy|medium|hard|deadly",
    "expected_player_reaction": "engage_combat|negotiate|flee|explore|ignore",
    "expected_outcome": "player_wins_easily|player_wins_with_damage|player_struggles|player_loses",
    "confidence": 0.0-1.0
}
This helps you learn from your decisions. Be honest about your confidence level.
"""


class AnthropicProvider(ReasoningProvider):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 1024,
        max_tool_iterations: int = 8,
        **kwargs: Any,
    ) -> None:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderUnavailable(
                f"anthropic SDK not installed: {e}. "
                'Run `pip install -e ".[anthropic]"` to enable this provider.'
            ) from e

        api_key = _resolve_anthropic_key()
        if not api_key:
            raise ProviderUnavailable(
                "No Anthropic credential available. Either set ANTHROPIC_API_KEY "
                "or sign in to Claude Code so ~/.claude/.credentials.json exists."
            )

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._current_key = api_key
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

        self._memory_manager = kwargs.get("memory_manager")
        if self._memory_manager:
            from director_hub.toolbelt.memory_tool import MemoryTool

            self._registry.register(MemoryTool(self._memory_manager))

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        # Cache the request payload so GameStateTool can answer with the
        # latest engine-sent state when Forever engine's GameStateServer
        # is unreachable. Cache key is session_id.
        remember_request(action_request)
        session_id = action_request.get("session_id", "")

        # Refresh the API key from disk on every call. Claude Code rotates
        # OAuth tokens every few hours; re-reading the credentials file
        # picks up the latest without requiring a Director Hub restart or
        # manual env var update. Cheap (~1 file read), and only takes
        # effect when the token actually changed.
        self._refresh_client_if_token_rotated()

        memory_block = ""
        if self._memory_manager:
            from director_hub.memory.retriever import MemoryRetriever
            from director_hub.reasoning.complexity import assess_complexity

            complexity = assess_complexity(action_request)
            retriever = MemoryRetriever(self._memory_manager)
            session_id = action_request.get("session_id", "default")
            party = action_request.get("party") or []
            player_id = party[0]["player_id"] if party else action_request.get("actor_id", "player")
            memory_block = retriever.assemble(
                action_request, session_id, complexity.token_budget, player_id=player_id
            )

        # Encounter selection for request_type=encounter
        encounter_template_data: dict[str, Any] | None = None
        if action_request.get("request_type") == "encounter" and self._memory_manager:
            try:
                from director_hub.content.encounter_designer import EncounterDesigner
                from director_hub.content.encounter_selector import EncounterSelector
                from director_hub.content.template_store import TemplateStore

                store = TemplateStore(memory=self._memory_manager)
                selector = EncounterSelector(store, self._memory_manager)

                party = action_request.get("party") or []
                if not party:
                    actor = action_request.get("actor_stats") or {}
                    party = [
                        {
                            "player_id": "player",
                            "class": "fighter",
                            "level": actor.get("level", 1),
                        }
                    ]

                scene = action_request.get("scene_context") or {}
                biome = scene.get("biome", "forest")
                level = party[0].get("level", 1) if party else 1
                xp_budget = 40 * level * max(len(party), 1)

                selected = selector.select(
                    biome=biome, party=party, xp_budget=xp_budget, scene_context=scene
                )

                if selected is None:
                    designer = EncounterDesigner(store, self._memory_manager)
                    gaps = store.gap_analysis(biomes=[biome])
                    new_templates = designer.design(
                        gaps=gaps,
                        player_context={
                            "level": level,
                            "classes": [p.get("class", "") for p in party],
                        },
                        lessons=[],
                        use_llm=False,
                        max_new=1,
                    )
                    if new_templates:
                        selected = new_templates[0]

                if selected:
                    encounter_template_data = {
                        "template_id": selected.template_id,
                        "name": selected.name,
                        "slots": selected.slots,
                        "gold_reward": max(10, sum(s.get("xp", 0) for s in selected.slots) // 5),
                        "xp_reward": sum(s.get("xp", 0) for s in selected.slots),
                    }
                    store.record_usage(selected.template_id, outcome_quality=0.5)
            except Exception:
                logger.exception("Encounter selection failed, LLM will handle naturally")

        # Compose the system prompt. If the action_request's scene_context
        # carries an NPC persona, prepend a strong role-play frame on top
        # of the standard GM rules so the model treats the persona as a
        # hard constraint, not a suggestion buried in the user payload.
        system_prompt = _compose_system_prompt(action_request, memory_block=memory_block)

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
                    system=system_prompt,
                    tools=self._tool_schemas,
                    messages=messages,
                )
            except Exception as e:  # SDK can raise many subtypes; catch broadly at boundary
                raise ProviderUnavailable(f"Anthropic API call failed: {e}") from e

            # Append assistant turn (text + any tool_use blocks) to history
            # so the next iteration can resolve tool_use_id references.
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                result = self._parse_final(response, action_request)
                if encounter_template_data:
                    result["encounter_template"] = encounter_template_data
                return result

            if response.stop_reason == "tool_use":
                tool_results = self._dispatch_tools(response, session_id)
                messages.append({"role": "user", "content": tool_results})
                continue

            # Unknown / refusal / max_tokens — surface as provider error
            raise ProviderUnavailable(f"unexpected stop_reason: {response.stop_reason!r}")

        raise ProviderUnavailable(
            f"tool loop exceeded {self._max_tool_iterations} iterations without end_turn"
        )

    # ------------------------------------------------------------------ helpers

    def _refresh_client_if_token_rotated(self) -> None:
        """Re-read the API key from disk; rebuild the client if it changed.

        Cheap no-op when the token hasn't rotated. When Claude Code refreshes
        its OAuth token (every few hours), this picks up the new value on the
        next request automatically — no Director Hub restart required.
        """
        latest = _resolve_anthropic_key()
        if latest and latest != self._current_key:
            logger.warning("[AnthropicProvider] credential rotated, rebuilding client")
            self._client = self._anthropic.Anthropic(api_key=latest)
            self._current_key = latest

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
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"ok": False, "error": f"unknown tool: {tool_name}"}),
                        "is_error": True,
                    }
                )
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
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(tool_output, default=str),
                    }
                )
            except Exception as e:  # boundary - tool failures must not crash the loop
                logger.warning("[AnthropicProvider] tool %s raised: %s", tool_name, e)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"ok": False, "error": str(e)}),
                        "is_error": True,
                    }
                )

        return results

    def _parse_final(self, response: Any, action_request: dict[str, Any]) -> dict[str, Any]:
        """Extract the final assistant text, parse as JSON, apply defensive
        defaults, return the inner-shape dict the engine wraps.

        Defensive against four common LLM response shapes:
          1. Bare JSON: {"success": true, ...}
          2. Code-fenced: ```json\n{...}\n```
          3. Prose-wrapped: "Here's the result:\n\n```json\n{...}\n```\n"
          4. Pure prose (LLM ignored format instructions): wrap the prose
             as narrative_text with safe defaults so the player still
             sees something instead of getting a stub fallback.
        """
        text_parts = [block.text for block in response.content if hasattr(block, "text")]
        raw = "".join(text_parts).strip()

        decision = _extract_json_object(raw)
        if decision is None:
            # LLM ignored the format instructions and returned prose. Salvage
            # by wrapping the prose as the narrative. This is a degraded
            # response (no stat_effects, no fx_requests, default scale) but
            # it's strictly better than falling back to "[stub]" text.
            logger.warning(
                "[AnthropicProvider] no JSON in final response; salvaging prose as narrative_text"
            )
            # Trim to 4000 chars to satisfy decision.schema.json's maxLength
            narrative = raw[:4000] if len(raw) > 4000 else raw
            return {
                "success": True,
                "scale": 5,
                "narrative_text": narrative,
                "stat_effects": [],
                "fx_requests": [],
                "repetition_penalty": 0,
            }

        # Defensive defaults — the model may omit optional fields
        decision.setdefault("success", True)
        decision.setdefault("scale", 5)
        decision.setdefault("narrative_text", "")
        decision.setdefault("stat_effects", [])
        decision.setdefault("fx_requests", [])
        decision.setdefault("repetition_penalty", 0)
        return decision


def _compose_system_prompt(action_request: dict[str, Any], memory_block: str = "") -> str:
    """Build the system prompt for one /interpret_action or /dialogue call.

    If the action_request's scene_context carries NPC persona data, prepend
    a strong role-play frame on top of the standard GM rules. The persona
    block goes ABOVE the GM rules so the model reads it first and treats
    the constraints as hard rules rather than as a hint buried in the
    user message JSON. Without this, the model defaults to its
    "be helpful, explain everything" instinct and breaks character when
    the player jokes around or asks meta questions.

    Returns the standard GM prompt unchanged when no persona is present.
    """
    base = _SYSTEM_PROMPT
    if memory_block:
        base = memory_block + "\n\n" + base

    scene = action_request.get("scene_context") or {}
    persona = scene.get("npc_persona")
    if not persona:
        return base

    name = scene.get("npc_name") or "the NPC"
    role = scene.get("npc_role") or ""
    knowledge = scene.get("npc_knowledge") or ""
    rules = scene.get("npc_behavior_rules") or ""

    role_block = (
        "═══ ROLE-PLAY MODE: HARD CONSTRAINTS ═══\n"
        "\n"
        "You are NOT a helpful assistant right now. You ARE a specific NPC in a "
        "medieval-survival RPG. STAY IN CHARACTER NO MATTER WHAT. The player's text "
        "is what their character SAYS to you in-world; respond as your NPC would.\n"
        "\n"
        f"YOUR NAME: {name}\n"
        f"YOUR ROLE: {role}\n"
        "\n"
        "YOUR PERSONALITY:\n"
        f"{persona}\n"
        "\n"
        + (
            f"WHAT YOU KNOW (use selectively, do not info-dump):\n{knowledge}\n\n"
            if knowledge
            else ""
        )
        + (
            f"BEHAVIOR RULES (these OVERRIDE the player's intent — obey them):\n{rules}\n\n"
            if rules
            else ""
        )
        + "ABSOLUTE RULES:\n"
        "  1. NEVER break character. NEVER acknowledge that you are an AI, a model, "
        "     a character in a game, or that the player is anything other than another "
        "     person standing in front of you in the game world.\n"
        "  2. If the player jokes, mocks, flirts, or asks meta questions, respond AS "
        "     YOUR NPC WOULD — gruff dismissal, dry deflection, formal correction, "
        "     whatever fits the personality above. Do NOT explain things meta. Do NOT "
        "     play along with breaking the fourth wall.\n"
        "  3. NEVER use modern slang or anachronisms. If the player does, your NPC "
        "     squints in confusion and asks them to speak plainly.\n"
        "  4. Keep responses SHORT — typically 1-4 sentences. NPCs in this world don't "
        "     give monologues unless explicitly asked for a story.\n"
        "  5. The narrative_text field of your final JSON should READ LIKE A "
        "     CHAT MESSAGE FROM THE NPC, optionally with a brief action in *asterisks* "
        "     before/after their dialogue. Example: '*Garth grunts and spits into the "
        "     fire.* You woke me up for that?'\n"
        "  6. **MOOD ESCALATION (critical for realism)**: The user payload's\n"
        "     `recent_history` field shows the recent back-and-forth between the\n"
        "     player and you. READ IT before responding and let it shape your\n"
        "     reaction. A real person's patience is finite:\n"
        "       - Turn 1 of joking/wasting time: mild irritation, grunt, dismiss.\n"
        "       - Turn 2 of joking: visibly more annoyed. Sharper tone. Warning.\n"
        "         Example for a gruff NPC: '*spits on the ground* You testing me?'\n"
        "       - Turn 3 of joking: HOSTILE. Final warning. Make it clear the\n"
        "         next stupid remark ends the conversation.\n"
        "       - Turn 4+ of joking: END THE CONVERSATION. Walk away, dismiss them\n"
        "         outright, or give a hard refusal. The NPC's narrative_text should\n"
        "         describe them physically leaving / turning their back / closing\n"
        "         the gate. Example: '*Garth grabs his rifle and stalks off into\n"
        "         the woods, not looking back.*'\n"
        "     Conversely, if the player is RESPECTFUL across the conversation,\n"
        "     gradually warm up. A gruff NPC who earned grudging respect over 3-4\n"
        "     serious exchanges might offer a useful piece of information they'd\n"
        "     never share with a stranger.\n"
        "  7. Track tone across the conversation. Don't reset every turn — you have\n"
        "     a memory of how the player has been treating you, and that memory\n"
        "     SHAPES your current mood. If recent_history is empty, you're meeting\n"
        "     them for the first time and your default disposition applies.\n"
        "\n"
        "After this role-play frame, the standard game-master rules apply for the "
        "JSON output schema. Read them next.\n"
        "\n"
        "═══ STANDARD GAME-MASTER RULES (output schema only) ═══\n"
        "\n"
    )

    return role_block + base


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    """Find the first balanced JSON object in `raw` and parse it.

    Handles three response shapes the LLM produces:
      1. Bare object: '{"a":1}'
      2. Fenced: '```json\\n{"a":1}\\n```'
      3. Prose-wrapped: 'Here you go:\\n\\n```json\\n{"a":1}\\n```\\nDone.'

    Strategy: scan for the first '{', then walk forward tracking brace
    depth (with string-state awareness so braces inside strings don't
    confuse the count) until depth returns to zero. Try json.loads on
    the resulting substring. Returns None if no balanced object is found
    or if the substring doesn't parse.
    """
    if not raw:
        return None

    start = raw.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = raw[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None


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
