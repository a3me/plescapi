import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class TestSettings(BaseSettings):
    model_config = ConfigDict(env_file=".env.test")
    
    google_client_id: str = "test-client-id"
    google_client_secret: str = "test-client-secret"
    gemini_api_key: str = "test-gemini-key"
    google_project_id: str = "test-project-id"
    secret_key: str = "test-secret-key"
    algorithm: str = "HS256"

test_settings = TestSettings() 