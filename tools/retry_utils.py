"""
Retry utilities for API calls using tenacity
Handles transient errors, rate limits, and network issues
"""
import logging
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger(__name__)


def should_retry_http_error(exception):
    """
    Determine if an HTTP error should be retried
    
    Retry on:
    - Network errors (ConnectError, TimeoutException)
    - 5xx server errors (500, 502, 503, 504)
    - 429 rate limit errors
    
    Don't retry on:
    - 4xx client errors (400, 401, 403, 404) except 429
    """
    if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    
    if isinstance(exception, httpx.HTTPStatusError):
        status_code = exception.response.status_code
        # Retry on server errors (5xx) and rate limits (429)
        if status_code >= 500 or status_code == 429:
            return True
        # Don't retry on client errors (4xx) except 429
        return False
    
    return False


def retry_api_call(max_attempts=3, initial_wait=1, max_wait=10, multiplier=2):
    """
    Decorator for retrying API calls with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_wait: Initial wait time in seconds (default: 1)
        max_wait: Maximum wait time in seconds (default: 10)
        multiplier: Exponential multiplier (default: 2)
    
    Usage:
        @retry_api_call(max_attempts=3)
        async def my_api_call():
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    """
    return retry(
        # Stop after max_attempts total attempts (1 initial + retries)
        stop=stop_after_attempt(max_attempts),
        # Exponential backoff: 1s, 2s, 4s (or up to max_wait)
        wait=wait_exponential(
            multiplier=multiplier,
            min=initial_wait,
            max=max_wait
        ),

        retry=retry_if_exception_type(httpx.ConnectError) |
              retry_if_exception_type(httpx.TimeoutException) |
              
              retry_if_exception(should_retry_http_error),
    
        before_sleep=before_sleep_log(logger, logging.WARNING),
     
        after=after_log(logger, logging.ERROR),
 
        reraise=True
    )
