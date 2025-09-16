"""Utilities for generating diffs and KPI deltas for ODL-SD documents."""
from __future__ import annotations

from typing import Dict, Any, List

from .patch import create_patch
from odl_sd_schema.document import OdlDocument


def group_diffs_by_section(patch_ops: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group patch operations by the top-level document section."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for op in patch_ops:
        path = op.get("path", "")
        section = path.lstrip("/").split("/")[0] if path else "root"
        grouped.setdefault(section, []).append(op)
    return grouped


def compute_kpi_deltas(source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, float]:
    """Compute KPI deltas between two documents using the ODL-SD schema."""
    deltas: Dict[str, float] = {}
    try:
        src_doc = OdlDocument.parse_obj(source)
        tgt_doc = OdlDocument.parse_obj(target)
    except Exception:
        # If validation fails, return empty deltas
        return deltas

    # Finance KPIs
    if src_doc.finance and tgt_doc.finance:
        for field in ["capex", "opex"]:
            src_val = getattr(src_doc.finance, field)
            tgt_val = getattr(tgt_doc.finance, field)
            if isinstance(src_val, (int, float)) and isinstance(tgt_val, (int, float)) and src_val != tgt_val:
                deltas[field] = tgt_val - src_val

    # ESG metric KPIs
    if src_doc.esg and tgt_doc.esg:
        old_metrics = {m.name: m.value for m in src_doc.esg.metrics.metrics}
        new_metrics = {m.name: m.value for m in tgt_doc.esg.metrics.metrics}
        for name in set(old_metrics) | set(new_metrics):
            old_val = old_metrics.get(name)
            new_val = new_metrics.get(name)
            if (
                isinstance(old_val, (int, float))
                and isinstance(new_val, (int, float))
                and old_val != new_val
            ):
                deltas[name] = new_val - old_val

    return deltas


def generate_diff_summary(source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    """Generate patch operations, grouped diffs and KPI deltas between two documents."""
    patch_ops = create_patch(source, target)
    grouped = group_diffs_by_section(patch_ops)
    kpi_deltas = compute_kpi_deltas(source, target)
    return {
        "patch": patch_ops,
        "grouped_diffs": grouped,
        "kpi_deltas": kpi_deltas,
    }
