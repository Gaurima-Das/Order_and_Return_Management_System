from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Order Management System"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database (defaults to SQLite for easy setup - no installation needed)
    DATABASE_URL: str = "sqlite:///./order_management.db"
    DATABASE_URL_ASYNC: str = "sqlite+aiosqlite:///./order_management.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery (defaults to filesystem broker for Windows - no Redis needed)
    # Using filesystem transport which works well for development
    CELERY_BROKER_URL: str = "filesystem://"
    CELERY_BROKER_TRANSPORT_OPTIONS: Dict[str, Any] = {
        "data_folder_in": "./celery_data/out",
        "data_folder_out": "./celery_data/out",
        "data_folder_processed": "./celery_data/processed"
    }
    CELERY_RESULT_BACKEND: str = "file://./celery_results"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

