from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/")
async def get_roleplay():
    return {"roleplay": ["Roleplay 1", "Roleplay 2"]}
