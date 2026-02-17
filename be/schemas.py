from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
import string

class Move(BaseModel):
    start_row: int
    start_col: int
    end_row: int
    end_col: int
    player_id: str

def validate_name(name: str) -> str:
    if not name:
        raise ValueError("Name cannot be empty")
    
    # Check printable
    if not all(c in string.printable for c in name):
        raise ValueError("Name contains invalid characters")
    
    # Check leading/trailing whitespace
    if name != name.strip():
        raise ValueError("Name cannot have leading or trailing whitespace")
        
    # Check length
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long")
        
    return name

class CreateGameRequest(BaseModel):
    player_id: str
    player_name: str
    mode: str = "online" # "online", "cpu", "local"
    
    @field_validator('player_name')
    def name_must_be_valid(cls, v):
        return validate_name(v)

class JoinGameRequest(BaseModel):
    player_id: str
    player_name: str

    @field_validator('player_name')
    def name_must_be_valid(cls, v):
        return validate_name(v)



class GameState(BaseModel):
    id: str
    board: List[List[Optional[str]]]  # 8x8 grid: "r", "b", "R", "B", None
    current_turn: str
    status: str
    winner: Optional[str]
    red_player_id: Optional[str]
    black_player_id: Optional[str]
    red_player_name: Optional[str]
    black_player_name: Optional[str]
    last_move: Optional[dict]
    active_piece: Optional[dict]
    mode: Optional[str] = "online"

    class Config:
        from_attributes = True
