import os
import sys
from pathlib import Path

import pytest

# Required settings for tests
os.environ["JWT_SECRET_KEY"] = "test"
os.environ["SECRET_KEY"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test.db"

# Ensure core and orchestrator modules are importable
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "api"))

from memory.graph_rag import GraphQuery, ODLSDGraphRAG


@pytest.mark.asyncio
async def test_semantic_similarity_search(tmp_path):
    """Verify semantic queries use real embeddings for similarity search."""
    graph = ODLSDGraphRAG(tmp_path / "graph.db")
    await graph.initialize()

    document = {
        "project_name": "Renewable Project",
        "domain": "energy",
        "components": {
            "solar": {"name": "Solar Panel", "type": "solar_panel"},
            "wind": {"name": "Wind Turbine", "type": "wind_turbine"},
        },
    }

    await graph.ingest_odl_document(document, "doc1", "proj1")

    query = GraphQuery(
        query_id="q1",
        query_text="solar panel",
        query_type="semantic",
        filters={"node_types": ["component"]},
        limit=1,
    )

    result = await graph.query_graph(query)
    assert result.nodes, "No nodes returned from semantic search"
    assert result.nodes[0].properties["component_id"] == "solar"
