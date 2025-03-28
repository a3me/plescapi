import jwt
import json
from pydantic import BaseModel
import requests
from fastapi import APIRouter, HTTPException, Request
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config import settings

router = APIRouter()

def verify_google_token(token: str):
    try:
        payload = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
        email = payload["email"]
        name = payload.get("name")
        sub = payload["sub"]
        # here we should check if the email is in the database
        # if not, we should create a new user
        # if yes, we grab the user from the database
        return {"email": email, "name": name, "sub": sub}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    

class TokenPayload(BaseModel):
    access_token: str

@router.post("/login/google")
async def login_google(token: TokenPayload):
    try:
        if not token.access_token:
            raise Exception("No access token found in payload")
        user = verify_google_token(token.access_token)
        return user
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
        "jwt": jwt.encode(user_info, settings.secret_key, algorithm=settings.algorithm)
    }
