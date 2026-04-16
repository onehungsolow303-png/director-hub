# Director Hub — Claude Code Project Rules

## What This Is
Python/FastAPI agentic AI brain for the Forever engine RPG. Runs on port 7802. Takes player actions + scene context from the C# engine, routes them through an LLM (Claude Haiku 4.5) with tool-use loops, and returns structured DecisionPayload JSON that the engine applies. Part of the four-repo ecosystem after the 2026-04-06 three-module consolidation pivot.

## Architecture
- **Reasoning Engine** (`reasoning/engine.py`) — Provider-based LLM dispatch. Falls back to deterministic stub if credentials are missing.
- **Providers** (`reasoning/providers/`) — `anthropic.py` (live LLM), `stub.py` (deterministic fallback), `record_replay.py` (cassette-based golden-test reproducibility)
- **Toolbelt** (`toolbelt/`) — In-context tools the LLM can call: `dice_tool`, `narrative_tool`, `asset_tool`, `game_state_tool`
- **Memory** (`memory/`) — Short-term (per-session), long-term (ChromaDB), semantic search
- **Bridge** (`bridge/server.py`) — FastAPI HTTP endpoints
- **Evals** (`evals/`) — Golden eval runner + cassettes for reproducible testing
- **Observability** (`observability/`) — Per-request logging, failure tagging

## Repo Ecosystem
- **Forever engine** (`C:\Dev\Forever engine`) — Unity 6 game runtime (the client)
- **Director Hub** (`C:\Dev\Director Hub`) — This repo. Agentic AI brain.
- **Asset Manager** (`C:\Dev\Asset Manager`) — Asset library + generators + AI gateway
- **`.shared`** (`C:\Dev\.shared`) — Cross-module contracts, schemas, codegen

## Rules

1. **Director Hub never writes to the engine.** Returns DecisionPayload JSON; the engine applies it. No direct ECS writes, no file system access to the Unity project.
2. **OAuth token self-heal.** The Anthropic provider re-reads `~/.claude/.credentials.json` on EVERY request so Claude Code's rotating OAuth tokens self-heal without service restart.
3. **Fault boundary on every LLM call.** If the provider raises, fall back to StubProvider for that request. Set `deterministic_fallback=true` on the response so the engine knows.
4. **CassetteMiss propagates in replay mode.** In golden-test replay, a missing cassette is a HARD failure (500), NOT a silent stub fallback. The engine's broad except-Exception handler was masking this — fixed in the CassetteMiss catch-before-generic pattern.
5. **System prompt is the source of truth for LLM behavior.** Physical effects (rest, heal, damage, inn) are documented in the prompt with HARD RULES + few-shot examples. If the LLM drifts, tighten the prompt before adding C# workarounds.
6. **Schemas in `.shared/schemas/` are the contract.** `action.schema.json` defines the request; `decision.schema.json` defines the response. Change the schema first, then update both sides.

## HTTP Endpoints (port 7802)
- `GET /health` — liveness check
- `POST /interpret_action` — core per-decision call (ActionRequest → DecisionPayload)
- `POST /dialogue` — NPC dialogue (same schema as interpret_action)
- `POST /quest` — dynamic quest generation (same schema)
- `POST /session/start` — open a session, return opening narrative

## Config
- `config/models.yaml` — active provider (anthropic/stub), replay_mode (live/record/replay), cassette_dir
- Environment overrides: `DIRECTOR_HUB_REPLAY_MODE`, `DIRECTOR_HUB_CASSETTE_DIR`

## Testing
```bash
cd "C:/Dev/Director Hub"
.venv/Scripts/python.exe -m pytest tests/ -q
# 162 tests, ~6 seconds
```

Golden eval runner:
```bash
.venv/Scripts/python.exe -m director_hub.evals.runner --mode replay
# 8 scenarios, all pass against captured cassettes
```

## Key Files
- `reasoning/providers/anthropic.py` — live LLM provider + system prompt (lines 99-249)
- `reasoning/engine.py` — provider dispatch + record/replay wiring
- `bridge/server.py` — FastAPI app
- `config/models.yaml` — provider + replay configuration
- `evals/cassettes/` — 6 golden-test cassettes
- `evals/runner.py` — eval suite runner
