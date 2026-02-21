from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Game
from schemas import GameState, JoinGameRequest
from dependencies import check_query_limit
from .common import to_game_state

router = APIRouter()

@router.post("/{game_id}/join", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def join_game(game_id: str, request: JoinGameRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    # Logic to join or rejoin
    if game.red_player_id == request.player_id:
        return to_game_state(game) # Rejoining as Red
    
    if game.black_player_id == request.player_id:
        return to_game_state(game) # Rejoining as Black
        
    if game.black_player_id is None:
        game.black_player_id = request.player_id
        game.black_player_name = request.player_name
        await db.commit()
        await db.refresh(game)
        return to_game_state(game)
        
    # If red is somehow None (unlikely) but black is taken
    if game.red_player_id is None:
        game.red_player_id = request.player_id
        await db.commit()
        await db.refresh(game)
        return to_game_state(game)
        
    raise HTTPException(status_code=400, detail="Game is full")
