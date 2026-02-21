from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
import uuid
from typing import Optional, List, Dict

class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    board_state: Mapped[List[List[Optional[str]]]] = mapped_column(JSONB, nullable=False)
    current_turn: Mapped[str] = mapped_column(String, default="red")
    status: Mapped[str] = mapped_column(String, default="active")
    winner: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    red_player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    black_player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    red_player_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    black_player_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_move: Mapped[Optional[Dict[str, int]]] = mapped_column(JSONB, nullable=True)
    active_piece: Mapped[Optional[Dict[str, int]]] = mapped_column(JSONB, nullable=True)
    mode: Mapped[str] = mapped_column(String, default="online")
    draw_offer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    draw_timer: Mapped[int] = mapped_column(Integer, default=0)
