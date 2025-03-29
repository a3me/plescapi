from fastapi import APIRouter
from google import genai
from app.config import settings

router = APIRouter()

client = genai.Client(api_key=settings.gemini_api_key)

@router.get("/google")
async def chat(message: str):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=message,
    )
    return {"response": response.text}