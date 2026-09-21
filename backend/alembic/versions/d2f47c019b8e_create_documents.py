"""create documents

Revision ID: d2f47c019b8e
Revises: 38c44b86e646
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2f47c019b8e"
down_revision: str | Sequence[str] | None = "38c44b86e646"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("object_key"),
    )


def downgrade() -> None:
    op.drop_table("documents")
