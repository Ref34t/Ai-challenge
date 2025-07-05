"""
Advanced Python: Asynchronous Programming
Demonstrates senior-level async/await patterns and concurrency
"""

import asyncio
import aiohttp
import aiofiles
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)


# =============================================================================
# ASYNC CONTEXT MANAGERS
# =============================================================================

@asynccontextmanager
async def async_timer(operation_name: str):
    """Async context manager for timing operations."""
    start_time = time.time()
    logger.info(f"Starting {operation_name}")
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name} in {duration:.3f}s")


class AsyncDatabase:
    """
    Async context manager for database connections.
    Demonstrates proper resource management in async code.
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection: Optional[Any] = None
        self.is_connected = False
    
    async def __aenter__(self):
        """Async context entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context exit with proper cleanup."""
        await self.close()
        if exc_type:
            logger.error(f"Exception in database context: {exc_val}")
        return False  # Don't suppress exceptions
    
    async def connect(self):
        """Simulate async database connection."""
        await asyncio.sleep(0.1)  # Simulate connection time
        self.is_connected = True
        logger.info("Database connected")
    
    async def close(self):
        """Simulate async database close."""
        await asyncio.sleep(0.05)  # Simulate cleanup time
        self.is_connected = False
        logger.info("Database connection closed")
    
    async def execute(self, query: str) -> Dict[str, Any]:
        """Execute async database query."""
        if not self.is_connected:
            raise RuntimeError("Database not connected")
        
        await asyncio.sleep(0.02)  # Simulate query time
        return {"query": query, "result": "success", "rows": 42}


# =============================================================================
# ASYNC ITERATORS AND GENERATORS
# =============================================================================

class AsyncDataStreamer:
    """
    Async iterator that demonstrates streaming data processing.
    Shows senior-level understanding of async iteration protocols.
    """
    
    def __init__(self, data_source: str, batch_size: int = 10):
        self.data_source = data_source
        self.batch_size = batch_size
        self.current_position = 0
        self.total_items = 100  # Simulate data size
    
    def __aiter__(self):
        """Return async iterator."""
        return self
    
    async def __anext__(self):
        """Get next batch of data."""
        if self.current_position >= self.total_items:
            raise StopAsyncIteration
        
        # Simulate async data fetching
        await asyncio.sleep(0.01)
        
        batch_start = self.current_position
        batch_end = min(self.current_position + self.batch_size, self.total_items)
        
        batch_data = [
            {"id": i, "value": f"item_{i}", "source": self.data_source}
            for i in range(batch_start, batch_end)
        ]
        
        self.current_position = batch_end
        return batch_data


async def async_data_generator(count: int):
    """
    Async generator for streaming data.
    Demonstrates memory-efficient async data processing.
    """
    for i in range(count):
        # Simulate async data fetching
        await asyncio.sleep(0.001)
        yield {"id": i, "timestamp": time.time(), "data": f"record_{i}"}


async def async_fibonacci_generator(limit: int):
    """Async generator for Fibonacci sequence."""
    a, b = 0, 1
    count = 0
    
    while count < limit:
        await asyncio.sleep(0.001)  # Allow other tasks to run
        yield a
        a, b = b, a + b
        count += 1


# =============================================================================
# CONCURRENT PATTERNS
# =============================================================================

class AsyncWorkerPool:
    """
    Async worker pool for concurrent task processing.
    Demonstrates advanced concurrency patterns.
    """
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks: List[asyncio.Task] = []
    
    async def submit_task(self, coro: Awaitable) -> Any:
        """Submit coroutine to worker pool."""
        async def _worker():
            async with self.semaphore:
                return await coro
        
        task = asyncio.create_task(_worker())
        self.active_tasks.append(task)
        
        # Clean up completed tasks
        self.active_tasks = [t for t in self.active_tasks if not t.done()]
        
        return await task
    
    async def map(self, func: Callable, items: List[Any]) -> List[Any]:
        """Apply async function to all items concurrently."""
        tasks = [self.submit_task(func(item)) for item in items]
        return await asyncio.gather(*tasks)
    
    async def shutdown(self):
        """Wait for all active tasks to complete."""
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)


@dataclass
class AsyncTaskResult:
    """Result container for async task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0


class AsyncTaskManager:
    """
    Advanced async task management with error handling and monitoring.
    Demonstrates production-ready async patterns.
    """
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[AsyncTaskResult] = []
        self.task_counter = 0
    
    async def run_task(
        self,
        coro: Awaitable,
        task_name: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> AsyncTaskResult:
        """Run async task with monitoring and error handling."""
        
        if task_name is None:
            self.task_counter += 1
            task_name = f"task_{self.task_counter}"
        
        start_time = time.time()
        
        try:
            if timeout:
                result = await asyncio.wait_for(coro, timeout=timeout)
            else:
                result = await coro
            
            task_result = AsyncTaskResult(
                task_id=task_name,
                success=True,
                result=result,
                duration=time.time() - start_time
            )
            
        except asyncio.TimeoutError as e:
            task_result = AsyncTaskResult(
                task_id=task_name,
                success=False,
                error=e,
                duration=time.time() - start_time
            )
            logger.error(f"Task {task_name} timed out after {timeout}s")
            
        except Exception as e:
            task_result = AsyncTaskResult(
                task_id=task_name,
                success=False,
                error=e,
                duration=time.time() - start_time
            )
            logger.error(f"Task {task_name} failed: {e}")
        
        self.completed_tasks.append(task_result)
        return task_result
    
    async def run_parallel_tasks(
        self,
        tasks: List[Awaitable],
        max_concurrent: int = 5,
        timeout_per_task: Optional[float] = None
    ) -> List[AsyncTaskResult]:
        """Run multiple tasks with concurrency control."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _run_with_semaphore(task_coro, task_id):
            async with semaphore:
                return await self.run_task(task_coro, f"parallel_{task_id}", timeout_per_task)
        
        parallel_tasks = [
            _run_with_semaphore(task, i) 
            for i, task in enumerate(tasks)
        ]
        
        return await asyncio.gather(*parallel_tasks)


# =============================================================================
# ASYNC HTTP CLIENT PATTERNS
# =============================================================================

class AsyncHTTPClient:
    """
    Production-ready async HTTP client with advanced features.
    Demonstrates real-world async HTTP patterns.
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_with_retry(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch URL with retry logic."""
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "data": data,
                            "status": response.status,
                            "attempt": attempt + 1
                        }
                    elif response.status >= 500 and attempt < self.max_retries:
                        # Retry on server errors
                        logger.warning(f"Server error {response.status}, retrying in {self.retry_delay}s")
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "status": response.status,
                            "attempt": attempt + 1
                        }
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    logger.warning(f"Request timeout, retrying in {self.retry_delay}s")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    return {
                        "success": False,
                        "error": "Request timeout",
                        "attempt": attempt + 1
                    }
            
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "attempt": attempt + 1
                }
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def fetch_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _fetch_with_semaphore(url):
            async with semaphore:
                return await self.fetch_with_retry(url)
        
        tasks = [_fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)


# =============================================================================
# ASYNC FILE OPERATIONS
# =============================================================================

class AsyncFileProcessor:
    """
    Async file processing with streaming and batching.
    Demonstrates efficient async I/O patterns.
    """
    
    @staticmethod
    async def read_file_in_chunks(
        filepath: str,
        chunk_size: int = 8192
    ) -> async_data_generator:
        """Read file asynchronously in chunks."""
        async with aiofiles.open(filepath, 'rb') as file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    async def process_large_file(
        input_path: str,
        output_path: str,
        processor: Callable[[bytes], bytes]
    ) -> Dict[str, Any]:
        """Process large file asynchronously with progress tracking."""
        
        start_time = time.time()
        bytes_processed = 0
        
        async with aiofiles.open(input_path, 'rb') as infile, \
                   aiofiles.open(output_path, 'wb') as outfile:
            
            async for chunk in AsyncFileProcessor.read_file_in_chunks(input_path):
                processed_chunk = processor(chunk)
                await outfile.write(processed_chunk)
                bytes_processed += len(chunk)
                
                # Allow other tasks to run
                await asyncio.sleep(0)
        
        return {
            "bytes_processed": bytes_processed,
            "duration": time.time() - start_time,
            "throughput_mb_s": bytes_processed / (1024 * 1024) / (time.time() - start_time)
        }


# =============================================================================
# MIXING SYNC AND ASYNC CODE
# =============================================================================

class AsyncSyncBridge:
    """
    Bridge between sync and async code.
    Demonstrates advanced integration patterns.
    """
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_sync_in_async(self, func: Callable, *args, **kwargs) -> Any:
        """Run synchronous function in async context."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    def run_async_in_sync(self, coro: Awaitable) -> Any:
        """Run async coroutine in synchronous context."""
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we can't use run()
            raise RuntimeError("Cannot run async code from within async context")
        except RuntimeError:
            # No running loop, we can create one
            return asyncio.run(coro)
    
    async def mixed_operation(self, sync_func: Callable, async_func: Callable) -> Dict[str, Any]:
        """Demonstrate mixing sync and async operations."""
        
        # Run sync function in thread pool
        sync_result = await self.run_sync_in_async(sync_func)
        
        # Run async function normally
        async_result = await async_func()
        
        return {
            "sync_result": sync_result,
            "async_result": async_result
        }
    
    def cleanup(self):
        """Clean up thread pool."""
        self.executor.shutdown(wait=True)


# =============================================================================
# DEMONSTRATION AND TESTING
# =============================================================================

async def demonstrate_async_basics():
    """Demonstrate basic async patterns."""
    print("=== Basic Async Patterns ===")
    
    # Async context manager
    async with async_timer("Database operation"):
        async with AsyncDatabase("sqlite://memory") as db:
            result = await db.execute("SELECT * FROM users")
            print(f"Query result: {result}")


async def demonstrate_async_iteration():
    """Demonstrate async iteration patterns."""
    print("\n=== Async Iteration ===")
    
    # Async iterator
    print("1. Async Data Streaming:")
    streamer = AsyncDataStreamer("api_source", batch_size=5)
    batch_count = 0
    async for batch in streamer:
        batch_count += 1
        print(f"Batch {batch_count}: {len(batch)} items")
        if batch_count >= 3:  # Limit for demo
            break
    
    # Async generator
    print("\n2. Async Generator:")
    async for value in async_fibonacci_generator(10):
        print(f"Fibonacci: {value}")


async def demonstrate_concurrency():
    """Demonstrate advanced concurrency patterns."""
    print("\n=== Advanced Concurrency ===")
    
    # Worker pool
    async def slow_task(n: int) -> int:
        await asyncio.sleep(0.1)
        return n * n
    
    pool = AsyncWorkerPool(max_workers=5)
    
    start_time = time.time()
    results = await pool.map(slow_task, list(range(10)))
    duration = time.time() - start_time
    
    print(f"Processed 10 tasks in {duration:.3f}s: {results}")
    await pool.shutdown()
    
    # Task manager
    task_manager = AsyncTaskManager()
    
    async def example_task(delay: float, should_fail: bool = False):
        await asyncio.sleep(delay)
        if should_fail:
            raise ValueError("Task failed intentionally")
        return f"Success after {delay}s"
    
    tasks = [
        example_task(0.1, False),
        example_task(0.2, False),
        example_task(0.15, True),  # This will fail
    ]
    
    results = await task_manager.run_parallel_tasks(tasks, max_concurrent=2)
    
    print(f"\nTask Results:")
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.task_id}: {result.duration:.3f}s")


async def demonstrate_http_client():
    """Demonstrate async HTTP client."""
    print("\n=== Async HTTP Client ===")
    
    # Mock URLs for demonstration
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/500",  # Will trigger retry
    ]
    
    async with AsyncHTTPClient(timeout=5.0, max_retries=2) as client:
        # Single request
        result = await client.fetch_with_retry("https://httpbin.org/json")
        print(f"Single request: {result['success']}")
        
        # Multiple requests
        results = await client.fetch_multiple(urls[:2], max_concurrent=2)  # Limit for demo
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        print(f"Multiple requests: {successful}/{len(results)} successful")


def demonstrate_sync_async_bridge():
    """Demonstrate mixing sync and async code."""
    print("\n=== Sync/Async Bridge ===")
    
    def slow_sync_function(n: int) -> int:
        time.sleep(0.1)  # Simulate slow sync operation
        return n * 2
    
    async def fast_async_function() -> str:
        await asyncio.sleep(0.05)
        return "async result"
    
    async def mixed_demo():
        bridge = AsyncSyncBridge()
        
        result = await bridge.mixed_operation(
            lambda: slow_sync_function(42),
            fast_async_function
        )
        
        print(f"Mixed operation result: {result}")
        bridge.cleanup()
    
    # Run in sync context
    asyncio.run(mixed_demo())


async def main():
    """Main demonstration function."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run all demonstrations
    await demonstrate_async_basics()
    await demonstrate_async_iteration()
    await demonstrate_concurrency()
    
    # Note: HTTP demo requires internet connection
    # await demonstrate_http_client()
    
    print("\n=== Summary ===")
    print("✅ Async Context Managers: Proper resource management")
    print("✅ Async Iteration: Memory-efficient data streaming")
    print("✅ Concurrency Patterns: Worker pools and task management")
    print("✅ Error Handling: Robust async error patterns")
    print("✅ Performance: Concurrent execution and optimization")


if __name__ == "__main__":
    # Run async demonstration
    asyncio.run(main())
    
    # Run sync/async bridge demonstration
    demonstrate_sync_async_bridge()