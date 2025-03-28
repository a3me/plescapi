from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    # apple_client_id: str
    # apple_team_id: str
    # apple_key_id: str
    # apple_private_key_path: str
    secret_key: str
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
