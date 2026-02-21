from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from models import Game
from schemas import GameState, Move
import logic
from telemetry import MOVES_MADE, GAMES_ACTIVE
from dependencies import check_move_limit
from .common import to_game_state

router = APIRouter()

@router.post("/{game_id}/move", response_model=GameState, dependencies=[Depends(check_move_limit)])
async def make_move(game_id: str, move: Move, db: AsyncSession = Depends(get_db)):
    # Fetch game
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is finished")
        
    # Validate Player Turn
    if game.current_turn == "red":
        if game.red_player_id and game.red_player_id != move.player_id:
            raise HTTPException(status_code=403, detail="It's Red's turn (not you)")
    elif game.current_turn == "black":
        if game.black_player_id and game.black_player_id != move.player_id:
            raise HTTPException(status_code=403, detail="It's Black's turn (not you)")
    
    # Check if active_piece restriction applies (double jump)
    active_tuple = None
    if game.active_piece:
        active_tuple = (game.active_piece["row"], game.active_piece["col"])
        
    # Validate logic
    if not logic.is_valid_move(game.board_state, move, game.current_turn, active_tuple):
        raise HTTPException(status_code=400, detail="Invalid move")
    
    # Check for Draw Progress (50-move rule)
    # We must check BEFORE applying the move
    piece = game.board_state[move.start_row][move.start_col]
    is_pawn = piece and not piece.isupper()
    is_capture = abs(move.start_row - move.end_row) == 2
    
    if is_pawn or is_capture:
        game.draw_timer = 0
    else:
        # Increment draw timer (1 per half-move)
        # Handle existing None value just in case
        current_timer = game.draw_timer if game.draw_timer is not None else 0
        game.draw_timer = current_timer + 1
        
    flag_modified(game, "draw_timer")

    # Apply move
    new_board, turn_finished, next_active_piece = logic.apply_move(game.board_state, move)
    
    MOVES_MADE.inc()
    
    game.board_state = list(new_board)
    flag_modified(game, "board_state")
    
    # Store last move for highlighting
    game.last_move = {
        "start_row": move.start_row,
        "start_col": move.start_col,
        "end_row": move.end_row,
        "end_col": move.end_col
    }
    flag_modified(game, "last_move")
    
    if turn_finished:
        game.current_turn = "black" if game.current_turn == "red" else "red"
        game.active_piece = None
    else:
        # Multi-jump required
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
