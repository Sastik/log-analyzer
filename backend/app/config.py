from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    
    # Log Files
    LOG_BASE_PATH: str
    LOG_FILE_RETENTION_DAYS: int = 2
    
    # API
    CORS_ORIGINS: str
    
    # Performance
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 300
    LOG_BATCH_SIZE: int = 100
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()