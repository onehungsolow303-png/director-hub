# Director Hub — Agentic AI Brain

The LLM-driven decision engine for the Forever engine RPG. Interprets player free-text actions against engine rules, generates narrative consequences, manages four memory tiers (short / episodic / semantic / long-term), exposes a tool belt the brain can call, and runs an observe→reason→act→reflect execution loop with disk-persisted traces.

**Spec:** `C:\Dev\.shared\docs\superpowers\specs\2026-04-06-three-module-consolidation-design.md`

## What this is NOT

This directory used to contain "Gut It Out", a UI screenshot extractor for video games. That code was archived to `C:\Dev\_archive\gut-it-out\` during the 2026-04-06 three-module pivot. Two pieces (`border_detect/`, `quality_metrics.py`) were salvaged into Asset Manager where they grade AI-generated assets.

## Status

**All spec §14 follow-ups complete.** Director Hub now ships with:

- A working pluggable LLM provider system with `stub` (default, no credentials) and `anthropic` (Claude, requires SDK + API key) providers.
- Four real toolbelt tools: `asset_request` (HTTP to Asset Manager), `dice_resolve` (NdM rolls), `narrative_write` (in-session journal), `game_state_read` (session-scoped engine state cache).
- A real LoopController running the four-phase rhythm with auto-trace.
- Four-tier memory: short-term in-memory, episodic JSONL on disk, semantic JSON on disk, long-term ChromaDB vector store.
- 8 golden eval scenarios + a runner that can be invoked standalone or via pytest.
- A CI workflow that exercises the suite plus a live HTTP smoke test.
- A contract drift detector that catches stale `_generated_schemas.py` against the live `.shared/codegen` output.

## Quick start

```bash
cd "C:/Dev/Director Hub"
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev]"
uvicorn director_hub.bridge.server:app --port 7802
```

```bash
curl http://127.0.0.1:7802/health
# {"status":"ok","service":"director_hub","version":"0.1.0"}
```

To enable the real Claude provider:

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=sk-ant-...
# Edit director_hub/config/models.yaml: change `active: stub` to `active: anthropic`
uvicorn director_hub.bridge.server:app --port 7802
```

To enable ChromaDB long-term memory (persistent vector store):

```bash
pip install -e ".[chroma]"
# No config change needed — LongTermMemory auto-detects chromadb at construction
```

## Tests

```bash
pytest tests/ -v
```

The full suite covers /health, /session/start, /interpret_action, all 8 golden eval scenarios, the reasoning provider system, the toolbelt, the LoopController, the Tracer, and all four memory tiers' persistence.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Liveness check |
| POST | `/session/start` | Open a session, return opening narrative |
| POST | `/interpret_action` | Per-decision: interpret player free-text action |
| POST | `/dialogue` | Generate NPC dialogue |
| POST | `/quest` | Generate dynamic quest |

All payloads validate against `C:\Dev\.shared\schemas\*.schema.json`. The pydantic models in `bridge/schemas.py` are imported from `bridge/_generated_schemas.py`, which is a vendored copy of `.shared/codegen/golden_python.py`. Re-vendor with the protocol in `.shared/README.md`.

## Architecture

```
director_hub/
├── reasoning/
│   ├── engine.py          ReasoningEngine: reads config, dispatches to active provider
│   └── providers/
│       ├── base.py        ReasoningProvider ABC
│       ├── stub.py        Deterministic fallback
│       └── anthropic.py   Claude SDK wrapper, lazy import, key check
├── memory/
│   ├── short_term.py      In-memory chain-of-thought buffer
│   ├── episodic.py        Disk JSONL log per session
│   ├── semantic.py        Disk JSON key/value store
│   ├── long_term.py       ChromaDB vector store w/ in-memory fallback
│   └── manager.py         Unified facade
├── toolbelt/
│   ├── base.py            Tool ABC
│   ├── registry.py        Tool registry
│   ├── asset_tool.py      HTTP -> Asset Manager
│   ├── dice_tool.py       NdM[+/-K] rolls via secrets RNG
│   ├── narrative_tool.py  In-session journal append/read/clear
│   └── game_state_tool.py Session-scoped state cache
├── loop/
│   └── controller.py      observe -> reason -> act -> reflect
├── evals/
│   ├── metrics.py         TSR + tool acc + adherence + ...
│   ├── replay.py          Real-task trace replay
│   ├── runner.py          Standalone CLI for live HTTP eval
│   └── golden/            8 hand-authored scenarios
├── observability/
│   ├── tracer.py          Disk-persisted JSONL traces
│   └── failure_tags.py    FailureTag enum
├── bridge/
│   ├── server.py          FastAPI app on port 7802
│   ├── schemas.py         Re-exports from _generated_schemas + local wrappers
│   └── _generated_schemas.py  Vendored from .shared/codegen/golden_python.py
└── config/
    ├── models.yaml        LLM provider config (active: stub by default)
    └── thresholds.yaml    Eval gate thresholds
```
