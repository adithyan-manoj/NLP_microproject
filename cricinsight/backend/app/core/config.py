import os
from typing import Any
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CricInsight"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"

    # Primary Database (PostgreSQL + pgvector)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "cricinsight"
    POSTGRES_USER: str = "cricops"
    POSTGRES_PASSWORD: str = "cricops_secret"
    DATABASE_URL: str = ""

    # Embedding model for pgvector
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # LLM Providers Configuration (Qwen Primary, Gemini External Research & Fallback)
    LLM_PRIMARY_PROVIDER: str = "qwen"
    LLM_FALLBACK_PROVIDER: str = "gemini"
    LLM_FALLBACK_ENABLED: bool = True

    # Google Gemini Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Local Qwen / Ollama Settings
    QWEN_BASE_URL: str = "http://localhost:11434"
    QWEN_MODEL: str = "qwen2.5:3b-instruct"
    QWEN_CONTEXT_LENGTH: int = 4096
    QWEN_PARALLEL_REQUESTS: int = 1
    QWEN_KEEP_ALIVE: str = "10m"

    # Timeouts and Fallback Deadlines (seconds)
    GEMINI_CONNECT_TIMEOUT: float = 3.0
    GEMINI_TOTAL_TIMEOUT: float = 10.0
    QWEN_TOTAL_TIMEOUT: float = 20.0
    QWEN_MAX_RETRIES: int = 0
    LLM_MAX_TOTAL_DEADLINE: float = 32.0
    LLM_MAX_CONCURRENT_REQUESTS: int = 2

    # Dataset Paths
    DATA_DIR: Path = BACKEND_DIR / "data"
    RAW_DATA_DIR: Path = BACKEND_DIR / "data" / "cricsheet"
    FIXTURES_DIR: Path = BACKEND_DIR / "data" / "fixtures"
    DUCKDB_PATH: Path = BACKEND_DIR / "data" / "cricinsight.duckdb"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.DATA_DIR.is_absolute():
            self.DATA_DIR = BACKEND_DIR / self.DATA_DIR
        if not self.RAW_DATA_DIR.is_absolute():
            self.RAW_DATA_DIR = BACKEND_DIR / self.RAW_DATA_DIR
        if not self.FIXTURES_DIR.is_absolute():
            self.FIXTURES_DIR = BACKEND_DIR / self.FIXTURES_DIR
        if not self.DUCKDB_PATH.is_absolute():
            self.DUCKDB_PATH = BACKEND_DIR / self.DUCKDB_PATH

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
