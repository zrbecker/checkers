from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Game
from schemas import GameState, GameActionRequest
from telemetry import GAMES_ACTIVE
from dependencies import check_query_limit
from .common import to_game_state

router = APIRouter()

@router.post("/{game_id}/resign", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def resign_game(game_id: str, request: GameActionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is finished")

    # Determine who is resigning
    winner = None
    if request.player_id == game.red_player_id:
        winner = "black"
    elif request.player_id == game.black_player_id:
        winner = "red"
    else:
        raise HTTPException(status_code=403, detail="Not a player in this game")

    game.status = "finished"
    game.winner = winner
    GAMES_ACTIVE.dec()
    
    await db.commit()
    await db.refresh(game)
    return to_game_state(game)
