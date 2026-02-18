import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from main import app
from database import get_db

# Override DB dependency
async def override_get_db():
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    yield mock_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

MOCKED_START_TIME = 1000000.0

@pytest.fixture
def mock_rate_limiter_time():
    """
    Patches time.time in the rate_limiter module.
    Returns a simple class to control time.
    """
    with patch("rate_limiter.time.time") as mock_time:
        mock_time.return_value = MOCKED_START_TIME
        yield mock_time

@pytest.fixture(autouse=True)
def reset_limiter(mock_rate_limiter_time):
    from rate_limiter import limiter
    
    # 1. Sync global buckets to mocked start time
    buckets = [limiter.global_game_create, limiter.global_move, limiter.global_query]
    
    for bucket in buckets:
        bucket.tokens = float(bucket.capacity)
        bucket.last_update = MOCKED_START_TIME
        
    # 2. Clear session buckets
    limiter.session_game_create.clear()
    limiter.session_move.clear()
    limiter.session_query.clear()

def test_game_create_rate_limit(mock_rate_limiter_time):
    payload = {"player_id": "p1", "player_name": "PlayerOne", "mode": "online"}
    
    # --- T = 0 ---
    # Request 1-5: Should pass (5 capacity)
    for i in range(5):
        res = client.post("/games", json=payload)
        # We expect success (201 or similar), definitely not 429
        # If DB fails (mocked), it might be 500/400, but not 429
        assert res.status_code != 429

    # Request 6: Should fail immediately (still T=0, tokens depleted)
    res = client.post("/games", json=payload)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]
    
    # --- T = 2.1s (Advance time) ---
    # The bucket refills at 0.5 token/sec. Need 1 token.
    # 2 seconds = 1.0 token.
    mock_rate_limiter_time.return_value = MOCKED_START_TIME + 2.1
    
    # Request 7: Should pass now
    res = client.post("/games", json=payload)
    assert res.status_code != 429

def test_move_rate_limit(mock_rate_limiter_time):
    payload = {
        "start_row": 0, "start_col": 0, 
        "end_row": 1, "end_col": 1, 
        "player_id": "p1"
    }
    game_id = "test-game"
    
    # --- T = 0 ---
    # Request 1-10: Pass (10 capacity)
    for i in range(10):
        res = client.post(f"/games/{game_id}/move", json=payload)
        assert res.status_code != 429
        
    # Request 11: Fail
    res = client.post(f"/games/{game_id}/move", json=payload)
    assert res.status_code == 429
    
    # --- T = 0.51s ---
    # Refill rate 2.0/sec => 0.5s for 1 token.
    mock_rate_limiter_time.return_value = MOCKED_START_TIME + 0.51
    
    # Request 12: Pass
    res = client.post(f"/games/{game_id}/move", json=payload)
    assert res.status_code != 429

def test_query_rate_limit(mock_rate_limiter_time):
    game_id = "test-game"
    
    # Session limit is 20 capacity
    # Refill rate is 10 tokens / sec => 1 token every 0.1s
    
    # --- T = 0 ---
    # Consume all 20 tokens
    for i in range(20):
        res = client.get(f"/games/{game_id}")
        assert res.status_code != 429
            
    # 21st Request: Fail (Empty bucket)
    res = client.get(f"/games/{game_id}")
    assert res.status_code == 429
    
    # --- T = 0.05s ---
    # Advance time by 0.05s. Tokens refilled = 0.05 * 10 = 0.5 tokens.
    # Should still fail (need 1.0 token)
    mock_rate_limiter_time.return_value = MOCKED_START_TIME + 0.05
    res = client.get(f"/games/{game_id}")
    assert res.status_code == 429
    
    # --- T = 0.11s ---
    # Advance time to 0.11s total. Tokens refilled = 0.11 * 10 = 1.1 tokens.
    # Should succeed now
    mock_rate_limiter_time.return_value = MOCKED_START_TIME + 0.11
    res = client.get(f"/games/{game_id}")
    assert res.status_code != 429
