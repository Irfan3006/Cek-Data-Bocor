import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    xposedornot_api_url: str = "https://api.xposedornot.com/v1"
    
    cache_ttl_seconds: int = 600
    
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60
    
    allowed_origins: list[str] = ["https://databocor.web.id"]
    
    pow_secret_key: str = "change-this-secret-key-in-production"
    pow_difficulty: int = 4
    pow_ttl_seconds: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
