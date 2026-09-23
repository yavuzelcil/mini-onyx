"""add embedding column to document chunks

Revision ID: 0e33771e5bbd
Revises: d73e8c3e5eb8
Create Date: 2026-09-23 13:38:04.056186

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e33771e5bbd"
down_revision: str | Sequence[str] | None = "d73e8c3e5eb8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("document_chunks", sa.Column("embedding", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
