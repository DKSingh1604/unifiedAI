"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ev_analytics"
    
    # Data Source Configuration
    csv_source: Literal["local", "s3"] = "local"
    csv_local_path: str = "./data/raw/Electric_Vehicle_Population_Data.csv"
    csv_s3_bucket: str = ""
    csv_s3_key: str = ""
    
    # AWS Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-west-2"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
