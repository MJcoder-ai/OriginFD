from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _run_subprocess(cmd: list[str]) -> bool:
    try:
        logger.info("prestart: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)
        return True
    except Exception as exc:
        logger.warning("prestart subprocess failed: %s", exc)
        return False


def _discover_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current.parent, *current.parents]:
        if (candidate / "services").exists() and (candidate / "tools").exists():
            return candidate
    return current.parents[3]


def _ensure_repo_path() -> None:
    root = _discover_repo_root()
    candidates = [root, root / "services" / "api"]
    for candidate in candidates:
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


def _bootstrap_sqlite(database_url: str) -> None:
    """Create tables and seed catalog when running against SQLite."""
    _ensure_repo_path()
    try:
        import importlib
        import sys

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        if "services.api.models" in sys.modules:
            models_module = sys.modules["services.api.models"]
        else:
            models_module = importlib.import_module("services.api.models")
        from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog

        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        from services.api.models.project import Project
        from services.api.models.lifecycle import LifecyclePhase, LifecycleGate, LifecycleGateApproval
        from services.api.models.user import User

        tables = [
            Project.__table__,
            LifecyclePhase.__table__,
            LifecycleGate.__table__,
            LifecycleGateApproval.__table__,
            User.__table__,
        ]
        models_module.Base.metadata.create_all(bind=engine, tables=tables)

        Session = sessionmaker(bind=engine)
        with Session() as session:
            seed_lifecycle_catalog(session)
            session.commit()
        logger.info("prestart: sqlite schema created and catalog seeded")
    except Exception as exc:  # pragma: no cover
        logger.warning("prestart sqlite bootstrap failed: %s", exc)


def _run_alembic_programmatic() -> None:
    try:
        from alembic import command
        from alembic.config import Config

        cfg_path = Path("alembic.ini")
        if cfg_path.exists():
            cfg = Config(str(cfg_path))
        else:
            cfg = Config()
            cfg.set_main_option("script_location", "services/api/alembic")
        command.upgrade(cfg, "head")
        logger.info("prestart: alembic upgrade head (programmatic) OK")
    except Exception as exc:  # pragma: no cover
        logger.warning("prestart: programmatic alembic failed: %s", exc)


def _seed_all_programmatic() -> None:
    try:
        _ensure_repo_path()
        from core.database import get_session_local

        from services.api.seeders.lifecycle_seeder import seed_lifecycle_catalog

        SessionLocal = get_session_local()
        with SessionLocal() as session:
            summary = seed_lifecycle_catalog(session)
            session.commit()
            logger.info("prestart: seeded catalog: %s", summary)
    except Exception as exc:  # pragma: no cover
        logger.warning("prestart: seeding failed: %s", exc)


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or "sqlite:///./dev.db"
    os.environ.setdefault("DATABASE_URL", database_url)

    if database_url.startswith("sqlite"):
        _bootstrap_sqlite(database_url)
        return

    if not _run_subprocess([sys.executable, "-m", "alembic", "upgrade", "head"]):
        _ensure_repo_path()
        _run_alembic_programmatic()

    if not _run_subprocess([sys.executable, "-m", "services.api.seeders", "--all"]):
        _seed_all_programmatic()


if __name__ == "__main__":
    main()
