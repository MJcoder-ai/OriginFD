"""Pydantic models for the model registry."""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
import uuid


class ModelInfo(BaseModel):
    """Representation of a model in the registry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: str
    region: str
    cost_per_1k_tokens: float
    latency_ms: int
    eval_score: float = 0.0
    is_active: bool = True
    routing_rules: Dict[str, str] = {}
    cag_hit_rate: float = 0.0
    cag_drift: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ModelCreate(BaseModel):
    name: str
    provider: str
    region: str
    cost_per_1k_tokens: float
    latency_ms: int
    eval_score: float = 0.0
    is_active: bool = True
    routing_rules: Dict[str, str] = {}
    cag_hit_rate: float = 0.0
    cag_drift: float = 0.0


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None
    cost_per_1k_tokens: Optional[float] = None
    latency_ms: Optional[int] = None
    eval_score: Optional[float] = None
    is_active: Optional[bool] = None
    routing_rules: Optional[Dict[str, str]] = None
    cag_hit_rate: Optional[float] = None
    cag_drift: Optional[float] = None
