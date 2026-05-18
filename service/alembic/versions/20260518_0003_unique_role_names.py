"""add unique role names

Revision ID: 20260518_0003
Revises: 20260518_0002
Create Date: 2026-05-18

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260518_0003"
down_revision: Union[str, None] = "20260518_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
