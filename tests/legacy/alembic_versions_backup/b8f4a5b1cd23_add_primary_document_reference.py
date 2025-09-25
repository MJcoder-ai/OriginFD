import pytest

pytestmark = pytest.mark.xfail(reason="Legacy in-memory lifecycle; superseded by DB-backed model", strict=False)

"""Add primary_document_id to projects

Revision ID: b8f4a5b1cd23
Revises: 8d6c0a521db0
Create Date: 2024-03-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8f4a5b1cd23"
down_revision = "8d6c0a521db0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the primary_document_id foreign key column."""
    op.add_column(
        "projects",
        sa.Column("primary_document_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_primary_document_id_documents",
        "projects",
        "documents",
        ["primary_document_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove the primary_document_id foreign key column."""
    op.drop_constraint(
        "fk_projects_primary_document_id_documents",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "primary_document_id")
