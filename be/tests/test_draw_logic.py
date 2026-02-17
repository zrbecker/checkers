import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from main import app
from database import get_db
from models import Game
import logic

# Override DB dependency
async def override_get_db():
    mock_db = AsyncMock()
    yield mock_db

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def mock_game():
    game = MagicMock(spec=Game)
    game.id = "test-game"
    game.status = "active"
    game.current_turn = "red"
    game.winner = None
    game.red_player_id = "p1"
    game.black_player_id = "p2"
    game.red_player_name = "Player 1"
    game.black_player_name = "Player 2"
    game.board_state = logic.initialize_board()
    game.last_move = None
    game.active_piece = None
    game.mode = "online"
    game.draw_offer = None
    game.draw_timer = 0
    return game

@patch("main.flag_modified")
def test_pawn_move_resets_timer(mock_flag_modified, mock_game):
    # Setup Mock DB Session
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_game
    mock_db.execute.return_value = mock_result
    
    # We need to ensure dependency override returns this specific mock_db
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Red Pawn Move: (2, 1) -> (3, 0)
    # This is a valid move for initial board
    payload = {
        "start_row": 2, "start_col": 1,
        "end_row": 3, "end_col": 0,
        "player_id": "p1"
    }
    
    # Set timer to non-zero to verify reset
    mock_game.draw_timer = 50
    
    with patch("logic.is_valid_move", return_value=True):
        res = client.post("/games/test-game/move", json=payload)
    
    assert res.status_code == 200
    assert mock_game.draw_timer == 0

@patch("main.flag_modified")
def test_king_move_increments_timer(mock_flag_modified, mock_game):
    # Setup Mock DB
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_game
    mock_db.execute.return_value = mock_result
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Place a King on board
    board = logic.initialize_board()
    board[3][3] = "R" # Red King
    mock_game.board_state = board
    mock_game.draw_timer = 50
    
    # Move King: (3, 3) -> (4, 4) (Non-capture)
    payload = {
        "start_row": 3, "start_col": 3,
        "end_row": 4, "end_col": 4,
        "player_id": "p1"
    }
    
    with patch("logic.is_valid_move", return_value=True):
        res = client.post("/games/test-game/move", json=payload)
        
    assert res.status_code == 200
    assert mock_game.draw_timer == 51

@patch("main.flag_modified")
def test_draw_condition_reached(mock_flag_modified, mock_game):
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_game
    mock_db.execute.return_value = mock_result
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # King Move, Timer at 99
    board = logic.initialize_board()
    board[3][3] = "R"
    mock_game.board_state = board
    mock_game.draw_timer = 99
    
    payload = {
        "start_row": 3, "start_col": 3,
        "end_row": 4, "end_col": 4,
        "player_id": "p1"
    }
    
    with patch("logic.is_valid_move", return_value=True):
        res = client.post("/games/test-game/move", json=payload)
        
    assert res.status_code == 200
    assert mock_game.draw_timer == 100
    assert mock_game.status == "finished"
    assert mock_game.winner == "draw"

@patch("main.flag_modified")
@patch("main.get_db")
def test_local_mode_resignation(mock_get_db_dep, mock_flag_modified, mock_game):
    # Setup Mock DB Session
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_game
    mock_db.execute.return_value = mock_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Setup local game state
    mock_game.mode = "local"
    mock_game.red_player_id = "p1"
    mock_game.black_player_id = "p1_2"
    
    # Resign as Black (Player 2)
    payload = {"player_id": "p1_2"}
    
    # DEBUG: Call move endpoint to verify DB override
    move_payload = {
        "start_row": 2, "start_col": 1,
        "end_row": 3, "end_col": 0,
        "player_id": "p1"
    }
    with patch("logic.is_valid_move", return_value=True):
        res_move = client.post("/games/test-game/move", json=move_payload)
    print(f"Move endpoint status: {res_move.status_code}")
    if res_move.status_code != 200:
        print(f"Move endpoint response: {res_move.json()}")

    # We are testing the resign endpoint
    res = client.post("/games/test-game/resign", json=payload)
    print(f"Resign endpoint response: {res.json()}")
    
    assert res.status_code == 200
    assert mock_game.status == "finished"
    assert mock_game.winner == "red" # Black resigned, Red wins
