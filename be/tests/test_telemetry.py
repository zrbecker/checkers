import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, MagicMock

# We need to mock get_db again as previous test setup might leak or be separate
# But since tests are run separately usually, it's fine.
# However, if running all tests, we should be careful.

client = TestClient(app)

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "checkers_games_created_total" in response.text
