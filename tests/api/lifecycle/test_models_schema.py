from sqlalchemy import UniqueConstraint

from services.api.models import Base


def _table(name: str):
    return Base.metadata.tables[name]


def test_lifecycle_phase_columns_present():
    table = _table("lifecycle_phases")
    expected_columns = {
        "phase_code",
        "phase_key",
        "title",
        "order",
        "entry_gate_code",
        "exit_gate_code",
        "required_entry_roles",
        "required_exit_roles",
        "odl_sd_sections",
    }
    assert expected_columns.issubset(table.columns.keys())


def test_lifecycle_gate_columns_and_constraints():
    table = _table("lifecycle_gates")
    required = {"project_id", "phase_code", "gate_code", "status", "context"}
    assert required.issubset(table.columns.keys())

    unique_sets = [
        {column.name for column in constraint.columns}
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert {"project_id", "phase_code", "gate_code"} in unique_sets


def test_lifecycle_gate_approval_columns():
    table = _table("lifecycle_gate_approvals")
    expected = {"gate_id", "approver_user_id", "role_key", "decision", "comment"}
    assert expected.issubset(table.columns.keys())
