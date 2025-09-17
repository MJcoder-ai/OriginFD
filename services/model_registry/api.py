"""FastAPI router exposing model registry CRUD operations."""

from typing import List

from fastapi import APIRouter, HTTPException

from .models import ModelCreate, ModelInfo, ModelUpdate
from .registry import ModelRegistry

router = APIRouter()
registry = ModelRegistry()


@router.get("/models", response_model=List[ModelInfo])
def list_models() -> List[ModelInfo]:
    """Return all registered models."""
    return registry.list_models()


@router.post("/models", response_model=ModelInfo)
def create_model(model: ModelCreate) -> ModelInfo:
    return registry.create_model(model)


@router.get("/models/{model_id}", response_model=ModelInfo)
def get_model(model_id: str) -> ModelInfo:
    model = registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/models/{model_id}", response_model=ModelInfo)
def update_model(model_id: str, update: ModelUpdate) -> ModelInfo:
    model = registry.update_model(model_id, update)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/models/{model_id}")
def delete_model(model_id: str) -> dict:
    if not registry.delete_model(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    return {"status": "deleted", "id": model_id}
