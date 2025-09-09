import os
import sys

import pytest

# Ensure the package path is available
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "packages", "py"))

from odl_sd_patch import (
    PatchValidationError,
    apply_patch,
    check_version_conflict,
    validate_patch,
    OptimisticLockError,
)


def test_validate_patch_success():
    document = {"field": 1}
    patch_ops = [{"op": "replace", "path": "/field", "value": 2}]

    result = validate_patch(patch_ops, document)
    assert result.is_valid
    assert result.errors == []


def test_validate_patch_failure():
    document = {"field": 1}
    patch_ops = [{"op": "replace", "path": "field", "value": 2}]  # Missing leading '/'

    result = validate_patch(patch_ops, document)
    assert not result.is_valid
    assert result.errors

    with pytest.raises(PatchValidationError):
        apply_patch(document, patch_ops)


def test_check_version_conflict():
    document = {"field": 1}
    patch_ops = [{"op": "replace", "path": "/field", "value": 2}]

    # Initial version should be 0
    check_version_conflict(document, 0)

    # Apply patch to increment version
    patched = apply_patch(document, patch_ops)

    # Correct version should pass
    check_version_conflict(patched, 1)

    # Outdated version should raise
    with pytest.raises(OptimisticLockError):
        check_version_conflict(patched, 0)
