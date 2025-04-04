from fastapi import APIRouter, HTTPException, Depends, Body
from google.cloud import firestore
from app.dependencies import get_current_user, get_firestore
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional
from datetime import datetime

router = APIRouter()

class Bot(BaseModel):
    name: str
    description: str
    prompt: str
    image_url: Optional[str] = None

class BotCreate(Bot):
    pass

class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    image_url: Optional[str] = None

def format_datetime(dt: datetime) -> str:
    """Format datetime in a consistent way."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

@router.post("")
async def create_bot(
    bot: BotCreate,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Create a new bot."""
    bot_id = str(uuid4())
    now = datetime.now()
    bot_data = {
        "id": bot_id,
        "name": bot.name,
        "description": bot.description,
        "prompt": bot.prompt,
        "image_url": bot.image_url,
        "created_by": current_user["email"],
        "created_at": now
    }
    
    # Store in Firestore with server timestamp
    db.collection("bots").document(bot_id).set({
        **bot_data,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    
    # Return with formatted datetime
    return {
        **bot_data,
        "created_at": format_datetime(now)
    }

@router.get("")
async def get_bots(
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Get all bots."""
    bots_ref = db.collection("bots").get()
    return [bot.to_dict() for bot in bots_ref]

@router.get("/{bot_id}")
async def get_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Get a specific bot by ID."""
    bot_ref = db.collection("bots").document(bot_id).get()
    if not bot_ref.exists:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot_ref.to_dict()

@router.put("/{bot_id}")
async def update_bot(
    bot_id: str,
    bot_update: BotUpdate = Body(None),
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Update a bot."""
    bot_ref = db.collection("bots").document(bot_id)
    bot_data = bot_ref.get()
    
    if not bot_data.exists:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot_data.to_dict()["created_by"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this bot")
    
    update_data = {}
    if bot_update.name is not None:
        update_data["name"] = bot_update.name
    if bot_update.description is not None:
        update_data["description"] = bot_update.description
    if bot_update.prompt is not None:
        update_data["prompt"] = bot_update.prompt
    if bot_update.image_url is not None:
        update_data["image_url"] = bot_update.image_url
    
    if update_data:
        bot_ref.update(update_data)
    
    return bot_ref.get().to_dict()

@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Delete a bot."""
    bot_ref = db.collection("bots").document(bot_id)
    bot_data = bot_ref.get()
    
    if not bot_data.exists:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot_data.to_dict()["created_by"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this bot")
    
    bot_ref.delete()
    return {"message": "Bot deleted successfully"}
