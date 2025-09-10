"""Dependency to access the graph store from FastAPI routes."""
from fastapi import Request


def get_graph_store(request: Request):
    return request.app.state.graph_store
