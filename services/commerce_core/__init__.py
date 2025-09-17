"""Core commerce modules for PSU metering and ledger tracking."""

from typing import Any, Dict

from .escrow_milestones import EscrowManager
from .fee_calculation import FeeCalculator
from .payout_ledger import PayoutLedger
from .psu_metering import PSUMeter

psu_meter = PSUMeter()
escrow_manager = EscrowManager()
fee_calculator = FeeCalculator()
payout_ledger = PayoutLedger()


def publish_usage_event(
    tenant_id: str, psu: int, metadata: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Publish a PSU usage event into the commerce core."""
    info = fee_calculator.calculate_fee(psu)
    event_meta = {**(metadata or {}), **info}
    psu_meter.record_usage(tenant_id, psu, event_meta)
    escrow_manager.update_progress(tenant_id, info["fee"])
    payout_ledger.record_transaction(tenant_id, psu, info["fee"], event_meta)
    return info
