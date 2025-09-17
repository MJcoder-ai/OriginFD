from datetime import datetime
from typing import Any, Dict, List


class EscrowManager:
    """Tracks escrow milestone payments."""

    def __init__(self) -> None:
        self._milestones: Dict[str, List[Dict[str, Any]]] = {}

    def update_progress(self, tenant_id: str, amount: float) -> None:
        """Record a milestone payment or adjustment."""
        milestone = {
            "timestamp": datetime.utcnow(),
            "amount": amount,
        }
        self._milestones.setdefault(tenant_id, []).append(milestone)

    def get_status(self, tenant_id: str) -> Dict[str, Any]:
        """Return escrow milestone status for a tenant."""
        milestones = self._milestones.get(tenant_id, [])
        total = sum(m.get("amount", 0.0) for m in milestones)
        return {
            "tenant_id": tenant_id,
            "milestones": milestones,
            "total": total,
        }
