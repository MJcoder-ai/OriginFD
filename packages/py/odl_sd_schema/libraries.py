"""Component library models for ODL-SD documents."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SignalKind(str, Enum):
    """Kinds of signals a port may carry."""

    DC = "dc"
    AC = "ac"
    DATA = "data"
    CONTROL = "control"
    THERMAL = "thermal"
    MEASUREMENT = "measurement"


class Direction(str, Enum):
    """Port direction relative to the component."""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


class Voltage(BaseModel):
    """Voltage specification for a signal."""

    nominal: float
    min: Optional[float] = None
    max: Optional[float] = None


class Signal(BaseModel):
    """Signal carried by a port."""

    kind: SignalKind
    voltage_v: Optional[Voltage] = None


class Port(BaseModel):
    """Component port definition."""

    id: str
    direction: Direction
    signal: Signal


class Component(BaseModel):
    """Component definition within a library."""

    id: str
    name: Optional[str] = None
    ports: List[Port] = Field(default_factory=list)
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)


class ComponentLibrary(BaseModel):
    """A collection of component definitions."""

    components: Dict[str, Component] = Field(default_factory=dict)
