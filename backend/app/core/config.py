from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = BASE_DIR / "configs"


class Settings(BaseSettings):
    APP_NAME: str = "AI Document Processing & Decision Engine"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-change-in-production-must-be-32-chars-min!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Database & Cache
    DATABASE_URL: str = "sqlite:///./documents.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_ALWAYS_EAGER: bool = True

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = str(BASE_DIR / "storage")
    MAX_FILE_SIZE_MB: int = 20

    # Parsing & OCR
    OCR_LANGUAGE: str = "eng"
    OCR_TIMEOUT_SECONDS: int = 60

    # Extraction
    EXTRACTION_PROVIDER: str = "mock"  # 'mock' or 'llm'
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = "gemini-1.5-flash"

    # Thresholds & Rules
    CONFIDENCE_AUTO_THRESHOLD: float = 0.90
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.70
    MAX_PROCESSING_ATTEMPTS: int = 3
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    LOG_LEVEL: str = "INFO"

    # Settings from YAML configs
    yaml_config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        env_file = ".env"
        extra = "ignore"

    def load_yaml_configs(self) -> None:
        settings_file = CONFIG_DIR / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                self.yaml_config = loaded

                # Override dynamic values if in YAML
                if "confidence" in loaded:
                    conf = loaded["confidence"]
                    if "automatic_processing_threshold" in conf:
                        self.CONFIDENCE_AUTO_THRESHOLD = float(conf["automatic_processing_threshold"])
                    if "review_threshold" in conf:
                        self.CONFIDENCE_REVIEW_THRESHOLD = float(conf["review_threshold"])
                if "documents" in loaded:
                    docs = loaded["documents"]
                    if "maximum_file_size_mb" in docs:
                        self.MAX_FILE_SIZE_MB = int(docs["maximum_file_size_mb"])


settings = Settings()
settings.load_yaml_configs()
