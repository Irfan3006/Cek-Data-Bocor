import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API endpoints
    xposedornot_api_url: str = "https://api.xposedornot.com/v1"
    
    # Cache settings
    cache_ttl_seconds: int = 600  # 10 minutes
    
    # Rate limit settings
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60
    
    # Security / CORS settings
    allowed_origins: list[str] = ["*"]
    
    # Environment variables
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()
