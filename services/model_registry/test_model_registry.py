from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.model_registry.api import registry, router

app = FastAPI()
app.include_router(router, prefix="/model-registry")
client = TestClient(app)


def test_list_models():
    response = client.get("/model-registry/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_and_delete_model():
    payload = {
        "name": "test-model",
        "provider": "test",
        "region": "eu",
        "cost_per_1k_tokens": 0.01,
        "latency_ms": 100,
        "eval_score": 0.5,
    }
    response = client.post("/model-registry/models", json=payload)
    assert response.status_code == 200
    created = response.json()
    model_id = created["id"]
    # ensure present
    assert client.get(f"/model-registry/models/{model_id}").status_code == 200
    # delete
    assert client.delete(f"/model-registry/models/{model_id}").status_code == 200
    assert client.get(f"/model-registry/models/{model_id}").status_code == 404
