from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tasks():
    """List active tasks (placeholder)."""
    return {"tasks": []}
