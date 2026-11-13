from pydantic_settings import BaseSettings
from pathlib import Path
import os
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

DB_PATH = (BACKEND_DIR / "finn.db").as_posix()


class Settings(BaseSettings):
    app_name: str = "FINN"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = f"sqlite:///{DB_PATH}"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    price_refresh_interval: int = 30
    announcement_refresh_interval: int = 15
    default_volume_multiplier: float = 2.0
    default_price_change_pct: float = 3.0

    class Config:
        env_file = str(BACKEND_DIR / ".env")


settings = Settings()
