"""
Core JSON-Patch operations for ODL-SD documents.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import jsonpatch
import copy
import hashlib
import json
from datetime import datetime

from .validation import validate_patch, PatchValidationError


class PatchError(Exception):
    """Base exception for patch operations."""
    pass


class InversePatchError(Exception):
    """Exception for inverse patch generation failures."""
    pass


def apply_patch(
    document: Dict[str, Any],
    patch_ops: List[Dict[str, Any]],
    evidence: Optional[List[str]] = None,
    dry_run: bool = False,
    actor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply JSON-Patch operations to an ODL-SD document.

    Args:
        document: The ODL-SD document to patch
        patch_ops: List of RFC 6902 patch operations
        evidence: Optional list of evidence URIs for the changes
        dry_run: If True, validate but don't apply changes
        actor: User/system making the changes

    Returns:
        The patched document

    Raises:
        PatchValidationError: If patch validation fails
        PatchError: If patch application fails
    """
    # Validate patch operations
    validation_result = validate_patch(patch_ops, document)
    if not validation_result.is_valid:
        raise PatchValidationError(f"Patch validation failed: {validation_result.errors}")

    if dry_run:
        # Return document with dry_run flag in metadata
        result = copy.deepcopy(document)
        result["_dry_run"] = True
        return result

    try:
        # Create a deep copy to avoid mutating the original
        doc_copy = copy.deepcopy(document)

        # Apply patch using jsonpatch library
        patch_obj = jsonpatch.JsonPatch(patch_ops)
        patched_doc = patch_obj.apply(doc_copy)

        # Update document metadata
        _update_document_metadata(patched_doc, patch_ops, evidence, actor)

        return patched_doc

    except Exception as e:
        raise PatchError(f"Failed to apply patch: {str(e)}")


def create_patch(source: Dict[str, Any], target: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create a JSON-Patch that transforms source into target.

    Args:
        source: The original document
        target: The desired document state

    Returns:
        List of patch operations
    """
    try:
        patch_obj = jsonpatch.make_patch(source, target)
        return list(patch_obj)
    except Exception as e:
        raise PatchError(f"Failed to create patch: {str(e)}")


def inverse_patch(
    patch_ops: List[Dict[str, Any]],
    original_document: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate inverse patch operations for rollback.

    Args:
        patch_ops: The original patch operations
        original_document: The document state before patching

    Returns:
        List of inverse patch operations

    Raises:
        InversePatchError: If inverse generation fails
    """
    try:
        # Apply the original patch to get the target state
        patched_doc = apply_patch(original_document, patch_ops, dry_run=False)

        # Create inverse patch from patched back to original
        inverse_ops = create_patch(patched_doc, original_document)

        return inverse_ops

    except Exception as e:
        raise InversePatchError(f"Failed to generate inverse patch: {str(e)}")


def batch_apply_patches(
    document: Dict[str, Any],
    patch_batches: List[List[Dict[str, Any]]],
    max_ops_per_patch: int = 100,
    actor: Optional[str] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Apply multiple patch batches with rollback capability.

    Args:
        document: The ODL-SD document to patch
        patch_batches: List of patch operation batches
        max_ops_per_patch: Maximum operations per patch
        actor: User/system making the changes

    Returns:
        Tuple of (final_document, list_of_inverse_patches)

    Raises:
        PatchError: If any patch fails (no changes applied)
    """
    if not patch_batches:
        return document, []

    # Validate all patches first
    for i, patch_ops in enumerate(patch_batches):
        if len(patch_ops) > max_ops_per_patch:
            raise PatchError(f"Patch batch {i} exceeds max operations ({max_ops_per_patch})")

        validate_patch(patch_ops, document)

    # Apply patches and collect inverses
    current_doc = copy.deepcopy(document)
    inverse_patches = []

    try:
        for patch_ops in patch_batches:
            # Generate inverse before applying
            inverse_ops = inverse_patch(patch_ops, current_doc)
            inverse_patches.append(inverse_ops)

            # Apply the patch
            current_doc = apply_patch(current_doc, patch_ops, actor=actor)

        # Reverse the inverse patches list for proper rollback order
        inverse_patches.reverse()

        return current_doc, inverse_patches

    except Exception as e:
        raise PatchError(f"Batch patch application failed: {str(e)}")


def _update_document_metadata(
    document: Dict[str, Any],
    patch_ops: List[Dict[str, Any]],
    evidence: Optional[List[str]] = None,
    actor: Optional[str] = None
):
    """Update document metadata after successful patch application."""
    now = datetime.utcnow()

    # Update timestamps
    if "meta" not in document:
        document["meta"] = {}
    if "timestamps" not in document["meta"]:
        document["meta"]["timestamps"] = {}

    document["meta"]["timestamps"]["updated_at"] = now.isoformat()

    # Update version info
    if "versioning" not in document["meta"]:
        document["meta"]["versioning"] = {}

    # Calculate new content hash
    doc_for_hash = copy.deepcopy(document)
    # Remove metadata that shouldn't affect the hash
    doc_for_hash.pop("audit", None)
    hash_str = hashlib.sha256(
        json.dumps(doc_for_hash, sort_keys=True).encode()
    ).hexdigest()

    old_hash = document["meta"]["versioning"].get("content_hash")
    document["meta"]["versioning"]["content_hash"] = f"sha256:{hash_str}"
    if old_hash:
        document["meta"]["versioning"]["previous_hash"] = old_hash

    # Add audit entry
    if "audit" not in document:
        document["audit"] = []

    audit_entry = {
        "timestamp": now.isoformat(),
        "action": "patch_applied",
        "actor": actor or "system",
        "version": len(document["audit"]) + 1,
        "details": {
            "patch_operations": len(patch_ops),
            "evidence": evidence or [],
            "operations": [op.get("op") for op in patch_ops]
        }
    }
    document["audit"].append(audit_entry)


def get_document_version(document: Dict[str, Any]) -> int:
    """Get the current version number of a document."""
    return len(document.get("audit", []))


def calculate_content_hash(document: Dict[str, Any]) -> str:
    """Calculate SHA-256 hash of document content (excluding audit trail)."""
    doc_copy = copy.deepcopy(document)
    doc_copy.pop("audit", None)
    if "meta" in doc_copy and "versioning" in doc_copy["meta"]:
        doc_copy["meta"]["versioning"].pop("content_hash", None)
        doc_copy["meta"]["versioning"].pop("previous_hash", None)

    hash_str = hashlib.sha256(
        json.dumps(doc_copy, sort_keys=True).encode()
    ).hexdigest()
    return f"sha256:{hash_str}"
