from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.cloud import firestore
from app.config import settings

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        # Verify the Google OAuth token
        payload = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"email": email}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_firestore() -> firestore.Client:
    """Get a Firestore client."""
    return firestore.Client() 