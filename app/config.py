from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    gemini_api_key: str
    secret_key: str
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
