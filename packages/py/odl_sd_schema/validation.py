"""Validation utilities for ODL-SD documents."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from .document import OdlDocument


class ValidationResult(BaseModel):
    """Result of a document validation run."""

    valid: bool
    errors: List[str] = []


def validate_document(document: OdlDocument) -> ValidationResult:
    """Validate an ODL-SD document instance.

    This is a lightweight placeholder that ensures the document can be
    serialised. Full JSON schema validation would be implemented separately.
    """

    try:
        document.dict()
    except Exception as exc:  # pragma: no cover - defensive
        return ValidationResult(valid=False, errors=[str(exc)])
    return ValidationResult(valid=True)
