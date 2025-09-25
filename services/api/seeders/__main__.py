try:
    from tools.paths import ensure_repo_on_path

    ensure_repo_on_path()
except Exception:
    pass

"""Command-line entry point for seeding lifecycle catalog."""

from __future__ import annotations

import argparse
import json
import logging
from uuid import UUID

from core.database import get_session_local

from services.api.models.project import Project
from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed lifecycle catalog data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Seed ALL projects with the lifecycle catalog",
    )
    group.add_argument(
        "--project-id",
        type=str,
        help="Seed a single project by UUID",
    )
    args = parser.parse_args()

    SessionLocal = get_session_local()
    session = SessionLocal()

    try:
        if args.project_id:
            project_uuid = UUID(args.project_id)
            project = session.get(Project, project_uuid)
            if project is None:
                raise SystemExit(f"Project {project_uuid} not found")
            summary = seed_lifecycle_catalog(session, project=project)
        else:
            summary = seed_lifecycle_catalog(session)
        session.commit()
    except Exception as exc:  # pragma: no cover - CLI safety
        session.rollback()
        logger.exception("Lifecycle seeding failed: %s", exc)
        raise
    finally:
        session.close()

    print(json.dumps(summary))


if __name__ == "__main__":
    main()
