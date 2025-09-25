import uuid
from typing import Iterable

from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.schema import Table

from services.api.models import Base


@compiles(PGUUID, "sqlite")
def _compile_pg_uuid(_type, compiler, **_):
    return "CHAR(32)"

@compiles(JSONB, "sqlite")
def _compile_jsonb(_type, compiler, **_):
    return "TEXT"


def make_sqlite_engine() -> Engine:
    """Create an in-memory SQLite engine configured for UUID defaults."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _register_functions(dbapi_connection, _):  # type: ignore[misc]
        dbapi_connection.create_function(  # type: ignore[attr-defined]
            "gen_random_uuid", 0, lambda: uuid.uuid4().hex
        )

    return engine


def _normalize_sqlite_defaults(tables: Iterable[Table]) -> None:
    for table in tables:
        for column in table.columns:
            default = getattr(column, "server_default", None)
            if default is None:
                continue
            text = getattr(default, "text", None)
            chunks: list[str] = []
            if isinstance(text, str):
                chunks.append(text.strip())
            arg = getattr(default, "arg", None)
            if arg is not None:
                chunks.append(str(arg).strip())
            joined = " ".join(chunks)
            if "gen_random_uuid()" in joined:
                column.server_default = None


def create_tables(engine: Engine, tables: Iterable[Table]) -> None:
    """Create only the specified tables for the test harness."""
    table_list = list(tables)
    _normalize_sqlite_defaults(table_list)
    Base.metadata.create_all(bind=engine, tables=table_list)


def drop_tables(engine: Engine, tables: Iterable[Table]) -> None:
    """Drop only the specified tables."""
    Base.metadata.drop_all(bind=engine, tables=list(tables))


def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker bound to the provided engine."""
    return sessionmaker(bind=engine)

