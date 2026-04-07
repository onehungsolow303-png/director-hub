"""Tests for the four Round P fillins: planner, self_correct, rubric, ci_gate."""
from __future__ import annotations

import pytest

from director_hub.evals.ci_gate import CIGate
from director_hub.evals.rubric import Rubric
from director_hub.loop.self_correct import SelfCorrector
from director_hub.observability.failure_tags import FailureTag
from director_hub.reasoning.planner import Planner


# ---------------------------------------------------------------- Planner


def test_planner_attack_goal():
    plan = Planner().plan("I attack the goblin")
    assert len(plan) >= 2
    tool_names = [step["tool"] for step in plan]
    assert "dice_resolve" in tool_names
    assert "game_state_read" in tool_names


def test_planner_dialogue_goal():
    plan = Planner().plan("I want to speak to the innkeeper")
    tool_names = [step["tool"] for step in plan]
    assert "narrative_write" in tool_names


def test_planner_search_goal():
    plan = Planner().plan("I look around the room")
    tool_names = [step["tool"] for step in plan]
    assert "dice_resolve" in tool_names


def test_planner_unknown_goal_returns_fallback():
    plan = Planner().plan("xkcd quantum tortilla recursion")
    assert len(plan) >= 1
    tool_names = [step["tool"] for step in plan]
    assert "narrative_write" in tool_names


def test_planner_returns_independent_dicts():
    """Mutating one returned step should not affect a subsequent plan() call."""
    p = Planner()
    plan1 = p.plan("I attack the goblin")
    plan1[0]["mutated"] = True
    plan2 = p.plan("I attack the goblin")
    assert "mutated" not in plan2[0]


# ---------------------------------------------------------------- SelfCorrector


def test_self_correct_does_not_replan_on_clean_result():
    sc = SelfCorrector()
    result = {
        "narrative_text": "the goblin falls",
        "scale": 6,
        "success": True,
    }
    assert sc.should_replan(result) is False


def test_self_correct_replans_on_empty_narrative():
    sc = SelfCorrector()
    result = {"narrative_text": "", "scale": 5}
    assert sc.should_replan(result) is True


def test_self_correct_replans_on_whitespace_narrative():
    sc = SelfCorrector()
    result = {"narrative_text": "   ", "scale": 5}
    assert sc.should_replan(result) is True


def test_self_correct_replans_on_out_of_range_scale():
    sc = SelfCorrector()
    result = {"narrative_text": "ok", "scale": 99}
    assert sc.should_replan(result) is True
    result_low = {"narrative_text": "ok", "scale": 0}
    assert sc.should_replan(result_low) is True


def test_self_correct_replans_on_recoverable_failure_tag():
    sc = SelfCorrector()
    result = {
        "narrative_text": "ok",
        "scale": 5,
        "failure_tag": FailureTag.TOOL_API_TIMEOUT.value,
    }
    assert sc.should_replan(result) is True


def test_self_correct_replans_on_non_dict_input():
    sc = SelfCorrector()
    assert sc.should_replan("not a dict") is True
    assert sc.should_replan(None) is True


# ---------------------------------------------------------------- Rubric


def test_rubric_empty_trace_scores_zero():
    assert Rubric().score([]) == 0.0


def test_rubric_full_clean_trace_scores_one():
    trace = [
        {"phase": "observe"},
        {"phase": "reason+act"},
        {"phase": "reflect"},
    ]
    assert Rubric().score(trace) == pytest.approx(1.0)


def test_rubric_failure_tag_loses_bonus():
    trace = [
        {"phase": "observe"},
        {"phase": "reason+act"},
        {"phase": "reflect", "failure_tag": "tool_api_timeout"},
    ]
    score = Rubric().score(trace)
    assert score == pytest.approx(0.9)  # 0.2 + 0.5 + 0.2, no bonus


def test_rubric_partial_phases_partial_score():
    trace = [
        {"phase": "observe"},
        {"phase": "reason+act"},
    ]
    score = Rubric().score(trace)
    assert score == pytest.approx(0.7)  # 0.2 + 0.5


def test_rubric_explain_returns_breakdown():
    trace = [
        {"phase": "observe"},
        {"phase": "reason+act"},
        {"phase": "reflect", "failure_tag": "tool_api_timeout"},
    ]
    explain = Rubric().explain(trace)
    assert explain["score"] == pytest.approx(0.9)
    assert "observe" in explain["phases_seen"]
    assert "tool_api_timeout" in explain["failures"]


# ---------------------------------------------------------------- CIGate


def test_ci_gate_passes_clean_metrics():
    gate = CIGate()
    baseline = {"task_success_rate": 0.9, "latency_ms": 100}
    current = {"task_success_rate": 0.91, "latency_ms": 95}
    passed, msg = gate.check(baseline, current)
    assert passed is True
    assert "passed" in msg


def test_ci_gate_blocks_on_tsr_drop():
    gate = CIGate()
    baseline = {"task_success_rate": 0.9}
    current = {"task_success_rate": 0.7}
    passed, msg = gate.check(baseline, current)
    assert passed is False
    assert "task_success_rate" in msg


def test_ci_gate_blocks_on_latency_rise():
    gate = CIGate()
    baseline = {"latency_ms": 100}
    current = {"latency_ms": 500}
    passed, msg = gate.check(baseline, current)
    assert passed is False
    assert "latency" in msg


def test_ci_gate_blocks_on_hallucination():
    gate = CIGate()
    baseline = {}
    current = {"hallucination_rate": 0.2}
    passed, msg = gate.check(baseline, current)
    assert passed is False
    assert "hallucination" in msg


def test_ci_gate_combines_problems():
    gate = CIGate()
    baseline = {"task_success_rate": 0.9, "latency_ms": 100}
    current = {"task_success_rate": 0.7, "latency_ms": 600, "hallucination_rate": 0.5}
    passed, msg = gate.check(baseline, current)
    assert passed is False
    assert "task_success_rate" in msg
    assert "latency" in msg
    assert "hallucination" in msg


def test_ci_gate_constructor_overrides():
    gate = CIGate(tsr_drop_threshold=0.5, latency_increase_ms=1000)
    baseline = {"task_success_rate": 0.9, "latency_ms": 100}
    current = {"task_success_rate": 0.6, "latency_ms": 800}
    passed, msg = gate.check(baseline, current)
    # 0.3 drop is within 0.5 tolerance, 700ms rise within 1000ms tolerance
    assert passed is True
