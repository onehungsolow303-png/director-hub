"""Toolbelt tests.

Covers all four tools: asset_tool (with httpx mock), dice_tool, narrative_tool,
game_state_tool. Each tool's happy path + at least one failure mode.
"""
from __future__ import annotations

from director_hub.toolbelt.asset_tool import AssetTool
from director_hub.toolbelt.dice_tool import DiceTool
from director_hub.toolbelt.game_state_tool import GameStateTool, remember_request
from director_hub.toolbelt.narrative_tool import NarrativeTool

# ---------------------------------------------------------------- AssetTool


def test_asset_tool_unreachable_returns_error():
    """Without a live Asset Manager, AssetTool falls back gracefully."""
    tool = AssetTool(base_url="http://127.0.0.1:7900", timeout=0.5)  # nothing on 7900
    result = tool.call(kind="sprite", biome="forest")
    assert result["ok"] is False
    assert "unreachable" in result["error"]


# ---------------------------------------------------------------- DiceTool


def test_dice_tool_simple_roll():
    tool = DiceTool()
    result = tool.call(spec="3d6")
    assert result["ok"] is True
    assert result["total"] == sum(result["rolls"])
    assert len(result["rolls"]) == 3
    assert all(1 <= r <= 6 for r in result["rolls"])


def test_dice_tool_with_modifier():
    tool = DiceTool()
    result = tool.call(spec="1d20+5")
    assert result["ok"] is True
    assert result["modifier"] == 5
    assert result["total"] == result["rolls"][0] + 5


def test_dice_tool_with_dc_pass():
    tool = DiceTool()
    result = tool.call(spec="100d6", dc=50)
    assert result["ok"] is True
    assert result["passed"] is True


def test_dice_tool_with_dc_fail():
    tool = DiceTool()
    result = tool.call(spec="1d4", dc=99)
    assert result["ok"] is True
    assert result["passed"] is False


def test_dice_tool_invalid_spec():
    tool = DiceTool()
    result = tool.call(spec="not a dice spec")
    assert result["ok"] is False
    assert "invalid" in result["error"]


def test_dice_tool_out_of_range():
    tool = DiceTool()
    result = tool.call(spec="9999d6")
    assert result["ok"] is False


# ---------------------------------------------------------------- NarrativeTool


def test_narrative_tool_append_and_read():
    tool = NarrativeTool()
    a = tool.call(action="append", actor="player", text="entered the cave")
    assert a["ok"] is True
    assert a["size"] == 1
    b = tool.call(action="append", actor="goblin", text="growled menacingly")
    assert b["size"] == 2

    r = tool.call(action="read", n=10)
    assert r["ok"] is True
    assert len(r["entries"]) == 2
    assert r["entries"][0]["actor"] == "player"
    assert r["entries"][1]["actor"] == "goblin"


def test_narrative_tool_clear():
    tool = NarrativeTool()
    tool.call(action="append", text="x")
    tool.call(action="append", text="y")
    c = tool.call(action="clear")
    assert c["ok"] is True
    assert c["size"] == 0
    r = tool.call(action="read")
    assert r["entries"] == []


def test_narrative_tool_unknown_action():
    tool = NarrativeTool()
    r = tool.call(action="bake")
    assert r["ok"] is False


# ---------------------------------------------------------------- GameStateTool


def test_game_state_tool_returns_cached_snapshot():
    remember_request(
        {
            "session_id": "gs-test-1",
            "actor_id": "player",
            "actor_stats": {"hp": 12, "max_hp": 20},
            "scene_context": {"biome": "swamp"},
        }
    )
    tool = GameStateTool()
    result = tool.call(session_id="gs-test-1")
    assert result["ok"] is True
    assert result["found"] is True
    assert result["snapshot"]["actor_stats"]["hp"] == 12
    assert result["snapshot"]["scene_context"]["biome"] == "swamp"


def test_game_state_tool_unknown_session():
    tool = GameStateTool()
    result = tool.call(session_id="never-seen")
    assert result["ok"] is True
    assert result["found"] is False


def test_game_state_tool_missing_session_id():
    tool = GameStateTool()
    result = tool.call()
    assert result["ok"] is False
