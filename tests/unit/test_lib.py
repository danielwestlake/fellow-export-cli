"""Unit tests for library utilities."""
import pytest
import time
from src.lib.rate_limiter import RateLimiter
from src.lib.retry import exponential_backoff, retry_on_error


def test_rate_limiter_basic():
    """Test rate limiter delays requests appropriately."""
    limiter = RateLimiter(requests_per_second=10.0)
    
    start_time = time.time()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.time() - start_time
    
    # Should take at least 0.1 seconds for second request
    assert elapsed >= 0.09  # Small margin for timing


def test_rate_limiter_reset():
    """Test rate limiter reset functionality."""
    limiter = RateLimiter(requests_per_second=10.0)
    
    limiter.acquire()
    limiter.reset()
    
    # After reset, should not delay
    start_time = time.time()
    limiter.acquire()
    elapsed = time.time() - start_time
    
    assert elapsed < 0.01


def test_exponential_backoff():
    """Test exponential backoff calculation."""
    assert exponential_backoff(0) == 2.0
    assert exponential_backoff(1) == 4.0
    assert exponential_backoff(2) == 8.0
    assert exponential_backoff(3) == 16.0
    assert exponential_backoff(10) == 60.0  # Max delay


def test_retry_decorator_success():
    """Test retry decorator with successful function."""
    call_count = 0
    
    @retry_on_error(max_retries=3)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_decorator_eventual_success():
    """Test retry decorator with eventual success."""
    call_count = 0
    
    @retry_on_error(max_retries=3, retryable_exceptions=[ValueError])
    def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"
    
    result = eventually_successful()
    assert result == "success"
    assert call_count == 3


def test_retry_decorator_max_retries():
    """Test retry decorator respects max retries."""
    call_count = 0
    
    @retry_on_error(max_retries=3, retryable_exceptions=[ValueError])
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Persistent error")
    
    with pytest.raises(ValueError):
        always_fails()
    
    assert call_count == 3
