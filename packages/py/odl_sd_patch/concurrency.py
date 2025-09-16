"""Utilities for optimistic concurrency control."""

from typing import Any, Dict


class OptimisticLockError(Exception):
    """Raised when a document version conflict is detected."""


def check_version_conflict(document: Dict[str, Any], expected_version: int) -> None:
    """Ensure the document version matches the expected version.

    Parameters
    ----------
    document:
        The document whose version should be checked. The version is derived
        from the length of the ``audit`` trail.
    expected_version:
        The version the caller believes the document is at.

    Raises
    ------
    OptimisticLockError
        If the current document version does not match ``expected_version``.
    """

    current_version = len(document.get("audit", []))
    if current_version != expected_version:
        raise OptimisticLockError(
            f"Version conflict: expected {expected_version}, found {current_version}"
        )
