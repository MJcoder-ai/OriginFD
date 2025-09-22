"""Shared fixtures and stubs for document API tests."""

import sys
import types
import uuid
from copy import deepcopy
from typing import Any, Dict, Optional


class _ColumnStub:
    """Mimic SQLAlchemy column behavior for filter expressions."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: Any) -> "_ColumnStub":  # pragma: no cover - behaviour is not exercised
        return self

    def __ne__(self, other: Any) -> "_ColumnStub":  # pragma: no cover - behaviour is not exercised
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> "_ColumnStub":  # pragma: no cover - compatibility
        return self

    def is_(self, other: Any) -> "_ColumnStub":  # pragma: no cover - compatibility
        return self

    def desc(self) -> "_ColumnStub":  # pragma: no cover - compatibility
        return self


class _StubDocument:
    """Lightweight stand-in for the SQLAlchemy Document model."""

    id = _ColumnStub("documents.id")
    tenant_id = _ColumnStub("documents.tenant_id")
    is_active = _ColumnStub("documents.is_active")

    def __init__(
        self,
        id: Optional[uuid.UUID] = None,
        tenant_id: Optional[uuid.UUID] = None,
        project_name: str | None = None,
        portfolio_id: Optional[uuid.UUID] = None,
        domain: str | None = None,
        scale: str | None = None,
        current_version: int = 1,
        content_hash: str = "",
        document_data: Optional[Dict[str, Any]] = None,
        **extra: Any,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.tenant_id = tenant_id or uuid.uuid4()
        self.project_name = project_name
        self.portfolio_id = portfolio_id
        self.domain = domain
        self.scale = scale
        self.current_version = current_version
        self.content_hash = content_hash
        self.document_data = deepcopy(document_data or {})
        self.is_active = extra.get("is_active", True)
        self.created_at = extra.get("created_at")
        self.updated_at = extra.get("updated_at")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<StubDocument id={self.id} version={self.current_version}>"


class _StubDocumentVersion:
    """Lightweight stand-in for the SQLAlchemy DocumentVersion model."""

    document_id = _ColumnStub("document_versions.document_id")
    version_number = _ColumnStub("document_versions.version_number")
    tenant_id = _ColumnStub("document_versions.tenant_id")

    def __init__(
        self,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
        version_number: int,
        content_hash: str,
        previous_hash: str | None = None,
        change_summary: str | None = None,
        patch_operations: Optional[Any] = None,
        evidence_uris: Optional[Any] = None,
        created_by: Optional[uuid.UUID] = None,
        document_data: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> None:
        self.id = uuid.uuid4()
        self.tenant_id = tenant_id
        self.document_id = document_id
        self.version_number = version_number
        self.content_hash = content_hash
        self.previous_hash = previous_hash
        self.change_summary = change_summary
        self.patch_operations = patch_operations
        self.evidence_uris = evidence_uris
        self.created_by = created_by
        self.document_data = deepcopy(document_data or {})

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<StubDocumentVersion document_id={self.document_id} version={self.version_number}>"


class _StubProject:
    """Minimal project representation for dependency overrides."""

    id = _ColumnStub("projects.id")
    primary_document_id = _ColumnStub("projects.primary_document_id")

    def __init__(self, id: Optional[uuid.UUID] = None, primary_document_id: Optional[uuid.UUID] = None) -> None:
        self.id = id or uuid.uuid4()
        self.primary_document_id = primary_document_id


def _install_model_stubs() -> None:
    """Ensure that tests import lightweight model stubs instead of SQLAlchemy models."""

    if "models" in sys.modules:
        return

    models_module = types.ModuleType("models")
    models_module.Document = _StubDocument
    models_module.DocumentVersion = _StubDocumentVersion
    models_module.Project = _StubProject

    sys.modules["models"] = models_module

    document_submodule = types.ModuleType("models.document")
    document_submodule.Document = _StubDocument
    document_submodule.DocumentVersion = _StubDocumentVersion
    sys.modules["models.document"] = document_submodule


_install_model_stubs()
