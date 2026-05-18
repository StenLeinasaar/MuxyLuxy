"""add unique target names

Revision ID: 20260518_0002
Revises: 20250515_0001
Create Date: 2026-05-18

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260518_0002"
down_revision: Union[str, None] = "20250515_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_targets_name"), "targets", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_targets_name"), table_name="targets")
