"""Lifecycle gate model extensions."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20240924_0001"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


GATE_STATUS_ENUM = sa.Enum(
    "NOT_STARTED",
    "IN_PROGRESS",
    "BLOCKED",
    "APPROVED",
    "REJECTED",
    name="gate_status",
)

APPROVAL_DECISION_ENUM = sa.Enum("APPROVE", "REJECT", name="approval_decision")


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    json_type = postgresql.JSON(astext_type=sa.Text()) if is_postgres else sa.JSON()
    json_array_default = sa.text("'[]'::jsonb") if is_postgres else sa.text("'[]'")
    json_object_default = sa.text("'{}'::jsonb") if is_postgres else sa.text("'{}'")

    # Create enums if they do not already exist.
    GATE_STATUS_ENUM.create(bind, checkfirst=True)
    APPROVAL_DECISION_ENUM.create(bind, checkfirst=True)

    # --- lifecycle_phases extensions ---
    op.add_column(
        "lifecycle_phases",
        sa.Column("phase_code", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "phase_key",
            sa.String(length=128),
            nullable=False,
            server_default="phase.unknown",
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "title", sa.String(length=256), nullable=False, server_default="Phase"
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "entry_gate_code",
            sa.String(length=16),
            nullable=False,
            server_default="G0",
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "exit_gate_code",
            sa.String(length=16),
            nullable=False,
            server_default="G1",
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "required_entry_roles",
            json_type,
            nullable=False,
            server_default=json_array_default,
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "required_exit_roles",
            json_type,
            nullable=False,
            server_default=json_array_default,
        ),
    )
    op.add_column(
        "lifecycle_phases",
        sa.Column(
            "odl_sd_sections",
            json_type,
            nullable=False,
            server_default=json_array_default,
        ),
    )

    op.create_index(
        "ix_lifecycle_phases_phase_code",
        "lifecycle_phases",
        ["phase_code"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_lifecycle_phases_project_phase_code",
        "lifecycle_phases",
        ["project_id", "phase_code"],
    )
    op.create_index(
        "ix_lifecycle_phases_phase_key", "lifecycle_phases", ["phase_key"], unique=False
    )
    op.create_index(
        "ix_lifecycle_phases_order", "lifecycle_phases", ["order"], unique=False
    )

    op.alter_column("lifecycle_phases", "phase_code", server_default=None)
    op.alter_column("lifecycle_phases", "phase_key", server_default=None)
    op.alter_column("lifecycle_phases", "title", server_default=None)
    op.alter_column("lifecycle_phases", "order", server_default=None)
    op.alter_column("lifecycle_phases", "entry_gate_code", server_default=None)
    op.alter_column("lifecycle_phases", "exit_gate_code", server_default=None)

    # --- lifecycle_gates extensions ---
    op.add_column(
        "lifecycle_gates",
        sa.Column("project_id", sa.UUID(), nullable=False),
    )
    op.add_column(
        "lifecycle_gates",
        sa.Column("phase_code", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "lifecycle_gates",
        sa.Column(
            "gate_code",
            sa.String(length=16),
            nullable=False,
            server_default="G0",
        ),
    )

    op.execute(
        """
        UPDATE lifecycle_gates
        SET status =
            CASE
                WHEN status IS NULL OR status = '' THEN 'NOT_STARTED'
                WHEN LOWER(status) IN ('pending', 'not_started') THEN 'NOT_STARTED'
                WHEN LOWER(status) IN (
                    'in_progress',
                    'in_review',
                    'active'
                ) THEN 'IN_PROGRESS'
                WHEN LOWER(status) IN ('approved', 'completed') THEN 'APPROVED'
                WHEN LOWER(status) = 'blocked' THEN 'BLOCKED'
                WHEN LOWER(status) = 'rejected' THEN 'REJECTED'
                ELSE 'NOT_STARTED'
            END
        """
    )

    op.alter_column(
        "lifecycle_gates",
        "status",
        existing_type=sa.String(),
        type_=GATE_STATUS_ENUM,
        nullable=False,
        server_default="NOT_STARTED",
    )
    op.alter_column(
        "lifecycle_gates",
        "context",
        existing_type=json_type,
        server_default=json_object_default,
        nullable=False,
    )

    op.create_foreign_key(
        "fk_lifecycle_gates_project_id",
        "lifecycle_gates",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.create_index(
        "ix_lifecycle_gates_project_id", "lifecycle_gates", ["project_id"], unique=False
    )
    op.create_index(
        "ix_lifecycle_gates_phase_code", "lifecycle_gates", ["phase_code"], unique=False
    )
    op.create_index(
        "ix_lifecycle_gates_gate_code", "lifecycle_gates", ["gate_code"], unique=False
    )
    op.create_index(
        "ix_lifecycle_gates_status", "lifecycle_gates", ["status"], unique=False
    )
    op.create_unique_constraint(
        "uq_lifecycle_gates_project_phase_gate",
        "lifecycle_gates",
        ["project_id", "phase_code", "gate_code"],
    )

    op.alter_column("lifecycle_gates", "phase_code", server_default=None)
    op.alter_column("lifecycle_gates", "gate_code", server_default=None)

    # --- lifecycle_gate_approvals extensions ---
    op.drop_constraint(
        "lifecycle_gate_approvals_gate_id_key",
        "lifecycle_gate_approvals",
        type_="unique",
    )
    op.drop_constraint(
        "lifecycle_gate_approvals_gate_id_fkey",
        "lifecycle_gate_approvals",
        type_="foreignkey",
    )
    op.add_column(
        "lifecycle_gate_approvals",
        sa.Column("approver_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "lifecycle_gate_approvals",
        sa.Column(
            "role_key",
            sa.String(length=128),
            nullable=False,
            server_default="role.project_manager",
        ),
    )
    op.add_column(
        "lifecycle_gate_approvals",
        sa.Column(
            "decision",
            APPROVAL_DECISION_ENUM,
            nullable=False,
            server_default="APPROVE",
        ),
    )
    op.add_column(
        "lifecycle_gate_approvals",
        sa.Column("comment", sa.Text(), nullable=True),
    )

    op.create_foreign_key(
        "lifecycle_gate_approvals_gate_id_fkey",
        "lifecycle_gate_approvals",
        "lifecycle_gates",
        ["gate_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "lifecycle_gate_approvals_approver_user_id_fkey",
        "lifecycle_gate_approvals",
        "users",
        ["approver_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_lifecycle_gate_approvals_gate_decision_created_at",
        "lifecycle_gate_approvals",
        ["gate_id", "decision", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_lifecycle_gate_approvals_approver_user_id",
        "lifecycle_gate_approvals",
        ["approver_user_id"],
        unique=False,
    )

    op.alter_column("lifecycle_gate_approvals", "role_key", server_default=None)
    op.alter_column("lifecycle_gate_approvals", "decision", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    json_type = postgresql.JSON(astext_type=sa.Text()) if is_postgres else sa.JSON()

    op.drop_index(
        "ix_lifecycle_gate_approvals_approver_user_id",
        table_name="lifecycle_gate_approvals",
    )
    op.drop_index(
        "ix_lifecycle_gate_approvals_gate_decision_created_at",
        table_name="lifecycle_gate_approvals",
    )
    op.drop_constraint(
        "lifecycle_gate_approvals_approver_user_id_fkey",
        "lifecycle_gate_approvals",
        type_="foreignkey",
    )
    op.drop_constraint(
        "lifecycle_gate_approvals_gate_id_fkey",
        "lifecycle_gate_approvals",
        type_="foreignkey",
    )
    op.alter_column(
        "lifecycle_gates",
        "status",
        existing_type=GATE_STATUS_ENUM,
        type_=sa.String(),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "lifecycle_gates",
        "context",
        existing_type=json_type,
        server_default=None,
        nullable=True,
    )

    op.drop_column("lifecycle_gate_approvals", "comment")
    op.drop_column("lifecycle_gate_approvals", "decision")
    op.drop_column("lifecycle_gate_approvals", "role_key")
    op.drop_column("lifecycle_gate_approvals", "approver_user_id")
    op.create_unique_constraint(
        "lifecycle_gate_approvals_gate_id_key",
        "lifecycle_gate_approvals",
        ["gate_id"],
    )
    op.create_foreign_key(
        "lifecycle_gate_approvals_gate_id_fkey",
        "lifecycle_gate_approvals",
        "lifecycle_gates",
        ["gate_id"],
        ["id"],
    )

    op.drop_constraint(
        "uq_lifecycle_gates_project_phase_gate",
        "lifecycle_gates",
        type_="unique",
    )
    op.drop_index("ix_lifecycle_gates_status", table_name="lifecycle_gates")
    op.drop_index("ix_lifecycle_gates_gate_code", table_name="lifecycle_gates")
    op.drop_index("ix_lifecycle_gates_phase_code", table_name="lifecycle_gates")
    op.drop_index("ix_lifecycle_gates_project_id", table_name="lifecycle_gates")
    op.drop_constraint(
        "fk_lifecycle_gates_project_id",
        "lifecycle_gates",
        type_="foreignkey",
    )
    op.drop_column("lifecycle_gates", "gate_code")
    op.drop_column("lifecycle_gates", "phase_code")
    op.drop_column("lifecycle_gates", "project_id")

    op.drop_index("ix_lifecycle_phases_order", table_name="lifecycle_phases")
    op.drop_index("ix_lifecycle_phases_phase_key", table_name="lifecycle_phases")
    op.drop_constraint(
        "uq_lifecycle_phases_project_phase_code",
        "lifecycle_phases",
        type_="unique",
    )
    op.drop_index("ix_lifecycle_phases_phase_code", table_name="lifecycle_phases")
    op.drop_column("lifecycle_phases", "odl_sd_sections")
    op.drop_column("lifecycle_phases", "required_exit_roles")
    op.drop_column("lifecycle_phases", "required_entry_roles")
    op.drop_column("lifecycle_phases", "exit_gate_code")
    op.drop_column("lifecycle_phases", "entry_gate_code")
    op.drop_column("lifecycle_phases", "order")
    op.drop_column("lifecycle_phases", "title")
    op.drop_column("lifecycle_phases", "phase_key")
    op.drop_column("lifecycle_phases", "phase_code")

    APPROVAL_DECISION_ENUM.drop(bind, checkfirst=True)
    GATE_STATUS_ENUM.drop(bind, checkfirst=True)
