from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from models import Game
from schemas import GameState
import logic
from telemetry import MOVES_MADE, GAMES_ACTIVE
from dependencies import check_move_limit
from .common import to_game_state

router = APIRouter()

@router.post("/{game_id}/ai-move", response_model=GameState, dependencies=[Depends(check_move_limit)])
async def make_ai_move(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is finished")
        
    # Verify it is AI turn
    if game.mode != "cpu":
        raise HTTPException(status_code=400, detail="Not a CPU game")
        
    # Assume CPU is always Black for now
    if game.current_turn != "black":
        raise HTTPException(status_code=400, detail="Not CPU's turn")
        
    # Check active piece
    active_tuple = None
    if game.active_piece:
        active_tuple = (game.active_piece["row"], game.active_piece["col"])
        
    # Get AI move
    move_dict = logic.get_random_move(game.board_state, "black", active_tuple)
    
    if not move_dict:
        # No moves available -> CPU loses
        game.status = "finished"
        game.winner = "red"
        GAMES_ACTIVE.dec()
        await db.commit()
        await db.refresh(game)
        return to_game_state(game)
        
    # Check for Draw Progress (50-move rule)
    sr, sc = move_dict["start_row"], move_dict["start_col"]
    er, _ = move_dict["end_row"], move_dict["end_col"]
    
    piece = game.board_state[sr][sc]
    is_pawn = piece and not piece.isupper()
    is_capture = abs(sr - er) == 2
    
    if is_pawn or is_capture:
        game.draw_timer = 0
    else:
        # Increment draw timer
        current_timer = game.draw_timer if game.draw_timer is not None else 0
        game.draw_timer = current_timer + 1
    
    flag_modified(game, "draw_timer")
        
    # Apply move
    new_board, turn_finished, next_active_piece = logic.apply_move(game.board_state, move_dict)
    
    MOVES_MADE.inc()
    
    game.board_state = list(new_board)
    flag_modified(game, "board_state")
    
    game.last_move = move_dict
    flag_modified(game, "last_move")
    
    if turn_finished:
        game.current_turn = "red"
        game.active_piece = None
    else:
        if next_active_piece:
            game.active_piece = {"row": next_active_piece[0], "col": next_active_piece[1]}
            flag_modified(game, "active_piece")
            
    # Check winner
    winner = logic.check_winner(game.board_state, game.current_turn)
    if winner:
        game.status = "finished"
        game.winner = winner
        GAMES_ACTIVE.dec()
    # Check for Draw (50-move rule -> 100 half-moves)
    # Reduced to 50 half-moves per user request
    elif game.draw_timer >= 50:
        game.status = "finished"
        game.winner = "draw"
        GAMES_ACTIVE.dec()
        
    await db.commit()
    await db.refresh(game)
    return to_game_state(game)
