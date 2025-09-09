"""Connection models linking component instances."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class ConnectionType(str, Enum):
    """Types of connections between components."""

    ELECTRICAL = "electrical"
    DATA = "data"
    CONTROL = "control"


class Connection(BaseModel):
    """Port-to-port connection between two component instances."""

    id: str
    from_instance_id: str
    from_port_id: str
    to_instance_id: str
    to_port_id: str
    type: ConnectionType = ConnectionType.ELECTRICAL
    properties: Dict[str, Any] = Field(default_factory=dict)
