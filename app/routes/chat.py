from fastapi import APIRouter, HTTPException, Depends
from google import genai
from google.genai import types
from app.config import settings
from google.cloud import firestore
from uuid import uuid4
from app.dependencies import get_current_user

instructions = """
You are a help Polish tutor. You respond in Polish, using simple sentences and short answers. Your name is Pleść.
Your main task is to help the user learn Polish by having a conversation with them.
You will also provide definitions and explanations of Polish words in English if the user asks for them.
"""

router = APIRouter()
client = genai.Client(api_key=settings.gemini_api_key)

db = firestore.Client()
chats_collection = db.collection("chats")

@router.get("/start")
async def start_chat(bot_prompt: str = instructions, current_user: dict = Depends(get_current_user)):
    """Creates a new chat session and stores it in Firestore."""
    chat_id = str(uuid4())  # Unique chat ID
    # Store chat metadata in Firestore
    chats_collection.document(chat_id).set({
        "user_id": current_user["email"],
        "bot_prompt": bot_prompt,
        "messages": [],
    })
    return {"chat_id": chat_id}

@router.get("/")
async def get_chats(current_user: dict = Depends(get_current_user)):
    """Fetch all chats for a user from Firestore."""
    chats_ref = chats_collection.where("user_id", "==", current_user["email"]).get()
    return [chat.to_dict() for chat in chats_ref]

@router.get("/{chat_id}")
async def get_chat(chat_id: str, current_user: dict = Depends(get_current_user)):
    """Fetch chat history from Firestore."""
    chat_ref = chats_collection.document(chat_id).get()
    if not chat_ref.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_data = chat_ref.to_dict()
    if chat_data["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    
    return chat_data

@router.post("/{chat_id}/message")
async def send_message(chat_id: str, message: str, current_user: dict = Depends(get_current_user)):
    """Sends a message to the chat and stores the response."""
    chat_ref = chats_collection.document(chat_id)
    chat_data = chat_ref.get()
    
    if not chat_data.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_dict = chat_data.to_dict()
    if chat_dict["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")

    # Restore chat context
    chat_history = chat_dict.get("messages", [])
    chat_history.append({"role": "user", "content": message})
    chat_ref.update({"messages": chat_history})
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(response_mime_type="text/plain", system_instruction=instructions),
        contents=chat_history
    )
    
    if response.text == "":
        raise HTTPException(status_code=400, detail="No response from model.")
    
    # Append messages to chat history
    chat_history.append({"role": "assistant", "content": response.text})
    chat_ref.update({"messages": chat_history})

    return {"response": response.text}

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, current_user: dict = Depends(get_current_user)):
    """Deletes a chat from Firestore."""
    chat_ref = chats_collection.document(chat_id)
    chat_data = chat_ref.get()
    
    if not chat_data.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_dict = chat_data.to_dict()
    if chat_dict["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")
    
    chat_ref.delete()
    return {"message": "Chat deleted"}