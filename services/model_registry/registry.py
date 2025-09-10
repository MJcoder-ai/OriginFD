"""Simple in-memory model registry."""
from typing import Dict, List, Optional
from datetime import datetime
from .models import ModelInfo, ModelCreate, ModelUpdate


class ModelRegistry:
    """In-memory registry storing model metadata."""

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        # Seed with a couple of example models
        self.create_model(
            ModelCreate(
                name="gpt-4", provider="openai", region="us-east", cost_per_1k_tokens=0.06,
                latency_ms=120, eval_score=0.92, cag_hit_rate=0.85, cag_drift=0.05,
                routing_rules={"default": "true"},
            )
        )
        self.create_model(
            ModelCreate(
                name="claude-3", provider="anthropic", region="us-west", cost_per_1k_tokens=0.05,
                latency_ms=150, eval_score=0.88, cag_hit_rate=0.8, cag_drift=0.07,
            )
        )

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        return self._models.get(model_id)

    def create_model(self, model: ModelCreate) -> ModelInfo:
        info = ModelInfo(**model.dict())
        self._models[info.id] = info
        return info

    def update_model(self, model_id: str, update: ModelUpdate) -> Optional[ModelInfo]:
        existing = self._models.get(model_id)
        if not existing:
            return None
        update_data = update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        self._models[model_id] = existing
        return existing

    def delete_model(self, model_id: str) -> bool:
        return self._models.pop(model_id, None) is not None
