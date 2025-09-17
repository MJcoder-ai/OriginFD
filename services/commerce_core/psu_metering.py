from datetime import datetime
from typing import Any, Dict, List


class PSUMeter:
    """Simple in-memory PSU usage tracker."""

    def __init__(self) -> None:
        self._usage: Dict[str, List[Dict[str, Any]]] = {}

    def record_usage(
        self, tenant_id: str, psu: int, metadata: Dict[str, Any] | None = None
    ) -> None:
        """Record PSU usage event for a tenant."""
        event = {
            "timestamp": datetime.utcnow(),
            "psu": psu,
        }
        if metadata:
            event.update(metadata)
        self._usage.setdefault(tenant_id, []).append(event)

    def get_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get aggregated PSU usage for a tenant."""
        events = self._usage.get(tenant_id, [])
        total_psu = sum(e.get("psu", 0) for e in events)
        return {
            "tenant_id": tenant_id,
            "total_psu": total_psu,
            "events": events,
        }
