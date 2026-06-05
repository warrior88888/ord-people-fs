"""expand post.description and bio.about

Revision ID: a1f2c3d4e5b6
Revises: be657372c2b1
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1f2c3d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'be657372c2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'post',
        'description',
        existing_type=sa.String(length=1000),
        type_=sa.String(length=5000),
        existing_nullable=False,
    )
    op.alter_column(
        'bio',
        'about',
        existing_type=sa.String(length=512),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'bio',
        'about',
        existing_type=sa.String(length=2000),
        type_=sa.String(length=512),
        existing_nullable=True,
    )
    op.alter_column(
        'post',
        'description',
        existing_type=sa.String(length=5000),
        type_=sa.String(length=1000),
        existing_nullable=False,
    )
