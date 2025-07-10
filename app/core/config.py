import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PDF Processing API"
    
    # Security
    HUGGINGFACE_API_KEY: Optional[str] = None  # Made optional for development
    GITHUB_TOKEN: str = ""  # Optional
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    
    # Processing
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create uploads directory if it doesn't exist
os.makedirs(Settings().UPLOAD_DIR, exist_ok=True)

settings = Settings() 