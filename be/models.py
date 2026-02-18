from sqlalchemy import String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
import uuid
from typing import Optional, List, Dict

def generate_uuid():
    return str(uuid.uuid4())

class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid, index=True)
    board_state: Mapped[List[List[Optional[str]]]] = mapped_column(JSON, nullable=False)
    current_turn: Mapped[str] = mapped_column(String, default="red")
    status: Mapped[str] = mapped_column(String, default="active")
    winner: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    red_player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    black_player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    red_player_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    black_player_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_move: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    active_piece: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    mode: Mapped[str] = mapped_column(String, default="online")
    draw_offer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    draw_timer: Mapped[int] = mapped_column(Integer, default=0)
