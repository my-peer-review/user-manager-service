from fastapi import APIRouter

router = APIRouter()

@router.get("/user/health")
async def health_check():
    return {"status": "ok"}