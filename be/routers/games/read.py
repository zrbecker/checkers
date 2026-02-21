from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Game
from schemas import GameState
from dependencies import check_query_limit
from .common import to_game_state

router = APIRouter()

@router.get("/{game_id}", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return to_game_state(game)
