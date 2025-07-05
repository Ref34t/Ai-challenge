## Personal Growth Principles

- Assume I'm stuck in a mental echo chamber. I want you to pry it open. Identify the blind spots in my reasoning, the assumptions I treat as facts, and the narratives I've subconsciously internalized. Don't just play devil's advocate—be a ruthless but respectful collaborator who seeks truth above comfort. Challenge my ideas with precision, offer unfamiliar perspectives, and if I'm playing it safe, tell me. Assume I want to grow, not be coddled.

## EXTREMELY IMPORTANT: Code Quality Checks

**ALWAYS run the following commands before completing any task:**

1. Automatically use the IDE's built-in diagnostics tool to check for linting and type errors:
- Run `mcp__ide__getDiagnostics` to check all files for diagnostics
- Fix any linting or type errors before considering the task complete
- Do this for any file you create or modify

## Python Coding Standards (MANDATORY)

**ALWAYS follow these enterprise-grade Python best practices when writing code:**

### 1. Code Organization & Architecture
```python
# ✅ REQUIRED: Modular structure with clear separation of concerns
src/
├── models/         # Business logic and AI models
├── api/           # REST API endpoints
├── config.py      # Centralized configuration
├── exceptions.py  # Custom exception hierarchy
└── utils.py       # Reusable utilities

# ✅ REQUIRED: Use absolute imports
from src.models.story_generator import StoryGenerator
from src.config import settings
```

### 2. Configuration Management
```python
# ✅ REQUIRED: Use Pydantic BaseSettings for all configuration
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    api_key: Optional[str] = Field(default=None, description="API key")
    model_name: str = Field(default="gpt-2", description="Model name")
    
    class Config:
        env_file = ".env"
        env_prefix = "APP_"

settings = Settings()
```

### 3. Exception Handling
```python
# ✅ REQUIRED: Custom exception hierarchy, never use bare except
class AppError(Exception):
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ModelLoadError(AppError):
    pass

# ✅ REQUIRED: Specific exception handling
try:
    result = load_model(model_name)
except ModelLoadError as e:
    logger.error(f"Model loading failed: {e}")
    # Specific recovery strategy
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Different recovery strategy
```

### 4. Type Safety & Documentation
```python
# ✅ REQUIRED: Type hints for all functions
from typing import Dict, List, Optional, Union

def generate_story(
    prompt: str, 
    genre: str = "general",
    max_tokens: Optional[int] = None
) -> Dict[str, Union[str, int, bool]]:
    """
    Generate a story based on prompt.
    
    Args:
        prompt: Story prompt (required)
        genre: Story genre (default: general)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Dictionary containing story and metadata
        
    Raises:
        InvalidPromptError: If prompt is invalid
        ModelLoadError: If model fails to load
    """
    pass
```

### 5. Resource Management
```python
# ✅ REQUIRED: Use context managers for resources
@contextmanager
def model_context(model_name: str):
    model = load_model(model_name)
    try:
        yield model
    finally:
        cleanup_model(model)
        torch.cuda.empty_cache()

# ✅ REQUIRED: Decorators for common patterns
@retry(max_attempts=3, delay=1.0)
@timing
@cache_result(ttl_seconds=3600)
def expensive_operation():
    pass
```

### 6. Input Validation
```python
# ✅ REQUIRED: Validate all inputs with Pydantic
from pydantic import BaseModel, Field, validator

class StoryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    genre: str = Field(default="general")
    temperature: float = Field(default=0.7, ge=0.1, le=1.0)
    
    @validator('genre')
    def validate_genre(cls, v):
        allowed_genres = ['fantasy', 'sci-fi', 'mystery']
        if v not in allowed_genres:
            raise ValueError(f'Genre must be one of {allowed_genres}')
        return v
```

### 7. Logging & Monitoring
```python
# ✅ REQUIRED: Proper logging setup
import logging

logger = logging.getLogger(__name__)

# ✅ REQUIRED: Structured logging with context
logger.info("Story generation started", extra={
    "prompt_length": len(prompt),
    "genre": genre,
    "model": model_name
})
```

### 8. Testing Requirements
```python
# ✅ REQUIRED: Comprehensive test coverage
import pytest
from unittest.mock import Mock, patch

class TestStoryGenerator:
    @pytest.fixture
    def generator(self):
        return StoryGenerator(model_name="test-model")
    
    def test_generate_story_success(self, generator):
        result = generator.generate_story("test prompt")
        assert result["success"]
        assert "story" in result
    
    def test_generate_story_invalid_prompt(self, generator):
        with pytest.raises(InvalidPromptError):
            generator.generate_story("")
```

### 9. Modern Python Tooling (MANDATORY)
```toml
# ✅ REQUIRED: pyproject.toml with these tools
[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
disallow_untyped_defs = true
strict_equality = true

[tool.pytest.ini_options]
addopts = ["--cov=src", "--cov-report=html"]
```

### 10. Code Quality Standards
- ✅ **NEVER** use global variables (use dependency injection)
- ✅ **NEVER** use bare `except:` clauses
- ✅ **ALWAYS** use type hints and docstrings
- ✅ **ALWAYS** validate inputs with Pydantic
- ✅ **ALWAYS** use specific exception types
- ✅ **ALWAYS** clean up resources with context managers
- ✅ **ALWAYS** follow SOLID principles
- ✅ **ALWAYS** write tests for new code

### 11. File Structure Template
```python
"""
Module docstring explaining purpose.
"""

# Standard library imports
import os
import logging
from typing import Dict, List, Optional

# Third-party imports
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

# Local imports
from src.config import settings
from src.exceptions import CustomError
from src.utils import retry, timing

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes and functions with proper type hints and docstrings
```

**ENFORCEMENT: These standards are MANDATORY for all Python code. Any code that doesn't follow these patterns should be refactored to comply.**