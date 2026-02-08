"""add user management fields

Revision ID: a1b2c3d4e5f6
Revises: e33bb845793c
Create Date: 2026-02-08 09:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e33bb845793c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add locked_until column
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    
    # Add verification_token column with index
    op.add_column('users', sa.Column('verification_token', sa.String(), nullable=True))
    op.create_index('ix_users_verification_token', 'users', ['verification_token'], unique=True)


def downgrade() -> None:
    # Remove index and column
    op.drop_index('ix_users_verification_token', table_name='users')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'locked_until')
