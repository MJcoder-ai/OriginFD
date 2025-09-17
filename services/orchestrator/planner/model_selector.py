"""Select appropriate models from the registry for tasks."""

from typing import List, Optional

from model_registry import ModelInfo, ModelRegistry


class ModelSelector:
    """Simple selector using registry metadata to choose models."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()

    def select_model(
        self, task_type: str, region: Optional[str] = None
    ) -> Optional[ModelInfo]:
        """Return the best model for a task type and region."""
        candidates = self._filter_models(region)
        if not candidates:
            return None
        # sort by eval score descending, lower cost and latency preferred
        candidates.sort(
            key=lambda m: (m.eval_score, -m.cost_per_1k_tokens, -m.latency_ms),
            reverse=True,
        )
        return candidates[0]

    def get_fallback_models(
        self, task_type: str, region: Optional[str] = None
    ) -> List[ModelInfo]:
        """Return models ordered by preference for fallback strategies."""
        candidates = self._filter_models(region)
        candidates.sort(
            key=lambda m: (m.eval_score, -m.cost_per_1k_tokens, -m.latency_ms),
            reverse=True,
        )
        return candidates[1:]

    def _filter_models(self, region: Optional[str]) -> List[ModelInfo]:
        models = self.registry.list_models()
        if region:
            models = [m for m in models if m.region == region]
        return [m for m in models if m.is_active]
