"""create lifecycle phase and gate tables

Revision ID: 8d6c0a521db0
Revises: de1cf7c4075a
Create Date: 2024-04-08 00:00:00.000000

"""

from __future__ import annotations

import uuid
from typing import List

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8d6c0a521db0"
down_revision = "de1cf7c4075a"
branch_labels = None
depends_on = None


DEFAULT_LIFECYCLE_TEMPLATE = [
    {
        "key": "design",
        "name": "Design",
        "status": "not_started",
        "gates": [
            {
                "key": "site_assessment",
                "name": "Site Assessment",
                "status": "not_started",
            },
            {"key": "bom_approval", "name": "BOM Approval", "status": "not_started"},
        ],
    },
    {
        "key": "procurement",
        "name": "Procurement",
        "status": "not_started",
        "gates": [
            {
                "key": "supplier_selection",
                "name": "Supplier Selection",
                "status": "not_started",
            },
            {
                "key": "contract_signed",
                "name": "Contract Signed",
                "status": "not_started",
            },
        ],
    },
    {
        "key": "construction",
        "name": "Construction",
        "status": "not_started",
        "gates": [
            {"key": "mobilization", "name": "Mobilization", "status": "not_started"},
        ],
    },
]


def upgrade() -> None:
    op.create_table(
        "lifecycle_phases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'not_started'"),
        ),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "project_id",
            "key",
            name="uq_lifecycle_phases_project_key",
        ),
    )

    op.create_table(
        "lifecycle_gates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "phase_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lifecycle_phases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'not_started'"),
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "phase_id",
            "key",
            name="uq_lifecycle_gates_phase_key",
        ),
    )

    op.create_index(
        "ix_lifecycle_phases_project_id",
        "lifecycle_phases",
        ["project_id"],
    )
    op.create_index(
        "ix_lifecycle_gates_project_id",
        "lifecycle_gates",
        ["project_id"],
    )
    op.create_index(
        "ix_lifecycle_gates_phase_id",
        "lifecycle_gates",
        ["phase_id"],
    )

    conn = op.get_bind()
    project_ids = [
        row[0] for row in conn.execute(sa.text("SELECT id FROM projects")).fetchall()
    ]

    if not project_ids:
        return

    phase_table = sa.table(
        "lifecycle_phases",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("project_id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("status", sa.String()),
        sa.column("position", sa.Integer()),
    )
    gate_table = sa.table(
        "lifecycle_gates",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("project_id", postgresql.UUID(as_uuid=True)),
        sa.column("phase_id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String()),
        sa.column("name", sa.String()),
        sa.column("status", sa.String()),
        sa.column("position", sa.Integer()),
    )

    phase_rows: List[dict] = []
    gate_rows: List[dict] = []

    for project_id in project_ids:
        for phase_index, phase_template in enumerate(
            DEFAULT_LIFECYCLE_TEMPLATE, start=1
        ):
            phase_id = uuid.uuid4()
            phase_rows.append(
                {
                    "id": phase_id,
                    "project_id": project_id,
                    "key": phase_template["key"],
                    "name": phase_template["name"],
                    "status": phase_template.get("status", "not_started"),
                    "position": phase_index,
                }
            )

            for gate_index, gate_template in enumerate(
                phase_template.get("gates", []), start=1
            ):
                gate_rows.append(
                    {
                        "id": uuid.uuid4(),
                        "project_id": project_id,
                        "phase_id": phase_id,
                        "key": gate_template["key"],
                        "name": gate_template["name"],
                        "status": gate_template.get("status", "not_started"),
                        "position": gate_index,
                    }
                )

    if phase_rows:
        op.bulk_insert(phase_table, phase_rows)
    if gate_rows:
        op.bulk_insert(gate_table, gate_rows)


def downgrade() -> None:
    op.drop_index("ix_lifecycle_gates_phase_id", table_name="lifecycle_gates")
    op.drop_index("ix_lifecycle_gates_project_id", table_name="lifecycle_gates")
    op.drop_index("ix_lifecycle_phases_project_id", table_name="lifecycle_phases")
    op.drop_table("lifecycle_gates")
    op.drop_table("lifecycle_phases")
