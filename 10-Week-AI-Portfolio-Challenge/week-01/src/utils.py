"""
Utility functions following Python best practices
Clean, reusable, well-tested utilities
"""

import functools
import time
import asyncio
import hashlib
import json
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from pathlib import Path
import logging
from contextlib import contextmanager
import signal
import sys

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


# Decorators following Python best practices
def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay}s")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def timing(func: F) -> F:
    """Decorator to measure function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
    
    return wrapper


def async_timing(func: Callable) -> Callable:
    """Decorator to measure async function execution time."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
    
    return wrapper


def cache_result(ttl_seconds: int = 3600):
    """
    Simple in-memory cache decorator with TTL.
    
    Args:
        ttl_seconds: Time-to-live for cached results
    """
    def decorator(func: F) -> F:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function arguments
            key = _create_cache_key(func.__name__, args, kwargs)
            current_time = time.time()
            
            # Check if result is cached and not expired
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    # Remove expired entry
                    del cache[key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        # Add cache management methods
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "keys": list(cache.keys())
        }
        
        return wrapper
    return decorator


# Utility functions
def _create_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Create a hash-based cache key from function arguments."""
    key_data = {
        "func": func_name,
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def safe_cast(value: Any, target_type: type, default: T = None) -> Union[T, Any]:
    """
    Safely cast value to target type with fallback.
    
    Args:
        value: Value to cast
        target_type: Target type to cast to
        default: Default value if casting fails
    
    Returns:
        Casted value or default
    """
    try:
        if target_type == bool and isinstance(value, str):
            # Handle string boolean conversion
            return value.lower() in ('true', '1', 'yes', 'on')
        return target_type(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to cast {value} to {target_type.__name__}: {e}")
        return default


def validate_input(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate input against constraints.
    
    Args:
        value: Value to validate
        constraints: Dictionary of constraint rules
    
    Returns:
        True if valid, False otherwise
    """
    try:
        if 'type' in constraints and not isinstance(value, constraints['type']):
            return False
        
        if 'min_length' in constraints and hasattr(value, '__len__'):
            if len(value) < constraints['min_length']:
                return False
        
        if 'max_length' in constraints and hasattr(value, '__len__'):
            if len(value) > constraints['max_length']:
                return False
        
        if 'min_value' in constraints and hasattr(value, '__lt__'):
            if value < constraints['min_value']:
                return False
        
        if 'max_value' in constraints and hasattr(value, '__gt__'):
            if value > constraints['max_value']:
                return False
        
        if 'choices' in constraints:
            if value not in constraints['choices']:
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = sanitized.strip('._')
    
    # Ensure it's not too long
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = name[:max_name_length] + ('.' + ext if ext else '')
    
    return sanitized or 'unnamed_file'


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        path: Directory path
    
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    Calculate file hash.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
    
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


# Context managers
@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for function timeout.
    
    Args:
        seconds: Timeout in seconds
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and a timeout alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Disable the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


@contextmanager
def temporary_env_var(key: str, value: str):
    """
    Context manager for temporary environment variable.
    
    Args:
        key: Environment variable key
        value: Environment variable value
    """
    import os
    
    old_value = os.environ.get(key)
    os.environ[key] = value
    
    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value


# Async utilities
async def run_in_thread(func: Callable, *args, **kwargs):
    """
    Run synchronous function in thread pool.
    
    Args:
        func: Function to run
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, **kwargs), *args)


class RateLimiter:
    """Simple rate limiter implementation."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if call is allowed under rate limit."""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get wait time until next call is allowed."""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))


class MemoryMonitor:
    """Monitor memory usage."""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return {
                "rss": process.memory_info().rss / 1024 / 1024,  # MB
                "vms": process.memory_info().vms / 1024 / 1024,  # MB
                "percent": process.memory_percent()
            }
        except ImportError:
            logger.warning("psutil not available, cannot monitor memory")
            return {"rss": 0.0, "vms": 0.0, "percent": 0.0}
    
    @staticmethod
    def check_memory_threshold(threshold_mb: float) -> bool:
        """Check if memory usage exceeds threshold."""
        usage = MemoryMonitor.get_memory_usage()
        return usage["rss"] > threshold_mb


# Testing utilities
def create_mock_response(data: Dict[str, Any], status_code: int = 200) -> object:
    """Create mock HTTP response for testing."""
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        
        def json(self):
            return self.json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")
    
    return MockResponse(data, status_code)


if __name__ == "__main__":
    # Example usage and testing
    
    # Test retry decorator
    @retry(max_attempts=3, delay=0.1)
    def flaky_function(fail_count: int = 2):
        """Function that fails first few times."""
        if not hasattr(flaky_function, 'attempts'):
            flaky_function.attempts = 0
        flaky_function.attempts += 1
        
        if flaky_function.attempts <= fail_count:
            raise ValueError(f"Attempt {flaky_function.attempts} failed")
        return f"Success on attempt {flaky_function.attempts}"
    
    # Test caching
    @cache_result(ttl_seconds=5)
    def expensive_function(x: int) -> int:
        time.sleep(0.1)  # Simulate expensive operation
        return x * x
    
    # Run tests
    print("Testing retry decorator...")
    try:
        result = flaky_function()
        print(f"Retry test passed: {result}")
    except Exception as e:
        print(f"Retry test failed: {e}")
    
    print("\nTesting cache...")
    start = time.time()
    result1 = expensive_function(5)
    first_time = time.time() - start
    
    start = time.time()
    result2 = expensive_function(5)  # Should be cached
    second_time = time.time() - start
    
    print(f"First call: {first_time:.4f}s, Second call: {second_time:.4f}s")
    print(f"Cache working: {second_time < first_time}")
    print(f"Cache info: {expensive_function.cache_info()}")
    
    print("\nTesting rate limiter...")
    limiter = RateLimiter(max_calls=3, time_window=1)
    for i in range(5):
        if limiter.is_allowed():
            print(f"Call {i+1}: Allowed")
        else:
            print(f"Call {i+1}: Rate limited, wait {limiter.wait_time():.2f}s")
    
    print("\nTesting input validation...")
    constraints = {
        'type': str,
        'min_length': 3,
        'max_length': 100,
        'choices': ['fantasy', 'sci-fi', 'mystery']
    }
    
    test_values = ['fantasy', 'hi', 'romance', 'sci-fi']
    for value in test_values:
        is_valid = validate_input(value, constraints)
        print(f"'{value}' is {'valid' if is_valid else 'invalid'}")
    
    print("\nTesting memory monitor...")
    memory_info = MemoryMonitor.get_memory_usage()
    print(f"Memory usage: {memory_info}")
    
    print("\nAll utility tests completed!")