from fastapi import APIRouter

router = APIRouter()

@router.get('/')
async def planning_root():
    """Planning operations placeholder."""
    return {'planning': 'ok'}
