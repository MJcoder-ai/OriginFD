"""Helpers for producing canonical ODL-SD document exports.

These helpers were extracted from the retired ``odl_sd_api`` module so new
routers can continue to provide the same canonical JSON/YAML exports without
re-implementing the response wiring.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi.responses import JSONResponse, Response
from odl_sd.schemas import OdlSdDocument


def canonicalize_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a canonical representation of an ODL-SD document.

    The ``odl_sd_api`` module historically normalised documents by parsing them
    with :class:`OdlSdDocument` and emitting ``dict`` output via ``to_dict``.
    Reusing the same approach guarantees that downstream tooling receives the
    same canonical structure regardless of the storage backend.
    """

    odl_doc = OdlSdDocument.model_validate(document_data)
    try:
        return odl_doc.model_dump(by_alias=True, exclude_none=False, mode="json")
    except TypeError:  # pragma: no cover - compatibility with older Pydantic
        return odl_doc.dict(by_alias=True, exclude_none=False)


def _build_filename(project_name: str, extension: str) -> str:
    safe_name = project_name.replace(" ", "_") or "document"
    return f"{safe_name}_odl.{extension}"


def create_json_export_response(
    project_name: str, document: Dict[str, Any]
) -> JSONResponse:
    """Create the JSON export response used by the legacy API."""

    filename = _build_filename(project_name, "json")
    return JSONResponse(
        content=document,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def create_yaml_export_response(
    project_name: str, document: Dict[str, Any]
) -> Response:
    """Create the YAML export response used by the legacy API."""

    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive import
        raise RuntimeError("YAML support requires PyYAML to be installed") from exc

    filename = _build_filename(project_name, "yaml")
    yaml_content = yaml.dump(document, default_flow_style=False)
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
