from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from typing import List

from database import engine, get_db, Base
from models import Game
from schemas import GameState, Move, CreateGameRequest, JoinGameRequest
import logic

app = FastAPI(title="Checkers API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "*"], # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/games", response_model=GameState, status_code=status.HTTP_201_CREATED)
async def create_game(request: CreateGameRequest, db: AsyncSession = Depends(get_db)):
    initial_board = logic.initialize_board()
    new_game = Game(
        board_state=initial_board,
        current_turn="red",
        status="active",
        red_player_id=request.player_id,
        black_player_id=None
    )
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    return format_game_response(new_game)

@app.post("/games/{game_id}/join", response_model=GameState)
async def join_game(game_id: int, request: JoinGameRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    # Logic to join or rejoin
    if game.red_player_id == request.player_id:
        return format_game_response(game) # Rejoining as Red
    
    if game.black_player_id == request.player_id:
        return format_game_response(game) # Rejoining as Black
        
    if game.black_player_id is None:
        game.black_player_id = request.player_id
        await db.commit()
        await db.refresh(game)
        return format_game_response(game)
        
    # If red is somehow None (unlikely) but black is taken
    if game.red_player_id is None:
        game.red_player_id = request.player_id
        await db.commit()
        await db.refresh(game)
        return format_game_response(game)
        
    raise HTTPException(status_code=400, detail="Game is full")

@app.get("/games/{game_id}", response_model=GameState)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return format_game_response(game)

@app.post("/games/{game_id}/move", response_model=GameState)
async def make_move(game_id: int, move: Move, db: AsyncSession = Depends(get_db)):
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
            
    # Validate logic
    if not logic.is_valid_move(game.board_state, move, game.current_turn):
        raise HTTPException(status_code=400, detail="Invalid move")
        
    # Apply move
    new_board, turn_finished = logic.apply_move(game.board_state, move)
    
    game.board_state = list(new_board)
    flag_modified(game, "board_state")
    
    if turn_finished:
        game.current_turn = "black" if game.current_turn == "red" else "red"
        
    # Check winner
    winner = logic.check_winner(game.board_state, game.current_turn)
    if winner:
        game.status = "finished"
        game.winner = winner
        
    await db.commit()
    await db.refresh(game)
    return format_game_response(game)

def format_game_response(game: Game) -> GameState:
    return GameState(
        id=game.id,
        board=game.board_state,
        current_turn=game.current_turn,
        status=game.status,
        winner=game.winner,
        red_player_id=game.red_player_id,
        black_player_id=game.black_player_id
    )
