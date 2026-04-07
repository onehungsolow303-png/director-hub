# Toolbelt status (audit 2026-04-07)

## TL;DR

**The toolbelt module exists but is dead code at runtime.** The 4 well-implemented tools are never invoked by anything in the call graph. The Director Hub LLM is currently doing single-shot prompt → JSON reasoning with no tool access.

## What exists

| Component | Path | Status |
|---|---|---|
| `Tool` ABC | `director_hub/toolbelt/base.py` | ✅ well-defined, single `call(**kwargs)` abstract method |
| `ToolRegistry` | `director_hub/toolbelt/registry.py` | ✅ implemented |
| `DiceTool` (`dice_resolve`) | `director_hub/toolbelt/dice_tool.py` | ✅ real implementation, NdM±K notation, optional DC |
| `NarrativeTool` (`narrative_write`) | `director_hub/toolbelt/narrative_tool.py` | ✅ real |
| `AssetTool` (`asset_request`) | `director_hub/toolbelt/asset_tool.py` | ✅ real, hits Asset Manager HTTP |
| `GameStateTool` (`game_state_read`) | `director_hub/toolbelt/game_state_tool.py` | ✅ real, hits Forever engine GameStateServer (port 7803) |
| `Planner` | `director_hub/reasoning/planner.py` | ✅ pure-logic regex-based goal → tool-call sequence |

## What's missing — the dead-code chain

| Symbol | Defined? | Instantiated anywhere? | Used? |
|---|---|---|---|
| `ToolRegistry` | yes | **no** | no |
| `Planner` | yes | imported in 1 file (its own), nowhere else | **no** |
| `tool.call()` | abstract in `Tool`, concrete in 4 tool classes | — | **no `.call(...)` invocation anywhere in `director_hub/`** |

The `ReasoningEngine` calls `self._provider.interpret(action_request)` and returns whatever single dict the provider gave back. `AnthropicProvider.interpret()` makes one `messages.create(...)` call with no `tools=[...]` parameter, parses the JSON response, and returns it. No tool dispatch loop. No multi-turn reasoning.

## Why this matters

The whole post-pivot rationale for moving the brain into Director Hub was to enable agentic behavior — the LLM plans, calls tools to gather info / mutate state, observes results, plans again, until it reaches a terminal action. Right now we have all the pieces of that loop sitting in the file tree but nothing connecting them.

**Concrete impact:**
- The LLM cannot read live engine state mid-reasoning (`game_state_read` is unreachable)
- The LLM cannot request assets mid-narrative (`asset_request` is unreachable)
- The LLM cannot request dice rolls (`dice_resolve` is unreachable — though this matters less since combat dice live in C#)
- The Planner's 4 plan templates are dead

## What it would take to wire this up

1. **Instantiate `ToolRegistry` in `ReasoningEngine.__init__`** and register the 4 tools
2. **Pass the registered tool schemas to `AnthropicProvider.interpret()`** as Claude's `tools=[...]` parameter (Claude tool-use API: https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview)
3. **Implement a `tool_use` loop in `interpret()`**: while the response contains `tool_use` blocks, dispatch to `registry.get(name).call(**input)`, append the `tool_result` to the message history, call `messages.create` again. Stop when the response is `end_turn` with no tool calls.
4. **Update `_SYSTEM_PROMPT`** to tell the LLM when to use each tool and what shape to return at the end.
5. **Update `LoopController` reflection** to surface tool-call chains in trace records.
6. **Add a fallback path** that uses the Planner to generate a deterministic plan when no real LLM provider is available (the existing stub provider could consume Planner output to feel less canned).

Estimated scope: small-to-medium feature work. The infrastructure is in place; this is primarily AnthropicProvider rewiring + a tool dispatch loop.

## Decision needed

This is feature work, not a bug fix. Three reasonable paths:

1. **Wire it now** (next session): full agentic loop, the LLM gets to call tools mid-reasoning
2. **Wire only `game_state_read`** as a smaller proof of concept; saves the others for later
3. **Defer indefinitely**: the single-shot reasoning is producing acceptable narratives for the demo and adding tool-use makes responses slower and more expensive

All three are reasonable. The current setup (option 3) ships rich narratives via Haiku 4.5 in well under a second per turn; tool-use would multiply that by N round-trips.
