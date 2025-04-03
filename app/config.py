from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    google_client_id: str
    google_client_secret: str
    gemini_api_key: str
    secret_key: str
    algorithm: str = "HS256"
    google_application_credentials: str

settings = Settings()
