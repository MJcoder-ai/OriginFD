"""add_lifecycle_and_enhanced_component_fields

Revision ID: de1cf7c4075a
Revises: 752df9eaede8
Create Date: 2025-09-12 06:02:43.388226

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Text

# revision identifiers, used by Alembic.
revision = "de1cf7c4075a"
down_revision = "752df9eaede8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to components table for Phase 1 ODL-SD v4.1 compliance
    op.add_column(
        "components", sa.Column("lifecycle_stage", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "components",
        sa.Column("inventory_managed", sa.Boolean(), nullable=True, default=False),
    )
    op.add_column(
        "components",
        sa.Column("compliance_status", sa.String(length=20), nullable=True),
    )
    op.add_column("components", sa.Column("warranty_details", sa.JSON(), nullable=True))
    op.add_column("components", sa.Column("voltage_v", sa.Float(), nullable=True))
    op.add_column("components", sa.Column("current_a", sa.Float(), nullable=True))
    op.add_column("components", sa.Column("efficiency", sa.Float(), nullable=True))
    op.add_column("components", sa.Column("energy_kwh", sa.Float(), nullable=True))
    op.add_column("components", sa.Column("dimensions", sa.JSON(), nullable=True))
    op.add_column("components", sa.Column("weight_kg", sa.Float(), nullable=True))
    op.add_column("components", sa.Column("certification", sa.JSON(), nullable=True))
    op.add_column(
        "components", sa.Column("warranty_years", sa.Integer(), nullable=True)
    )

    # Add indexes for new fields
    op.create_index("ix_components_lifecycle_stage", "components", ["lifecycle_stage"])
    op.create_index(
        "ix_components_inventory_managed", "components", ["inventory_managed"]
    )
    op.create_index(
        "ix_components_compliance_status", "components", ["compliance_status"]
    )

    # Create component_inventory table for detailed inventory tracking
    op.create_table(
        "component_inventory",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("component_id", sa.String(length=255), nullable=False),
        sa.Column("warehouse_location", sa.String(length=100), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False, default=0),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, default=0),
        sa.Column("quantity_on_order", sa.Integer(), nullable=False, default=0),
        sa.Column("reorder_level", sa.Integer(), nullable=False, default=0),
        sa.Column("reorder_quantity", sa.Integer(), nullable=False, default=0),
        sa.Column("unit_cost", sa.Float(), nullable=True),
        sa.Column("location_details", sa.JSON(), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add indexes for component_inventory
    op.create_index(
        "ix_component_inventory_component_id", "component_inventory", ["component_id"]
    )
    op.create_index(
        "ix_component_inventory_warehouse",
        "component_inventory",
        ["warehouse_location"],
    )
    op.create_index(
        "ix_component_inventory_low_stock",
        "component_inventory",
        ["quantity_available", "reorder_level"],
    )

    # Create inventory_transactions table for tracking inventory movements
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("component_id", sa.String(length=255), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=True),
        sa.Column("from_location", sa.String(length=100), nullable=True),
        sa.Column("to_location", sa.String(length=100), nullable=True),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("notes", Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add indexes for inventory_transactions
    op.create_index(
        "ix_inventory_transactions_component_id",
        "inventory_transactions",
        ["component_id"],
    )
    op.create_index(
        "ix_inventory_transactions_type", "inventory_transactions", ["transaction_type"]
    )
    op.create_index(
        "ix_inventory_transactions_created_at", "inventory_transactions", ["created_at"]
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table("inventory_transactions")
    op.drop_table("component_inventory")

    # Drop indexes
    op.drop_index("ix_components_compliance_status", "components")
    op.drop_index("ix_components_inventory_managed", "components")
    op.drop_index("ix_components_lifecycle_stage", "components")

    # Drop columns from components table
    op.drop_column("components", "warranty_years")
    op.drop_column("components", "certification")
    op.drop_column("components", "weight_kg")
    op.drop_column("components", "dimensions")
    op.drop_column("components", "energy_kwh")
    op.drop_column("components", "efficiency")
    op.drop_column("components", "current_a")
    op.drop_column("components", "voltage_v")
    op.drop_column("components", "warranty_details")
    op.drop_column("components", "compliance_status")
    op.drop_column("components", "inventory_managed")
    op.drop_column("components", "lifecycle_stage")
