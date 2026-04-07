# Director Hub - Agentic AI Brain

The LLM-driven decision engine for Forever engine. Interprets player actions against engine rules, generates narrative consequences, manages four memory tiers, exposes a tool belt the brain can call.

**Spec:** `C:\Dev\.shared\docs\superpowers\specs\2026-04-06-three-module-consolidation-design.md`

## What this is NOT

This directory used to contain "Gut It Out", a UI screenshot extractor. That code has been archived to `C:\Dev\_archive\gut-it-out\`. Two pieces (`border_detect/`, `quality_metrics.py`) were salvaged into Asset Manager where they grade AI-generated assets.

## Status

Phase 1 of the three-module pivot. Currently a **scaffolded service** with stub endpoints. Real reasoning, memory, tools, and evals are follow-up specs.

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

## Tests

```bash
pytest tests/ -v
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | /health | Liveness check |
| POST | /session/start | Open a session, return opening narrative |
| POST | /interpret_action | Per-decision: interpret player action |
| POST | /dialogue | Generate NPC dialogue |
| POST | /quest | Generate dynamic quest |

All response shapes are defined in `C:\Dev\.shared\schemas\`.
