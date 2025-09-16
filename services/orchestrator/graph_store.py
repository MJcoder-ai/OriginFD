"""Persistent storage for orchestrator graph configurations."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any


class GraphStore:
    """Simple JSON file-backed store for agent graphs."""

    def __init__(self, path: str | Path = "graph_store.json") -> None:
        self.path = Path(path)
        self.graphs: Dict[str, Dict[str, Any]] = {}

    def load(self) -> None:
        """Load graph configurations from disk."""
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                self.graphs = json.load(f)
        else:
            self.graphs = {}

    def save(self) -> None:
        """Persist current graph configurations to disk."""
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.graphs, f, indent=2)

    def get_graph(self, graph_id: str) -> Dict[str, Any] | None:
        return self.graphs.get(graph_id)

    def import_graph(self, graph_id: str, data: Dict[str, Any]) -> None:
        self.graphs[graph_id] = data
        self.save()
