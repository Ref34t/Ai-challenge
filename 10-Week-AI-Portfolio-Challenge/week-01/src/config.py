"""
Configuration management using Pydantic Settings
Following Python best practices for configuration
"""

from pydantic import BaseSettings, Field
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Model Configuration
    model_name: str = Field(
        default="microsoft/DialoGPT-medium",
        description="Default Hugging Face model name"
    )
    fallback_model: str = Field(
        default="gpt2",
        description="Fallback model if primary fails"
    )
    use_openai: bool = Field(default=False, description="Enable OpenAI integration")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Generation Parameters
    default_temperature: float = Field(
        default=0.7, ge=0.1, le=1.0,
        description="Default creativity temperature"
    )
    max_tokens_short: int = Field(default=150, description="Tokens for short stories")
    max_tokens_medium: int = Field(default=300, description="Tokens for medium stories")
    max_tokens_long: int = Field(default=500, description="Tokens for long stories")
    max_batch_size: int = Field(default=5, description="Maximum batch generation size")
    
    # Device Configuration
    device: str = Field(default="auto", description="Computing device (auto/cpu/cuda)")
    max_memory_gb: Optional[float] = Field(default=None, description="Maximum memory usage")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Cache Configuration
    enable_cache: bool = Field(default=True, description="Enable model caching")
    cache_dir: str = Field(default="~/.cache/story_generator", description="Cache directory")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Requests per minute")
    rate_limit_burst: int = Field(default=20, description="Burst requests allowed")
    
    # Security
    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501"],
        description="Allowed CORS origins"
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    
    class Config:
        env_file = ".env"
        env_prefix = "STORY_GEN_"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            """Custom environment variable parsing."""
            if field_name == 'allowed_origins':
                return [origin.strip() for origin in raw_val.split(',')]
            return cls.json_loads(raw_val)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Post-initialization validation and setup
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            
        if self.openai_api_key:
            self.use_openai = True
            
        # Expand cache directory path
        self.cache_dir = str(Path(self.cache_dir).expanduser())
        
        # Create cache directory if it doesn't exist
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    @property
    def length_token_mapping(self) -> dict:
        """Get token limits for different story lengths."""
        return {
            "short": self.max_tokens_short,
            "medium": self.max_tokens_medium,
            "long": self.max_tokens_long
        }

    @property
    def is_gpu_available(self) -> bool:
        """Check if GPU is available and should be used."""
        import torch
        if self.device == "auto":
            return torch.cuda.is_available()
        return self.device == "cuda"

    def get_model_device(self) -> str:
        """Get the appropriate device for model loading."""
        if self.device == "auto":
            return "cuda" if self.is_gpu_available else "cpu"
        return self.device

    def validate_settings(self) -> None:
        """Validate configuration settings."""
        if self.use_openai and not self.openai_api_key:
            raise ValueError("OpenAI API key required when use_openai=True")
        
        if self.max_memory_gb and self.max_memory_gb <= 0:
            raise ValueError("max_memory_gb must be positive")
        
        if not (0.1 <= self.default_temperature <= 1.0):
            raise ValueError("default_temperature must be between 0.1 and 1.0")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection function for FastAPI."""
    return settings


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"
    api_host: str = "127.0.0.1"


class ProductionSettings(Settings):
    """Production environment settings."""
    debug: bool = False
    log_level: str = "WARNING"
    rate_limit_requests: int = 1000
    enable_cache: bool = True


class TestingSettings(Settings):
    """Testing environment settings."""
    debug: bool = True
    log_level: str = "DEBUG"
    model_name: str = "gpt2"  # Use smaller model for tests
    max_tokens_short: int = 50
    max_tokens_medium: int = 100
    max_tokens_long: int = 150


def get_environment_settings(env: str = None) -> Settings:
    """Get settings based on environment."""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings
    }
    
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


if __name__ == "__main__":
    # Example usage and validation
    config = Settings()
    config.validate_settings()
    
    print("Configuration loaded successfully:")
    print(f"Model: {config.model_name}")
    print(f"Device: {config.get_model_device()}")
    print(f"OpenAI enabled: {config.use_openai}")
    print(f"Cache directory: {config.cache_dir}")
    print(f"Token limits: {config.length_token_mapping}")