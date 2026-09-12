import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Clipper API"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Register the enterprise configuration variables keys definitions fallbacks
    GEMINI_API_KEY: str = "AIzaSyYOUR_ACTUAL_GEMINI_KEY_HERE"
    EXPORT_CRF: int = 18
    
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "data/uploads")
    PROXY_DIR: str = os.path.join(BASE_DIR, "data/proxies")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "data/outputs")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

for folder in [settings.UPLOAD_DIR, settings.PROXY_DIR, settings.OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)
