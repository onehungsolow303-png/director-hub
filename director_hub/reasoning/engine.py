"""Reasoning Engine - the LLM that interprets player input.

Reads the active provider from `director_hub/config/models.yaml` and dispatches
to it. Falls back to the StubProvider if the active provider can't be
initialized (missing SDK, missing API key, etc.) so the engine never crashes
on missing credentials — the bridge will return a deterministic-fallback
DecisionPayload instead.

Config example (`director_hub/config/models.yaml`):

    providers:
      - name: anthropic
        model: claude-sonnet-4-5
        max_tokens: 1024
      - name: stub
    active: anthropic   # falls back to stub if anthropic fails to initialize
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .providers.base import ReasoningProvider
from .providers.stub import StubProvider

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "models.yaml"
)


class ReasoningEngine:
    def __init__(self, config: dict[str, Any] | None = None, config_path: Path | None = None) -> None:
        self.config = config or _load_config(config_path or _DEFAULT_CONFIG_PATH)
        self._provider: ReasoningProvider = _build_provider(self.config)
        logger.info(
            f"[ReasoningEngine] active provider: {self._provider.name} "
            f"(real={self._provider.is_real})"
        )

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def provider_is_real(self) -> bool:
        return self._provider.is_real

    def interpret(self, action_request: dict[str, Any]) -> dict[str, Any]:
        try:
            inner = self._provider.interpret(action_request)
        except Exception as e:  # boundary - fall back to stub on any provider error
            logger.warning(
                f"[ReasoningEngine] provider {self._provider.name} failed: {e}. "
                "Falling back to stub for this request."
            )
            inner = StubProvider().interpret(action_request)
            self._provider_failed_once = True

        return {
            "schema_version": "1.0.0",
            "session_id": action_request.get("session_id", ""),
            "success": inner.get("success", True),
            "scale": int(inner.get("scale", 5)),
            "narrative_text": str(inner.get("narrative_text", "")),
            "stat_effects": inner.get("stat_effects") or [],
            "fx_requests": inner.get("fx_requests") or [],
            "repetition_penalty": int(inner.get("repetition_penalty", 0)),
            "deterministic_fallback": not self._provider.is_real,
        }


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"providers": [{"name": "stub"}], "active": "stub"}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        logger.warning(f"[ReasoningEngine] failed to load {path}: {e}; using stub.")
        return {"providers": [{"name": "stub"}], "active": "stub"}


def _build_provider(config: dict[str, Any]) -> ReasoningProvider:
    """Resolve the active provider name to a ReasoningProvider instance.

    Falls back to StubProvider on any failure (missing SDK, missing key,
    unknown name, ProviderUnavailable raised during construction).
    """
    active_name = config.get("active", "stub")
    providers_cfg = {p.get("name"): p for p in config.get("providers", []) if isinstance(p, dict)}
    active_cfg = providers_cfg.get(active_name, {})

    if active_name == "stub":
        return StubProvider()

    if active_name == "anthropic":
        try:
            from .providers.anthropic import AnthropicProvider, ProviderUnavailable
        except ImportError as e:
            logger.warning(
                f"[ReasoningEngine] anthropic provider import failed: {e}. Using stub."
            )
            return StubProvider()
        try:
            return AnthropicProvider(
                model=active_cfg.get("model", "claude-sonnet-4-5"),
                max_tokens=int(active_cfg.get("max_tokens", 1024)),
            )
        except ProviderUnavailable as e:
            logger.warning(
                f"[ReasoningEngine] anthropic provider unavailable: {e}. Using stub."
            )
            return StubProvider()

    logger.warning(
        f"[ReasoningEngine] unknown provider '{active_name}'. Using stub."
    )
    return StubProvider()
