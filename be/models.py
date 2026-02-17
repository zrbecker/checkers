from sqlalchemy import Column, String, JSON, Integer
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    board_state = Column(JSON, nullable=False)  # 8x8 grid or list of pieces
    current_turn = Column(String, default="red") # "red" or "black"
    status = Column(String, default="active") # "active", "finished"
    winner = Column(String, nullable=True) # "red", "black", or None
    red_player_id = Column(String, nullable=True)
    black_player_id = Column(String, nullable=True)
    red_player_name = Column(String, nullable=True)
    black_player_name = Column(String, nullable=True)
    last_move = Column(JSON, nullable=True) # {start_row, start_col, end_row, end_col}
    active_piece = Column(JSON, nullable=True) # {row, col} or None
    mode = Column(String, default="online") # "online", "cpu", "local"
    draw_offer = Column(String, nullable=True) # "red", "black", or None
    draw_timer = Column(Integer, default=0) # Half-moves since last pawn move or capture
