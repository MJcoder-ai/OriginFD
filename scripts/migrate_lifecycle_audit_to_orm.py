#!/usr/bin/env python3
"""Backfill legacy lifecycle snapshots into normalized ORM tables.

This script is intentionally conservative: it does not assume a particular
legacy storage location. Update ``iter_legacy_snapshots`` to surface the
project/snapshot pairs from your historical source (for example, project
document audit blobs or a dedicated legacy table).
"""

from tools.paths import ensure_repo_on_path
ensure_repo_on_path()


import argparse
import json
import logging
from typing import Any, Dict, Iterable, Iterator, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_session_local
from services.api.models.project import Project
from services.api.models.lifecycle import (
    ApprovalDecision,
    GateStatus,
    LifecycleGate,
    LifecycleGateApproval,
    LifecyclePhase,
)

logger = logging.getLogger("lifecycle_migration")


def iter_legacy_snapshots(session: Session) -> Iterable[Tuple[Project, Dict[str, Any]]]:
    """Yield ``(project, snapshot)`` pairs from the legacy lifecycle store.

    Replace this stub with queries that load existing lifecycle snapshots from
    your system. Snapshots should align with the ``LifecyclePhaseView`` schema
    returned by the current API (e.g. ``{"phases": [{"phase_code": 0, ...}]}``).
    """

    yield from ()


def map_legacy_status(status_str: str) -> GateStatus:
    mapping = {
        "approved": GateStatus.APPROVED,
        "rejected": GateStatus.REJECTED,
        "blocked": GateStatus.BLOCKED,
        "in_progress": GateStatus.IN_PROGRESS,
        "in-progress": GateStatus.IN_PROGRESS,
        "in progress": GateStatus.IN_PROGRESS,
        "not_started": GateStatus.NOT_STARTED,
        "not started": GateStatus.NOT_STARTED,
        "pending": GateStatus.NOT_STARTED,
    }
    return mapping.get(status_str.lower().strip(), GateStatus.NOT_STARTED)


def backfill_snapshot(session: Session, project_id: UUID, snapshot: Dict[str, Any]) -> Dict[str, int]:
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "approvals": 0}
    phases = {
        phase.phase_code: phase
        for phase in session.scalars(
            select(LifecyclePhase).where(LifecyclePhase.project_id == project_id)
        ).all()
    }

    for phase_payload in snapshot.get("phases", []):
        try:
            phase_code = int(phase_payload.get("phase_code"))
        except (TypeError, ValueError):
            continue

        phase = phases.get(phase_code)
        if phase is None:
            logger.debug("Skipping unknown phase %s for project %s", phase_code, project_id)
            continue

        for gate_payload in phase_payload.get("gates", []) or []:
            gate_code = gate_payload.get("gate_code") or gate_payload.get("key")
            if not gate_code:
                continue

            status = map_legacy_status(str(gate_payload.get("status") or ""))
            gate = session.execute(
                select(LifecycleGate).where(
                    LifecycleGate.project_id == project_id,
                    LifecycleGate.phase_code == phase_code,
                    LifecycleGate.gate_code == gate_code,
                )
            ).scalar_one_or_none()

            if gate is None:
                gate = LifecycleGate(
                    project_id=project_id,
                    phase_id=phase.id,
                    phase_code=phase.phase_code,
                    gate_code=gate_code,
                    name=gate_payload.get("name") or phase.title,
                    description=phase.description,
                    sequence=1 if gate_code == phase.entry_gate_code else 2,
                    status=status,
                    context={},
                )
                session.add(gate)
                stats["inserted"] += 1
            else:
                if gate.status != status:
                    gate.status = status
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1

            if status in (GateStatus.APPROVED, GateStatus.REJECTED):
                decision = (
                    ApprovalDecision.APPROVE
                    if status == GateStatus.APPROVED
                    else ApprovalDecision.REJECT
                )
                if not any(approval.decision == decision for approval in gate.approvals):
                    approval = LifecycleGateApproval(
                        gate=gate,
                        approver_user_id=None,
                        role_key="legacy.migration",
                        decision=decision,
                        comment="Backfilled from legacy snapshot",
                        status=status.value,
                        decided_by=None,
                        decided_at=None,
                    )
                    session.add(approval)
                    stats["approvals"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize legacy lifecycle snapshots")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process snapshots without committing database changes",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    SessionLocal = get_session_local()
    session = SessionLocal()

    totals = {"projects": 0, "inserted": 0, "updated": 0, "skipped": 0, "approvals": 0}

    try:
        for project, snapshot in iter_legacy_snapshots(session):
            if not snapshot:
                continue
            totals["projects"] += 1
            result = backfill_snapshot(session, project.id, snapshot)
            for key, value in result.items():
                totals[key] += value

        if args.dry_run:
            session.rollback()
            totals["dry_run"] = True
        else:
            session.commit()
            totals["dry_run"] = False

        print(json.dumps(totals, indent=2))
    except Exception:  # pragma: no cover - defensive
        session.rollback()
        logger.exception("Lifecycle backfill failed")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
