"""Webhook endpoints for orchestrator callbacks."""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import AliasChoices, BaseModel, Field

from api.services import (
    DocumentNotFoundError,
    DocumentPatchError,
    DocumentPatchResult,
    DocumentService,
    DocumentValidationError,
    DocumentVersionConflictError,
)
from core.config import Settings, get_settings
from core.database import SessionDep

logger = logging.getLogger(__name__)
router = APIRouter()

SIGNATURE_HEADER = "X-Orchestrator-Signature"
SIGNATURE_PREFIX = "sha256="


class OrchestratorEvent(BaseModel):
    """Envelope for orchestrator webhook events."""

    event: str
    data: Dict[str, Any]
    event_id: Optional[uuid.UUID] = Field(default=None, alias="id")
    timestamp: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class DocumentPatchPayload(BaseModel):
    """Payload describing a document patch operation."""

    document_id: uuid.UUID
    tenant_id: uuid.UUID
    patch: list[Dict[str, Any]]
    document_version: int = Field(
        ..., validation_alias=AliasChoices("version", "document_version")
    )
    change_summary: Optional[str] = None
    evidence: Optional[list[str]] = Field(default_factory=list)
    actor_id: Optional[uuid.UUID] = None
    actor_type: str = "system"

    model_config = {"populate_by_name": True}


def get_document_service(session: SessionDep) -> DocumentService:
    """Dependency returning a document service bound to the session."""

    return DocumentService(session)


def _verify_signature(raw_body: bytes, signature_header: Optional[str], secret: str) -> None:
    """Validate the request signature using the configured secret."""

    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing orchestrator signature header",
        )

    if not signature_header.startswith(SIGNATURE_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid orchestrator signature format",
        )

    provided_signature = signature_header[len(SIGNATURE_PREFIX) :]
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(provided_signature, expected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid orchestrator signature",
        )


def _handle_document_patch(
    payload: DocumentPatchPayload,
    document_service: DocumentService,
) -> DocumentPatchResult:
    """Delegate to the document service to apply the patch."""

    return document_service.apply_patch(
        document_id=payload.document_id,
        tenant_id=payload.tenant_id,
        expected_version=payload.document_version,
        patch_ops=payload.patch,
        actor_id=payload.actor_id,
        actor_type=payload.actor_type,
        change_summary=payload.change_summary,
        evidence=payload.evidence,
    )


@router.post("/callbacks", status_code=status.HTTP_202_ACCEPTED)
async def orchestrator_callback(
    request: Request,
    event: OrchestratorEvent,
    document_service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings),
):
    """Process webhook callbacks emitted by the AI orchestrator."""

    raw_body = await request.body()

    secret = getattr(settings, "ORCHESTRATOR_WEBHOOK_SECRET", None)
    if secret:
        signature = request.headers.get(SIGNATURE_HEADER)
        _verify_signature(raw_body, signature, secret)

    handler: Optional[DocumentPatchResult] = None

    if event.event == "initialization.completed":
        document_payload = DocumentPatchPayload.model_validate(event.data)
        try:
            handler = _handle_document_patch(document_payload, document_service)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except DocumentVersionConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
        except DocumentValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except DocumentPatchError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    else:
        logger.info("Received unsupported orchestrator event %s", event.event)
        return {"status": "ignored", "event": event.event}

    return {
        "status": "applied",
        "event": event.event,
        "document_id": str(handler.document_id),
        "document_version": handler.version,
        "content_hash": handler.content_hash,
    }
