#!/usr/bin/env python3
"""
Simple API for storing media redaction references.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Media Redaction API")

class RedactionBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class MediaRedaction(BaseModel):
    original_uri: str
    redacted_uri: str
    doc_type: str
    boxes: List[RedactionBox] = []

# in-memory storage for demo purposes
STORE: List[MediaRedaction] = []

@app.post("/api/media/redaction")
def save_media_redaction(payload: MediaRedaction):
    STORE.append(payload)
    return {"status": "ok", "id": len(STORE) - 1}

@app.get("/api/media/redaction")
def list_media_redactions() -> List[MediaRedaction]:
    return STORE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
