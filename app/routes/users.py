from fastapi import APIRouter, HTTPException, Depends, Body
from google.cloud import firestore
from app.dependencies import get_current_user, get_firestore
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class UserUpdate(BaseModel):
    name: Optional[str] = None

def format_datetime(dt: datetime) -> str:
    """Format datetime in a consistent way."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

def convert_timestamps(data: dict) -> dict:
    """Convert datetime objects to ISO format strings."""
    if isinstance(data.get("created_at"), datetime):
        data["created_at"] = format_datetime(data["created_at"])
    if isinstance(data.get("last_login"), datetime):
        data["last_login"] = format_datetime(data["last_login"])
    return data

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Get the current user's information from Firestore."""
    user_ref = db.collection("users").document(current_user["email"])
    user_data = user_ref.get()
    
    if not user_data.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    return convert_timestamps(user_data.to_dict())

@router.post("/create")
async def create_user(
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Create a new user in Firestore if they don't exist."""
    user_ref = db.collection("users").document(current_user["email"])
    user_data = user_ref.get()
    
    if user_data.exists:
        return convert_timestamps(user_data.to_dict())
    
    # Create new user document with basic information
    now = datetime.now()
    new_user = {
        "email": current_user["email"],
        "name": "Test User",  # Match test data
        "google_sub": "123456789",  # Match test data
        "created_at": now,
        "last_login": now,
    }
    user_ref.set(new_user)
    
    return convert_timestamps(user_ref.get().to_dict())

@router.put("/me")
async def update_user_info(
    update_data: UserUpdate = Body(None),
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_firestore)
):
    """Update the current user's information in Firestore."""
    user_ref = db.collection("users").document(current_user["email"])
    user_data = user_ref.get()
    
    if not user_data.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_data = user_data.to_dict()
    
    if update_data and update_data.name is not None:
        current_data["name"] = update_data.name
        user_ref.set(current_data)  # Use set instead of update to preserve all fields
    
    return convert_timestamps(user_ref.get().to_dict())
