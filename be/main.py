from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from typing import List
import os

from database import engine, get_db, Base
from models import Game
from schemas import GameState, Move, CreateGameRequest, JoinGameRequest
import logic
from fastapi import Request
from rate_limiter import limiter

app = FastAPI(title="Checkers API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "*"], # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def check_create_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_game_create(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")

async def check_move_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_move(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")

async def check_query_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check_query(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again later.")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/games", response_model=GameState, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_create_limit)])
async def create_game(request: CreateGameRequest, db: AsyncSession = Depends(get_db)):
    initial_board = logic.initialize_board()
    new_game = Game(
        board_state=initial_board,
        current_turn="red",
        status="active",
        red_player_id=request.player_id,
        red_player_name=request.player_name,
        black_player_id=None,
        black_player_name=None,
        last_move=None,
        active_piece=None
    )
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)
    return format_game_response(new_game)

@app.post("/games/{game_id}/join", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def join_game(game_id: str, request: JoinGameRequest, db: AsyncSession = Depends(get_db)):
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
        game.black_player_name = request.player_name
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

@app.get("/games/{game_id}", response_model=GameState, dependencies=[Depends(check_query_limit)])
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return format_game_response(game)

@app.post("/games/{game_id}/move", response_model=GameState, dependencies=[Depends(check_move_limit)])
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
        
    # Apply move
    new_board, turn_finished, next_active_piece = logic.apply_move(game.board_state, move)
    
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
        
    await db.commit()
    await db.refresh(game)
    return format_game_response(game)

def format_game_response(game: Game) -> GameState:
    return GameState(
        id=str(game.id),
        board=game.board_state,
        current_turn=game.current_turn,
        status=game.status,
        winner=game.winner,
        red_player_id=game.red_player_id,
        black_player_id=game.black_player_id,
        red_player_name=game.red_player_name,
        black_player_name=game.black_player_name,
        last_move=game.last_move,
        active_piece=game.active_piece
    )

# Serve Frontend
frontend_dist = os.getenv("FRONTEND_DIST")
if frontend_dist and os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in dist (e.g. favicon.ico, etc)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise return index.html
        return FileResponse(os.path.join(frontend_dist, "index.html"))
