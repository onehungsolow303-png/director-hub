"""Categorized failure tagging.

Tag categories per spec:
    tool_api_timeout, hallucination_factual, planning_loop, misinterpreted_goal
"""
from __future__ import annotations

from enum import Enum


class FailureTag(Enum):
    TOOL_API_TIMEOUT = "tool_api_timeout"
    HALLUCINATION_FACTUAL = "hallucination_factual"
    PLANNING_LOOP = "planning_loop"
    MISINTERPRETED_GOAL = "misinterpreted_goal"
    UNKNOWN = "unknown"
