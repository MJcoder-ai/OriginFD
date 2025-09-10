from datetime import datetime
from typing import Dict, List, Any


class PayoutLedger:
    """Stores payout transactions."""

    def __init__(self) -> None:
        self._ledger: Dict[str, List[Dict[str, Any]]] = {}

    def record_transaction(self, tenant_id: str, psu: int, fee: float, metadata: Dict[str, Any] | None = None) -> None:
        entry = {
            "timestamp": datetime.utcnow(),
            "psu": psu,
            "fee": fee,
        }
        if metadata:
            entry.update(metadata)
        self._ledger.setdefault(tenant_id, []).append(entry)

    def get_history(self, tenant_id: str) -> Dict[str, Any]:
        transactions = self._ledger.get(tenant_id, [])
        return {"tenant_id": tenant_id, "transactions": transactions}
