import os

# Use a specific port for testing to avoid conflicts
os.environ["METRICS_PORT"] = "9099"

from fastapi.testclient import TestClient
from main import app
from prometheus_client import REGISTRY

client = TestClient(app)

def test_metrics_no_longer_exposed_on_api():
    """Verify /metrics is NOT on port 8080"""
    response = client.get("/metrics")
    assert response.status_code == 404

def test_metrics_recorded_internally():
    """Verify metrics are actually being recorded in the registry"""
    # Trigger a request to ensure instrumentator hooks run
    client.get("/docs")
    
    # Collect all metric names
    metric_names = [m.name for m in REGISTRY.collect()]
    print(f"Found metrics: {metric_names}")
    
    # Verify our custom business metrics are present
    # Note: prometheus_client might strip _total suffix in internal representation
    assert "checkers_games_active" in metric_names
    assert "checkers_games_created" in metric_names
    
    # Verify DB metrics
    assert "checkers_db_queries" in metric_names
    
    # Verify standard HTTP metrics (instrumentator usually adds these)
    # We check for partial match as names can vary
    assert any("http_" in m for m in metric_names)
