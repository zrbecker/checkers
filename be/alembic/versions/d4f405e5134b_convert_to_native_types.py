"""convert_to_native_types

Revision ID: d4f405e5134b
Revises: 81e2fb85546d
Create Date: 2026-02-20 23:22:01.027878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4f405e5134b'
down_revision: Union[str, Sequence[str], None] = '81e2fb85546d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Convert 'id' from String to UUID
    # We use explicit casting with USING
    op.execute(
        "ALTER TABLE games ALTER COLUMN id TYPE uuid USING id::uuid"
    )

    # 2. Convert 'board_state' from JSON to JSONB
    op.execute(
        "ALTER TABLE games ALTER COLUMN board_state TYPE jsonb USING board_state::jsonb"
    )
    
    # 3. Convert 'last_move' from JSON to JSONB
    op.execute(
        "ALTER TABLE games ALTER COLUMN last_move TYPE jsonb USING last_move::jsonb"
    )
    
    # 4. Convert 'active_piece' from JSON to JSONB
    op.execute(
        "ALTER TABLE games ALTER COLUMN active_piece TYPE jsonb USING active_piece::jsonb"
    )


def downgrade() -> None:
    # Reverse the operations
    
    # 1. Convert 'active_piece' back to JSON
    op.execute(
        "ALTER TABLE games ALTER COLUMN active_piece TYPE json USING active_piece::json"
    )

    # 2. Convert 'last_move' back to JSON
    op.execute(
        "ALTER TABLE games ALTER COLUMN last_move TYPE json USING last_move::json"
    )

    # 3. Convert 'board_state' back to JSON
    op.execute(
        "ALTER TABLE games ALTER COLUMN board_state TYPE json USING board_state::json"
    )
    
    # 4. Convert 'id' back to String
    op.execute(
        "ALTER TABLE games ALTER COLUMN id TYPE varchar USING id::text"
    )
