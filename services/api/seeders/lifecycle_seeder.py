"""Lifecycle catalog seeding utilities."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.domain.lifecycle_catalog import LIFECYCLE_CATALOG
from services.api.models import LifecyclePhase
from services.api.models.project import Project

logger = logging.getLogger(__name__)


def _ensure_iterable(value: Iterable[str]) -> List[str]:
    return list(value)


def _set_if_changed(obj: LifecyclePhase, attr: str, value) -> bool:
    if getattr(obj, attr) != value:
        setattr(obj, attr, value)
        return True
    return False


def seed_lifecycle_catalog(
    session: Session,
    project: Optional[Project] = None,
) -> Dict[str, int]:
    """Upsert lifecycle phases for one or more projects from the canonical catalog."""

    if project is not None:
        projects_to_seed: List[Project] = [project]
    else:
        projects_to_seed = list(session.scalars(select(Project)))

    inserted = 0
    updated = 0
    unchanged = 0

    for project_row in projects_to_seed:
        project_id: UUID = project_row.id

        for spec in LIFECYCLE_CATALOG:
            existing = session.execute(
                select(LifecyclePhase).where(
                    LifecyclePhase.project_id == project_id,
                    LifecyclePhase.phase_code == spec.phase_code,
                )
            ).scalar_one_or_none()

            if existing is None:
                phase = LifecyclePhase(
                    id=uuid4(),
                    project_id=project_id,
                    phase_code=spec.phase_code,
                    phase_key=spec.phase_key,
                    title=spec.title,
                    order=spec.order,
                    entry_gate_code=spec.entry_gate_code,
                    exit_gate_code=spec.exit_gate_code,
                    required_entry_roles=_ensure_iterable(spec.required_entry_roles),
                    required_exit_roles=_ensure_iterable(spec.required_exit_roles),
                    odl_sd_sections=_ensure_iterable(spec.odl_sd_sections),
                    name=spec.title,
                    description=spec.description,
                    sequence=spec.order,
                    status="not_started",
                    context={},
                )
                session.add(phase)
                inserted += 1
            else:
                changed = False
                changed |= _set_if_changed(existing, "phase_key", spec.phase_key)
                changed |= _set_if_changed(existing, "title", spec.title)
                changed |= _set_if_changed(existing, "order", spec.order)
                changed |= _set_if_changed(
                    existing, "entry_gate_code", spec.entry_gate_code
                )
                changed |= _set_if_changed(
                    existing, "exit_gate_code", spec.exit_gate_code
                )
                changed |= _set_if_changed(
                    existing,
                    "required_entry_roles",
                    _ensure_iterable(spec.required_entry_roles),
                )
                changed |= _set_if_changed(
                    existing,
                    "required_exit_roles",
                    _ensure_iterable(spec.required_exit_roles),
                )
                changed |= _set_if_changed(
                    existing,
                    "odl_sd_sections",
                    _ensure_iterable(spec.odl_sd_sections),
                )
                changed |= _set_if_changed(existing, "name", spec.title)
                changed |= _set_if_changed(existing, "description", spec.description)
                changed |= _set_if_changed(existing, "sequence", spec.order)

                if changed:
                    updated += 1
                else:
                    unchanged += 1

    session.flush()

    summary = {"inserted": inserted, "updated": updated, "unchanged": unchanged}
    logger.info(
        "Lifecycle catalog seeding complete for %d project(s): %s",
        len(projects_to_seed),
        summary,
    )
    return summary
