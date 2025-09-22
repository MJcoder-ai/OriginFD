"""Service layer utilities for the API gateway."""

from .document_service import (
    DocumentNotFoundError,
    DocumentPatchError,
    DocumentPatchResult,
    DocumentService,
    DocumentValidationError,
    DocumentVersionConflictError,
)

__all__ = [
    "DocumentService",
    "DocumentPatchResult",
    "DocumentNotFoundError",
    "DocumentVersionConflictError",
    "DocumentValidationError",
    "DocumentPatchError",
]
