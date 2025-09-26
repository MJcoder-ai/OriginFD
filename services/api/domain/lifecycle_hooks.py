"""Agent and automation hooks for lifecycle events."""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

AGENTS_ENABLED = os.getenv("AGENTS_ENABLED", "0") in {"1", "true", "True"}


def emit_phase_milestone(
    project_id,
    *,
    phase_code: int,
    gate_code: str,
    event_type: str,
    comment: Optional[str] = None,
) -> None:
    """Emit or log lifecycle milestone events behind a feature flag."""

    payload = {
        "project_id": str(project_id),
        "phase_code": int(phase_code),
        "gate_code": gate_code,
        "event_type": event_type,
        "comment": comment or "",
    }

    if not AGENTS_ENABLED:
        logger.debug("Agent hook (disabled): %s", payload)
        return

    # TODO: integrate with AgentManager / task queue
    logger.info("Agent hook (ENABLED): %s", payload)
