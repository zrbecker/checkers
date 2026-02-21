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

@router.post("/{game_id}/draw/offer", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def offer_draw(game_id: str, request: GameActionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is finished")

    player_color = None
    if request.player_id == game.red_player_id:
        player_color = "red"
    elif request.player_id == game.black_player_id:
        player_color = "black"
    else:
        raise HTTPException(status_code=403, detail="Not a player in this game")

    # AI Logic: AI always rejects draws immediately (by not setting the offer)
    if game.mode == "cpu":
        return to_game_state(game)

    game.draw_offer = player_color
    await db.commit()
    await db.refresh(game)
    return to_game_state(game)

@router.post("/{game_id}/draw/accept", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def accept_draw(game_id: str, request: GameActionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is finished")

    if not game.draw_offer:
        raise HTTPException(status_code=400, detail="No draw offered")

    # Verify acceptor is the opponent of the offerer
    acceptor_color = None
    if request.player_id == game.red_player_id:
        acceptor_color = "red"
        
    elif request.player_id == game.black_player_id:
        acceptor_color = "black"
    else:
        raise HTTPException(status_code=403, detail="Not a player in this game")

    if game.draw_offer == acceptor_color:
        raise HTTPException(status_code=400, detail="Cannot accept your own draw offer")

    # Accepted!
    game.status = "finished"
    game.winner = "draw"
    game.draw_offer = None
    GAMES_ACTIVE.dec()
    
    await db.commit()
    await db.refresh(game)
    return to_game_state(game)

@router.post("/{game_id}/draw/reject", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def reject_draw(game_id: str, request: GameActionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game.draw_offer:
        # Just return current state if nothing to reject
        return to_game_state(game)

    # Verify rejector is the opponent (or maybe self-cancel?)
    # Let's allow either player to cancel the offer (reject or rescind)
    if request.player_id == game.red_player_id:
        pass
    elif request.player_id == game.black_player_id:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not a player in this game")

    game.draw_offer = None
    await db.commit()
    await db.refresh(game)
    return to_game_state(game)
