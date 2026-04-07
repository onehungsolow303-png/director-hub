def test_session_start_returns_session_id_and_opening(client):
    payload = {
        "schema_version": "1.0.0",
        "player_profile": {"name": "Hero", "class": "rogue"},
        "map_meta": {"seed": 12345, "biome": "forest"},
    }
    r = client.post("/session/start", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "session_id" in body and len(body["session_id"]) > 0
    assert body["opening"]["deterministic_fallback"] is True


def test_interpret_action_returns_decision(client):
    payload = {
        "schema_version": "1.0.0",
        "session_id": "test-1",
        "actor_id": "player",
        "target_id": "goblin_01",
        "player_input": "I throw sand in the goblin's eyes",
        "actor_stats": {"hp": 20, "max_hp": 20},
    }
    r = client.post("/interpret_action", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "test-1"
    assert isinstance(body["narrative_text"], str)
    assert body["scale"] in range(1, 11)
    assert body["deterministic_fallback"] is True


def test_interpret_action_rejects_missing_required(client):
    bad = {"schema_version": "1.0.0", "session_id": "x"}
    r = client.post("/interpret_action", json=bad)
    assert r.status_code == 422
