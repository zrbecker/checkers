from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Game
from schemas import GameState, CreateGameRequest
import logic
from telemetry import GAMES_CREATED, GAMES_ACTIVE
from dependencies import check_create_limit
from .common import to_game_state

router = APIRouter()

@router.post("", response_model=GameState, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_create_limit)])
async def create_game(request: CreateGameRequest, db: AsyncSession = Depends(get_db)):
    initial_board = logic.initialize_board()
    
    black_player_id = None
    black_player_name = None
    
    if request.mode == "cpu":
        black_player_id = "CPU"
        black_player_name = "Computer"
    elif request.mode == "local":
        black_player_id = f"{request.player_id}_2"
        black_player_name = request.player2_name if request.player2_name else "Player 2"
    
    new_game = Game(
        board_state=initial_board,
        current_turn="red",
        status="active",
        red_player_id=request.player_id,
        red_player_name=request.player_name,
        black_player_id=black_player_id,
        black_player_name=black_player_name,
        last_move=None,
        active_piece=None,
        mode=request.mode
    )
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    
    # Telemetry
    GAMES_CREATED.inc()
    GAMES_ACTIVE.inc()
    
    return to_game_state(new_game)
