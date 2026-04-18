"""Rule-based chunk content generator. Returns structures, NPCs, encounters, POIs for a chunk."""

import random
from typing import Any


def generate_chunk_content(
    chunk_x: int,
    chunk_z: int,
    biome: str,
    elevation: float,
    temperature: float,
    moisture: float,
    distance_from_spawn: int,
    world_seed: int = 42,
) -> dict[str, Any]:
    """Generate content for a chunk based on biome and location."""
    rng = random.Random(world_seed * 10000 + chunk_x * 1000 + chunk_z)

    structures = []
    npcs = []
    encounter_zones = []
    points_of_interest = []

    # Content density: higher near spawn, sparser in wilderness
    density = max(0.1, 1.0 - distance_from_spawn * 0.1)

    # Biome-specific content
    if biome in ("boreal_forest", "temperate_forest", "tropical_rainforest"):
        if rng.random() < 0.3 * density:
            structures.append(
                {
                    "type": "lumber_camp",
                    "name": f"Camp ({chunk_x},{chunk_z})",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "size": "small",
                }
            )
            npcs.append(
                {
                    "name": "Camp Foreman",
                    "role": "worker",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "faction": "loggers",
                }
            )
        if rng.random() < 0.2 * density:
            points_of_interest.append(
                {
                    "type": "ancient_ruins",
                    "name": "Weathered Stones",
                    "position_x": rng.randint(10, 240),
                    "position_z": rng.randint(10, 240),
                    "discoverable": True,
                }
            )

    elif biome in ("mountain",):
        if rng.random() < 0.2 * density:
            structures.append(
                {
                    "type": "mine_entrance",
                    "name": f"Old Mine ({chunk_x},{chunk_z})",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "size": "small",
                }
            )
        if rng.random() < 0.15 * density:
            structures.append(
                {
                    "type": "watchtower",
                    "name": "Crumbling Tower",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "size": "medium",
                }
            )

    elif biome in ("grassland", "savanna", "arid_steppe"):
        if rng.random() < 0.25 * density:
            structures.append(
                {
                    "type": "farm",
                    "name": f"Homestead ({chunk_x},{chunk_z})",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "size": "small",
                }
            )
            npcs.append(
                {
                    "name": "Farmer",
                    "role": "merchant",
                    "position_x": rng.randint(20, 230),
                    "position_z": rng.randint(20, 230),
                    "faction": "settlers",
                }
            )

    elif biome == "desert":
        if rng.random() < 0.1 * density:
            points_of_interest.append(
                {
                    "type": "oasis",
                    "name": "Desert Oasis",
                    "position_x": rng.randint(10, 240),
                    "position_z": rng.randint(10, 240),
                    "discoverable": True,
                }
            )

    # Encounter zones (all non-ocean biomes)
    if biome not in ("ocean", "ice_sheet", "ice_snow"):
        danger = (
            "low" if distance_from_spawn < 3 else ("medium" if distance_from_spawn < 6 else "high")
        )
        if rng.random() < 0.4 * density:
            encounter_zones.append(
                {
                    "position_x": rng.randint(30, 220),
                    "position_z": rng.randint(30, 220),
                    "radius": 40,
                    "danger_level": danger,
                }
            )

    return {
        "structures": structures,
        "npcs": npcs,
        "encounter_zones": encounter_zones,
        "points_of_interest": points_of_interest,
        "content_source": "director_hub",
    }
