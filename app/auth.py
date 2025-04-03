import jwt
import json
from pydantic import BaseModel
import requests
from fastapi import APIRouter, HTTPException, Request, Response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config import settings
from google.cloud import firestore

router = APIRouter()
db = firestore.Client()
users_collection = db.collection("users")

def verify_google_token(token: str):
    try:
        payload = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
        email = payload["email"]
        name = payload.get("name")
        sub = payload["sub"]

        # Check if user exists in Firestore
        user_ref = users_collection.document(email)
        user_data = user_ref.get()

        if not user_data.exists:
            # Create new user if they don't exist
            user_ref.set({
                "email": email,
                "name": name,
                "google_sub": sub,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
            })
        else:
            # Update last login for existing user
            user_ref.update({
                "last_login": firestore.SERVER_TIMESTAMP,
            })

        # Return the Google token directly
        return {"token": token}
    except Exception as e:
        print(f"Error in verify_google_token: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token")

class TokenPayload(BaseModel):
    access_token: str

@router.post("/login/google")
async def login_google(token: TokenPayload):
    try:
        if not token.access_token:
            raise Exception("No access token found in payload")
        return verify_google_token(token.access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

@router.get("/login/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    provider = request.query_params.get("provider")
    
    if not code or not provider:
        raise HTTPException(status_code=400, detail="Missing authorization code or provider")
    
    if provider == "google":
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:8000/auth/callback"  # Change for production
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    response = requests.post(token_url, data=data)
    token_data = response.json()
    
    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")
    
    if provider == "google":
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    elif provider == "apple":
        user_info_url = "https://appleid.apple.com/auth/keys"  # Apple doesn't provide an easy user info endpoint
    
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    user_info = requests.get(user_info_url, headers=headers).json()
    
    return {
        "email": user_info.get("email"),
        "name": user_info.get("name", "Apple User"),
        "token": token_data["access_token"]
    }
