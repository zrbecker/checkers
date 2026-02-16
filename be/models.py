from sqlalchemy import Column, Integer, String, JSON
from database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    board_state = Column(JSON, nullable=False)  # 8x8 grid or list of pieces
    current_turn = Column(String, default="red") # "red" or "black"
    status = Column(String, default="active") # "active", "finished"
    winner = Column(String, nullable=True) # "red", "black", or None
    red_player_id = Column(String, nullable=True)
    black_player_id = Column(String, nullable=True)
