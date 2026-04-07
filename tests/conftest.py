import pytest
from fastapi.testclient import TestClient

from director_hub.bridge.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
