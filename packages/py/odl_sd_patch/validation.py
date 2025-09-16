from __future__ import annotations

"""Validation utilities for JSON-Patch operations."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import jsonpatch


class PatchValidationError(Exception):
    """Exception raised when patch validation fails."""


@dataclass
class ValidationResult:
    """Result of validating patch operations."""

    is_valid: bool
    errors: List[str]


def validate_patch(
    patch_ops: List[Dict[str, Any]],
    document: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Validate JSON-Patch operations.

    Parameters
    ----------
    patch_ops:
        The list of JSON-Patch operations to validate.
    document:
        Optional document to apply the patch against. When provided, the
        validation will attempt to apply the patch in-memory to ensure the
        operations are compatible with the document.

    Returns
    -------
    ValidationResult
        Object containing validation status and any error messages.
    """

    errors: List[str] = []

    # Basic validation using jsonpatch library
    try:
        jsonpatch.JsonPatch(patch_ops)
    except Exception as exc:  # pragma: no cover - library provides message
        errors.append(str(exc))
        return ValidationResult(False, errors)

    # If a document is provided, attempt to apply the patch to ensure
    # all paths exist and operations succeed.
    if document is not None:
        try:
            jsonpatch.apply_patch(document, patch_ops, in_place=False)
        except Exception as exc:  # pragma: no cover - library provides message
            errors.append(str(exc))
            return ValidationResult(False, errors)

    return ValidationResult(True, [])
