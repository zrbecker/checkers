from pydantic import BaseModel
from typing import List, Optional, Union

class Move(BaseModel):
    start_row: int
    start_col: int
    end_row: int
    end_col: int
    player_id: str

class CreateGameRequest(BaseModel):
    player_id: str

class JoinGameRequest(BaseModel):
    player_id: str


class GameState(BaseModel):
    id: int
    board: List[List[Optional[str]]]  # 8x8 grid: "r", "b", "R", "B", None
    current_turn: str
    status: str
    winner: Optional[str]
    red_player_id: Optional[str]
    black_player_id: Optional[str]

    class Config:
        from_attributes = True
