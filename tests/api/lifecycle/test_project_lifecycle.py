import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
API_ROOT = os.path.join(PROJECT_ROOT, "services", "api")

if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

from api.routers import projects  # noqa: E402


class StubLifecycleGateApproval:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        gate_id: uuid.UUID,
        status: str,
        decided_by: uuid.UUID,
        decided_at: datetime,
        comments: Optional[str] = None,
    ) -> None:
        self.id = id
        self.gate_id = gate_id
        self.status = status
        self.decided_by = decided_by
        self.decided_at = decided_at
        self.comments = comments

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "status": self.status,
            "decided_by": str(self.decided_by) if self.decided_by else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "comments": self.comments,
        }


class StubLifecycleGate:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        name: str,
        sequence: int,
        status: str,
        phase_id: Optional[uuid.UUID] = None,
        due_date: Optional[datetime] = None,
        owner: Optional[str] = None,
        description: Optional[str] = None,
        context: Optional[Dict[str, object]] = None,
        approval: Optional[StubLifecycleGateApproval] = None,
    ) -> None:
        self.id = id
        self.phase_id = phase_id
        self.name = name
        self.sequence = sequence
        self.status = status
        self.due_date = due_date
        self.owner = owner
        self.description = description
        self._context = dict(context or {})
        self.approval = approval

    def context_dict(self) -> Dict[str, object]:
        return dict(self._context)


class StubLifecyclePhase:
    def __init__(
        self,
        *,
        id: uuid.UUID,
        project_id: uuid.UUID,
        name: str,
        sequence: int,
        status: str,
        description: Optional[str] = None,
        context: Optional[Dict[str, object]] = None,
    ) -> None:
        self.id = id
        self.project_id = project_id
        self.name = name
        self.sequence = sequence
        self.status = status
        self.description = description
        self._context = dict(context or {})

    def context_dict(self) -> Dict[str, object]:
        return dict(self._context)


class StubSession:
    def __init__(self, fallback_phases):
        self._fallback_phases = list(fallback_phases or [])

    class _Query:
        def __init__(self, phases):
            self._phases = phases

        def filter(self, *args, **kwargs):  # pragma: no cover - passthrough
            return self

        def order_by(self, *args, **kwargs):  # pragma: no cover - passthrough
            return self

        def all(self):
            return list(self._phases)

    def query(self, model):
        return self._Query(self._fallback_phases)


def _invoke_lifecycle(
    *,
    project_id: uuid.UUID,
    rows,
    monkeypatch,
    current_user: Dict[str, str],
    fallback_phases=None,
):
    def _fake_fetch(db, project_uuid):
        assert project_uuid == project_id
        return rows

    monkeypatch.setattr(projects, "_fetch_project_lifecycle_rows", _fake_fetch)

    return asyncio.run(
        projects.get_project_lifecycle(
            project_id=str(project_id),
            db=StubSession(fallback_phases),
            current_user=current_user,
        )
    )


def test_lifecycle_response_includes_ordered_phases_and_gates(monkeypatch):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()

    design_phase = StubLifecyclePhase(
        id=uuid.uuid4(),
        project_id=project_id,
        name="Design",
        sequence=1,
        status="completed",
        description="Design activities",
        context={"critical": True},
    )

    design_gate = StubLifecycleGate(
        id=uuid.uuid4(),
        name="Site Assessment",
        sequence=1,
        status="completed",
        owner="site-team@example.com",
        description="Site review",
        context={"checklist": ["terrain", "access"]},
    )

    design_approval = StubLifecycleGateApproval(
        id=uuid.uuid4(),
        gate_id=design_gate.id,
        status="approved",
        decided_by=user_id,
        decided_at=datetime.now(timezone.utc) - timedelta(days=1),
        comments="All requirements satisfied",
    )

    procurement_phase = StubLifecyclePhase(
        id=uuid.uuid4(),
        project_id=project_id,
        name="Procurement",
        sequence=2,
        status="current",
        description="Procurement execution",
        context={"lead": "procurement@example.com"},
    )

    contract_gate = StubLifecycleGate(
        id=uuid.uuid4(),
        name="Contract Signed",
        sequence=2,
        status="pending",
        due_date=datetime.now(timezone.utc) + timedelta(days=5),
        owner="legal@example.com",
        description="Finalize contract",
    )

    supplier_gate = StubLifecycleGate(
        id=uuid.uuid4(),
        name="Supplier Selection",
        sequence=1,
        status="blocked",
        due_date=datetime.now(timezone.utc) - timedelta(days=2),
        owner="buyer@example.com",
        description="Select suppliers",
        context={"rfq": "RFQ-2024-001"},
    )

    rows = [
        (procurement_phase, contract_gate, None),
        (design_phase, design_gate, design_approval),
        (procurement_phase, supplier_gate, None),
    ]

    payload = _invoke_lifecycle(
        project_id=project_id,
        rows=rows,
        monkeypatch=monkeypatch,
        current_user={"id": str(user_id), "tenant_id": "tenant", "email": "user@example.com"},
    )

    assert [phase["name"] for phase in payload["phases"]] == ["Design", "Procurement"]

    procurement_payload = payload["phases"][1]
    assert [gate["name"] for gate in procurement_payload["gates"]] == [
        "Supplier Selection",
        "Contract Signed",
    ]
    supplier_payload = procurement_payload["gates"][0]
    assert supplier_payload["approval_status"] == "pending"
    assert supplier_payload["due_date"].endswith("+00:00")

    design_payload = payload["phases"][0]
    approval_metadata = design_payload["gates"][0]["approval"]
    assert approval_metadata["status"] == "approved"
    assert approval_metadata["decided_by"] == str(user_id)

    assert isinstance(payload["bottlenecks"], list)


def test_lifecycle_returns_empty_when_no_phases(monkeypatch):
    project_id = uuid.uuid4()

    payload = _invoke_lifecycle(
        project_id=project_id,
        rows=[],
        monkeypatch=monkeypatch,
        current_user={"id": str(uuid.uuid4()), "tenant_id": "tenant", "email": "user@example.com"},
        fallback_phases=[],
    )

    assert payload["phases"] == []


def test_lifecycle_phase_without_gates(monkeypatch):
    project_id = uuid.uuid4()
    phase = StubLifecyclePhase(
        id=uuid.uuid4(),
        project_id=project_id,
        name="Commissioning",
        sequence=3,
        status="pending",
        description="Commissioning activities",
    )

    payload = _invoke_lifecycle(
        project_id=project_id,
        rows=[(phase, None, None)],
        monkeypatch=monkeypatch,
        current_user={"id": str(uuid.uuid4()), "tenant_id": "tenant", "email": "user@example.com"},
    )

    assert payload["phases"][0]["gates"] == []
    assert payload["phases"][0]["name"] == "Commissioning"
