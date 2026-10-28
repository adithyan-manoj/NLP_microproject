import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: /Users/adithyanmanoj/Codes_and_all/NLP project
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CricInsight"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Environment
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database
    DUCKDB_PATH: Path = BACKEND_DIR / "data" / "cricinsight.duckdb"
    RAW_DATA_DIR: Path = BACKEND_DIR / "data" / "cricsheet"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure data directory exists
settings.DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
