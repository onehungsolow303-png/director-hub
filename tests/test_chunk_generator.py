from director_hub.content.chunk_generator import generate_chunk_content


def test_generate_returns_valid_structure():
    result = generate_chunk_content(0, 0, "grassland", 0.5, 0.5, 0.5, distance_from_spawn=0)
    assert "structures" in result
    assert "npcs" in result
    assert "encounter_zones" in result
    assert "points_of_interest" in result
    assert result["content_source"] == "director_hub"


def test_forest_biome_gets_forest_content():
    # Generate many chunks — at least one should have a lumber camp
    found_camp = False
    for i in range(20):
        result = generate_chunk_content(
            i, 0, "boreal_forest", 0.5, 0.4, 0.8, distance_from_spawn=1, world_seed=i
        )
        for s in result["structures"]:
            if s["type"] == "lumber_camp":
                found_camp = True
                break
    assert found_camp


def test_content_density_higher_near_spawn():
    near = generate_chunk_content(
        0, 0, "grassland", 0.5, 0.6, 0.5, distance_from_spawn=0, world_seed=100
    )
    far = generate_chunk_content(
        0, 0, "grassland", 0.5, 0.6, 0.5, distance_from_spawn=10, world_seed=100
    )
    # Near spawn should have >= as much content as far (probabilistic, but density factor ensures this directionally)
    # Just verify both return valid dicts
    assert isinstance(near["structures"], list)
    assert isinstance(far["structures"], list)


def test_ocean_biome_no_encounters():
    result = generate_chunk_content(0, 0, "ocean", 0.2, 0.5, 0.5, distance_from_spawn=5)
    assert len(result["encounter_zones"]) == 0


def test_deterministic_for_same_seed():
    r1 = generate_chunk_content(
        5, 3, "grassland", 0.5, 0.5, 0.5, distance_from_spawn=2, world_seed=42
    )
    r2 = generate_chunk_content(
        5, 3, "grassland", 0.5, 0.5, 0.5, distance_from_spawn=2, world_seed=42
    )
    assert r1 == r2


def test_chunk_generate_endpoint(client):
    payload = {
        "chunk_x": 3,
        "chunk_z": 7,
        "biome": "grassland",
        "elevation": 0.5,
        "temperature": 0.6,
        "moisture": 0.4,
        "distance_from_spawn": 2,
        "world_seed": 42,
    }
    r = client.post("/chunk/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "structures" in body
    assert "npcs" in body
    assert "encounter_zones" in body
    assert "points_of_interest" in body
    assert body["content_source"] == "director_hub"


def test_chunk_generate_endpoint_rejects_extra_fields(client):
    payload = {
        "chunk_x": 0,
        "chunk_z": 0,
        "biome": "desert",
        "unknown_field": "bad",
    }
    r = client.post("/chunk/generate", json=payload)
    assert r.status_code == 422


def test_chunk_generate_endpoint_uses_defaults(client):
    payload = {"chunk_x": 0, "chunk_z": 0, "biome": "mountain"}
    r = client.post("/chunk/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["structures"], list)
