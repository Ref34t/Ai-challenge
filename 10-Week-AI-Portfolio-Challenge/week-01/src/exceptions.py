"""
Custom exceptions for the Story Generator
Following Python best practices for exception handling
"""

from typing import Optional, Any, Dict


class StoryGeneratorError(Exception):
    """Base exception for story generator errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ModelLoadError(StoryGeneratorError):
    """Raised when model loading fails."""
    
    def __init__(self, model_name: str, reason: str):
        message = f"Failed to load model '{model_name}': {reason}"
        details = {"model_name": model_name, "reason": reason}
        super().__init__(message, details)


class ModelInferenceError(StoryGeneratorError):
    """Raised when model inference fails."""
    
    def __init__(self, model_name: str, prompt: str, reason: str):
        message = f"Model '{model_name}' inference failed: {reason}"
        details = {
            "model_name": model_name,
            "prompt_length": len(prompt),
            "reason": reason
        }
        super().__init__(message, details)


class InsufficientMemoryError(StoryGeneratorError):
    """Raised when system runs out of memory."""
    
    def __init__(self, required_memory: Optional[str] = None):
        message = "Insufficient memory for model operation"
        if required_memory:
            message += f". Required: {required_memory}"
        details = {"required_memory": required_memory}
        super().__init__(message, details)


class InvalidPromptError(StoryGeneratorError):
    """Raised when prompt is invalid."""
    
    def __init__(self, prompt: str, reason: str):
        message = f"Invalid prompt: {reason}"
        details = {
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "reason": reason
        }
        super().__init__(message, details)


class InvalidGenreError(StoryGeneratorError):
    """Raised when genre is not supported."""
    
    def __init__(self, genre: str, available_genres: list):
        message = f"Unsupported genre '{genre}'. Available: {', '.join(available_genres)}"
        details = {
            "requested_genre": genre,
            "available_genres": available_genres
        }
        super().__init__(message, details)


class ConfigurationError(StoryGeneratorError):
    """Raised when configuration is invalid."""
    
    def __init__(self, config_key: str, value: Any, reason: str):
        message = f"Invalid configuration for '{config_key}': {reason}"
        details = {
            "config_key": config_key,
            "value": str(value),
            "reason": reason
        }
        super().__init__(message, details)


class APIKeyError(StoryGeneratorError):
    """Raised when API key is missing or invalid."""
    
    def __init__(self, service: str, reason: str = "Missing or invalid API key"):
        message = f"{service} API error: {reason}"
        details = {"service": service, "reason": reason}
        super().__init__(message, details)


class RateLimitError(StoryGeneratorError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, service: str, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        details = {"service": service, "retry_after": retry_after}
        super().__init__(message, details)


class GenerationTimeoutError(StoryGeneratorError):
    """Raised when story generation times out."""
    
    def __init__(self, timeout_seconds: int, model_name: str):
        message = f"Story generation timed out after {timeout_seconds} seconds"
        details = {
            "timeout_seconds": timeout_seconds,
            "model_name": model_name
        }
        super().__init__(message, details)


class ValidationError(StoryGeneratorError):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value: Any, constraint: str):
        message = f"Validation failed for field '{field}': {constraint}"
        details = {
            "field": field,
            "value": str(value),
            "constraint": constraint
        }
        super().__init__(message, details)


class ServiceUnavailableError(StoryGeneratorError):
    """Raised when external service is unavailable."""
    
    def __init__(self, service: str, status_code: Optional[int] = None):
        message = f"Service '{service}' is unavailable"
        if status_code:
            message += f" (HTTP {status_code})"
        details = {"service": service, "status_code": status_code}
        super().__init__(message, details)


# Exception handling utilities
def handle_model_errors(func):
    """Decorator for handling common model errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                raise InsufficientMemoryError("GPU memory exhausted")
            elif "No module named" in str(e):
                raise ModelLoadError("unknown", f"Missing dependency: {e}")
            else:
                raise ModelInferenceError("unknown", "", str(e))
        except ImportError as e:
            raise ModelLoadError("unknown", f"Import error: {e}")
        except Exception as e:
            raise StoryGeneratorError(f"Unexpected error: {e}")
    
    return wrapper


def create_error_response(exception: StoryGeneratorError) -> Dict[str, Any]:
    """Create standardized error response for API."""
    return {
        "success": False,
        "error": exception.to_dict(),
        "story": "",
        "prompt": "",
        "genre": "",
        "length": "",
        "model": "",
        "word_count": 0,
        "temperature": 0.0
    }


# Context manager for resource cleanup
class ModelContext:
    """Context manager for proper model resource management."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
    
    def __enter__(self):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            return self.model, self.tokenizer
            
        except Exception as e:
            raise ModelLoadError(self.model_name, str(e))
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        # Clear GPU cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


if __name__ == "__main__":
    # Example usage
    try:
        raise InvalidPromptError("", "Empty prompt not allowed")
    except StoryGeneratorError as e:
        print("Error occurred:", e.to_dict())
        error_response = create_error_response(e)
        print("API Response:", error_response)