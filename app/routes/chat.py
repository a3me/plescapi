from fastapi import APIRouter, HTTPException, Depends, Body
from google import genai
from google.genai import types
from app.config import settings
from google.cloud import firestore
from uuid import uuid4
from app.dependencies import get_current_user, get_firestore
from pydantic import BaseModel
from datetime import datetime, UTC

class Message(BaseModel):
    message: str

instructions = """
You are a help Polish tutor. You respond in Polish, using simple sentences and short answers. Your name is Pleść.
Your main task is to help the user learn Polish by having a conversation with them.
You will also provide definitions and explanations of Polish words in English if the user asks for them.
"""

router = APIRouter()
client = genai.Client(api_key=settings.gemini_api_key)

@router.get("/start")
async def start_chat(bot_id: str, current_user: dict = Depends(get_current_user), db: firestore.Client = Depends(get_firestore)):
    """Creates a new chat session with a specific bot and stores it in Firestore."""
    # Get the bot's prompt
    bots_collection = db.collection("bots")
    bot_ref = bots_collection.document(bot_id).get()
    if not bot_ref.exists:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot_data = bot_ref.to_dict()
    bot_prompt = bot_data["prompt"]
    
    chat_id = str(uuid4())  # Unique chat ID
    # Store chat metadata in Firestore
    chats_collection = db.collection("chats")
    chats_collection.document(chat_id).set({
        "user_id": current_user["email"],
        "bot_id": bot_id,
        "bot_prompt": bot_prompt,
        "messages": [],
    })
    return {"chat_id": chat_id}

@router.get("/")
async def get_chats(current_user: dict = Depends(get_current_user), db: firestore.Client = Depends(get_firestore)):
    """Fetch all chats for a user from Firestore."""
    chats_collection = db.collection("chats")
    chats_ref = chats_collection.where(filter=firestore.FieldFilter("user_id", "==", current_user["email"])).get()
    
    chats = []
    for chat in chats_ref:
        chat_data = chat.to_dict()
        chat_data["id"] = chat.id  # Add the chat ID to the response
        
        # Get bot information
        bot_ref = db.collection("bots").document(chat_data["bot_id"]).get()
        if bot_ref.exists:
            bot_data = bot_ref.to_dict()
            chat_data["bot"] = bot_data
        
        chats.append(chat_data)
    
    return chats

@router.get("/{chat_id}")
async def get_chat(chat_id: str, current_user: dict = Depends(get_current_user), db: firestore.Client = Depends(get_firestore)):
    """Fetch chat history from Firestore."""
    chats_collection = db.collection("chats")
    chat_ref = chats_collection.document(chat_id).get()
    if not chat_ref.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_data = chat_ref.to_dict()
    if chat_data["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    
    return chat_data

@router.post("/{chat_id}/message")
async def send_message(chat_id: str, message: Message, current_user: dict = Depends(get_current_user), db: firestore.Client = Depends(get_firestore)):
    """Sends a message to the chat and stores the response."""
    chats_collection = db.collection("chats")
    chat_ref = chats_collection.document(chat_id)
    chat_data = chat_ref.get()
    
    if not chat_data.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_dict = chat_data.to_dict()
    if chat_dict["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")

    # Restore chat context
    chat_history = chat_dict.get("messages", [])
    current_time = datetime.now(UTC)
    chat_history.append({
        "role": "user", 
        "content": message.message,
        "timestamp": current_time
    })
    chat_ref.update({"messages": chat_history})
    
    # Format chat history for Gemini API
    formatted_history = []
    for msg in chat_history:
        if msg["role"] == "user":
            formatted_history.append(types.Content(parts=[types.Part(text=msg["content"])], role="user"))
        else:
            formatted_history.append(types.Content(parts=[types.Part(text=msg["content"])], role="model"))
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        config=types.GenerateContentConfig(response_mime_type="text/plain", system_instruction=instructions),
        contents=formatted_history
    )
    
    if response.text == "":
        raise HTTPException(status_code=400, detail="No response from model.")
    
    # Append messages to chat history
    chat_history.append({
        "role": "assistant", 
        "content": response.text,
        "timestamp": current_time
    })
    chat_ref.update({"messages": chat_history})

    return {"response": response.text}

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, current_user: dict = Depends(get_current_user), db: firestore.Client = Depends(get_firestore)):
    """Deletes a chat from Firestore."""
    chats_collection = db.collection("chats")
    chat_ref = chats_collection.document(chat_id)
    chat_data = chat_ref.get()
    
    if not chat_data.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_dict = chat_data.to_dict()
    if chat_dict["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")
    
    chat_ref.delete()
    return {"message": "Chat deleted"}