"""
BlueVektor Agents - Configuration Management
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    
    # LLM Configuration
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: str | None = Field(None, description="OpenAI API key for embeddings")
    
    default_model: str = "claude-sonnet-4-20250514"
    reasoning_model: str = "claude-opus-4-20250514"
    fast_model: str = "claude-haiku-3-20240307"
    
    # Local LLM
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    use_local_llm: bool = False
    
    # Database
    database_url: str = Field(..., description="PostgreSQL connection URL")
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Atlassian
    atlassian_url: str | None = None
    atlassian_email: str | None = None
    atlassian_api_token: str | None = None
    
    # Google
    google_credentials_file: str | None = None
    google_delegated_email: str | None = None
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Human-in-the-loop
    hitl_webhook_url: str | None = None
    
    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
