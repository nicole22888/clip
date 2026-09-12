import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# ABSOLUTE PATH ANCHOR: Locate the exact directory of this file
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
# Walk up one step to the backend root directory where your .env lives
BACKEND_DIR = os.path.abspath(os.path.join(CORE_DIR, ".."))
ENV_FILE_PATH = os.path.join(BACKEND_DIR, ".env")

# Force explicit environment variables loading system-wide on execution
if os.path.exists(ENV_FILE_PATH):
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Clipper API"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Placeholder fallback validation keys
    GEMINI_API_KEY: str = "AIzaSyYOUR_ACTUAL_GEMINI_KEY_HERE"
    EXPORT_CRF: int = 18
    
    BASE_DIR: str = BACKEND_DIR
    UPLOAD_DIR: str = os.path.join(BACKEND_DIR, "data/uploads")
    PROXY_DIR: str = os.path.join(BACKEND_DIR, "data/proxies")
    OUTPUT_DIR: str = os.path.join(BACKEND_DIR, "data/outputs")

    # Secure environment wrapper paths alignments
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

for folder in [settings.UPLOAD_DIR, settings.PROXY_DIR, settings.OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)
