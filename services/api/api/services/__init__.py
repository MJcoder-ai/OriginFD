"""Service layer utilities for the API gateway."""

from .document_service import (
    DocumentService,
    DocumentPatchResult,
    DocumentNotFoundError,
    DocumentVersionConflictError,
    DocumentValidationError,
    DocumentPatchError,
)

__all__ = [
    "DocumentService",
    "DocumentPatchResult",
    "DocumentNotFoundError",
    "DocumentVersionConflictError",
    "DocumentValidationError",
    "DocumentPatchError",
]
