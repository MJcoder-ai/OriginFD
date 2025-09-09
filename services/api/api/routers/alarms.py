"""Alarm management endpoints."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from api.routers.auth import get_current_user
from core.database import SessionDep

router = APIRouter()


class Alarm(BaseModel):
    """Alarm data model."""

    id: str = Field(..., description="Unique alarm identifier")
    device_id: str = Field(..., description="Identifier of the device raising the alarm")
    severity: str = Field(..., description="Alarm severity level")
    message: str = Field(..., description="Human readable alarm message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trend: List[float] = Field(default_factory=list, description="Recent metric values for trend charts")


# Simple in-memory alarm store used for the prototype implementation
_ALARMS: Dict[str, Alarm] = {
    "1": Alarm(id="1", device_id="inverter-1", severity="critical", message="Overvoltage"),
    "2": Alarm(id="2", device_id="inverter-1", severity="warning", message="Temperature high"),
    "3": Alarm(id="3", device_id="batt-2", severity="warning", message="State of charge low"),
}


@router.get("/", response_model=List[Alarm])
async def list_alarms(
    db: SessionDep,
    current_user: dict = Depends(get_current_user),
) -> List[Alarm]:
    """Return all active alarms."""

    return list(_ALARMS.values())


@router.get("/{alarm_id}/correlations", response_model=List[Alarm])
async def correlate_alarm(
    alarm_id: str,
    db: SessionDep,
    current_user: dict = Depends(get_current_user),
) -> List[Alarm]:
    """Return alarms correlated to the given alarm.

    This prototype simply correlates alarms originating from the same device.
    """

    alarm = _ALARMS.get(alarm_id)
    if not alarm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alarm not found")

    return [a for a in _ALARMS.values() if a.device_id == alarm.device_id and a.id != alarm.id]


@router.websocket("/ws")
async def alarm_stream(websocket: WebSocket) -> None:
    """Stream alarm trend updates to connected clients."""

    await websocket.accept()
    try:
        while True:
            for alarm in _ALARMS.values():
                # Generate a synthetic metric value and keep last 20 samples
                new_val = random.random()
                alarm.trend.append(new_val)
                if len(alarm.trend) > 20:
                    alarm.trend.pop(0)
                await websocket.send_json({"id": alarm.id, "value": new_val})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Client disconnected; simply exit
        return
