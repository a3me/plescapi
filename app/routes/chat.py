from fastapi import APIRouter
from google import genai
from google.genai import types
from app.config import settings
# import jwt

instructions = """
You are a help Polish tutor. You respond in Polish, using simple sentences and short answers. Your name is Pleść.
Your main task is to help the user learn Polish by having a conversation with them.
You will also provide definitions and explanations of Polish words in English if the user asks for them.
"""

router = APIRouter()
client = genai.Client(api_key=settings.gemini_api_key)

def create_chat():
    return client.chats.create(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(response_mime_type="text/plain", system_instruction=instructions)
    )
    
chat = create_chat()

@router.get("/google/reset")
async def reset_chat():
    global chat
    chat = create_chat()
    return {"message": "Chat reset"}

@router.get("/google/history")
async def get_history():
    return chat.get_history()

@router.get("/google")
async def send_message(message: str):
    # validate jwt from token cookie
    # try:
    #     payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    # except Exception:
    #     raise HTTPException(status_code=401, detail="Invalid JWT token")
    response = chat.send_message(message)
    return {"response": response.text}