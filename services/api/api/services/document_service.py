"""Document service providing patch application utilities."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from models.document import Document, DocumentVersion
from odl_sd.schemas import OdlSdDocument
from odl_sd_patch import PatchValidationError, apply_patch
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Base exception for document service errors."""


class DocumentNotFoundError(DocumentServiceError):
    """Raised when a document cannot be found for the provided identifiers."""


class DocumentVersionConflictError(DocumentServiceError):
    """Raised when the requested version does not match the stored version."""


class DocumentValidationError(DocumentServiceError):
    """Raised when a patched document fails validation."""


class DocumentPatchError(DocumentServiceError):
    """Raised when applying a patch to a document fails."""


@dataclass
class DocumentPatchResult:
    """Details about an applied patch."""

    document_id: uuid.UUID
    version: int
    content_hash: str


class DocumentService:
    """Service object encapsulating document mutation operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def apply_patch(
        self,
        *,
        document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        expected_version: int,
        patch_ops: Iterable[dict],
        actor_id: Optional[uuid.UUID] = None,
        actor_type: str = "system",
        change_summary: Optional[str] = None,
        evidence: Optional[List[str]] = None,
    ) -> DocumentPatchResult:
        """Apply a JSON patch to a document and persist the new version."""

        logger.info(
            "Applying patch to document %s for tenant %s via document service",
            document_id,
            tenant_id,
        )

        document = (
            self._session.query(Document)
            .filter(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if not document:
            logger.warning(
                "Document %s not found for tenant %s while applying orchestrator patch",
                document_id,
                tenant_id,
            )
            raise DocumentNotFoundError("Document not found")

        if document.current_version != expected_version:
            logger.error(
                "Version conflict applying patch to document %s: expected %s got %s",
                document_id,
                expected_version,
                document.current_version,
            )
            raise DocumentVersionConflictError(
                f"Version conflict. Expected {expected_version}, got {document.current_version}"
            )

        evidence_list = list(evidence or [])

        try:
            patched_document = apply_patch(
                document.document_data,
                list(patch_ops),
                evidence=evidence_list,
                dry_run=False,
                actor=str(actor_id) if actor_id else None,
            )
        except PatchValidationError as exc:
            logger.error("Patch validation error for document %s: %s", document_id, exc)
            raise DocumentPatchError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Unexpected error applying patch to document %s", document_id
            )
            raise DocumentPatchError("Failed to apply patch") from exc

        odl_document = OdlSdDocument.parse_obj(patched_document)
        validation_result = odl_document.validate_document()
        if not validation_result.is_valid:
            logger.error(
                "Patched document %s failed validation: %s",
                document_id,
                validation_result.errors,
            )
            raise DocumentValidationError(
                f"Patched document invalid: {validation_result.errors}"
            )

        new_version = document.current_version + 1
        previous_hash = document.content_hash
        new_hash = odl_document.meta.versioning.content_hash
        actor_uuid = actor_id or uuid.uuid5(uuid.NAMESPACE_DNS, "originfd-orchestrator")

        document.current_version = new_version
        document.content_hash = new_hash
        document.document_data = patched_document
        document.updated_at = datetime.utcnow()

        version = DocumentVersion(
            tenant_id=document.tenant_id,
            document_id=document.id,
            version_number=new_version,
            content_hash=new_hash,
            previous_hash=previous_hash,
            change_summary=change_summary,
            patch_operations=list(patch_ops),
            evidence_uris=evidence_list,
            created_by=actor_uuid,
            actor_type=actor_type,
            document_data=patched_document,
        )

        try:
            self._session.add(version)
            self._session.commit()
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Failed to persist new document version for %s", document_id
            )
            self._session.rollback()
            raise DocumentPatchError("Failed to persist document changes") from exc

        logger.info(
            "Successfully applied patch to document %s, new version %s",
            document_id,
            new_version,
        )

        return DocumentPatchResult(
            document_id=document.id,
            version=new_version,
            content_hash=new_hash,
        )
