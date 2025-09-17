"""Graph management endpoints for orchestrator."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..graph_store_dependency import get_graph_store

router = APIRouter()


class GraphImportRequest(BaseModel):
    """Payload for importing a graph configuration."""

    id: str
    data: Dict[str, Any]


@router.get("/", response_model=Dict[str, Any])
async def export_graphs(store=Depends(get_graph_store)):
    """Return all stored graph configurations."""
    return store.graphs


@router.get("/{graph_id}", response_model=Dict[str, Any])
async def export_graph(graph_id: str, store=Depends(get_graph_store)):
    """Return a single graph configuration by id."""
    graph = store.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph


@router.post("/", status_code=201)
async def import_graph(req: GraphImportRequest, store=Depends(get_graph_store)):
    """Persist a new graph configuration."""
    store.import_graph(req.id, req.data)
    return {"status": "imported"}


@router.post("/{graph_id}/trace")
async def trace_graph(graph_id: str, store=Depends(get_graph_store)):
    """Trigger a sandbox trace run for a graph."""
    graph = store.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    # Placeholder for real trace logic
    return {"graph_id": graph_id, "status": "trace_started"}


@router.get("/nodes/{node_id}", response_model=Dict[str, Any])
async def get_node(node_id: str, store=Depends(get_graph_store)):
    """Return metadata for a specific node across all graphs."""
    for graph in store.graphs.values():
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                return node
    raise HTTPException(status_code=404, detail="Node not found")
