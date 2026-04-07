import pytest
from fastapi.testclient import TestClient

from director_hub.bridge import server as server_module
from director_hub.bridge.server import app
from director_hub.reasoning.engine import ReasoningEngine


@pytest.fixture
def stub_engine() -> ReasoningEngine:
    """Build a ReasoningEngine pinned to the deterministic stub provider.

    Tests must use this rather than `ReasoningEngine()` so they remain
    independent of the production models.yaml — the on-disk default may
    point at a real LLM provider, but tests should not depend on env vars,
    network, or rate limits.
    """
    return ReasoningEngine(config={"active": "stub", "providers": [{"name": "stub"}]})


@pytest.fixture
def client(stub_engine: ReasoningEngine) -> TestClient:
    """TestClient with the global Director Hub engine swapped for a stub.

    The bridge server holds the engine in a module-level global; we
    monkey-patch it here so endpoint tests assert against deterministic
    output instead of whatever provider production config selects.
    """
    original = server_module._engine
    server_module._engine = stub_engine
    try:
        yield TestClient(app)
    finally:
        server_module._engine = original
