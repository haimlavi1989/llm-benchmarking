"""Cache decorators for automatic caching."""

import functools
import hashlib
from typing import Any, Callable, Optional, Union
from datetime import timedelta

from .redis_cache import cache


def cache_result(
    ttl: Optional[Union[int, timedelta]] = None,
    key_prefix: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds or timedelta
        key_prefix: Prefix for cache key
        key_func: Custom function to generate cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(
    key_pattern: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        key_pattern: Pattern to match keys for invalidation
        key_func: Custom function to generate cache key pattern
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Execute function
            result = func(*args, **kwargs)
            
            # Invalidate cache
            if key_func:
                pattern = key_func(*args, **kwargs)
            elif key_pattern:
                pattern = key_pattern
            else:
                pattern = _generate_cache_key(func, args, kwargs)
            
            cache.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func: Callable, 
    args: tuple, 
    kwargs: dict, 
    prefix: Optional[str] = None
) -> str:
    """Generate a cache key for function arguments."""
    # Create a string representation of arguments
    args_str = str(args) + str(sorted(kwargs.items()))
    
    # Create hash of arguments
    args_hash = hashlib.md5(args_str.encode()).hexdigest()
    
    # Generate cache key
    func_name = func.__name__
    module_name = func.__module__
    
    if prefix:
        return f"{prefix}:{module_name}:{func_name}:{args_hash}"
    else:
        return f"{module_name}:{func_name}:{args_hash}"


# Specialized cache decorators for common use cases

def cache_model_recommendations(ttl: Union[int, timedelta] = 300):  # 5 minutes
    """Cache model recommendations with default TTL."""
    return cache_result(ttl=ttl, key_prefix="recommendations")


def cache_benchmark_results(ttl: Union[int, timedelta] = 1800):  # 30 minutes
    """Cache benchmark results with default TTL."""
    return cache_result(ttl=ttl, key_prefix="benchmarks")


def cache_model_details(ttl: Union[int, timedelta] = 3600):  # 1 hour
    """Cache model details with default TTL."""
    return cache_result(ttl=ttl, key_prefix="models")


def invalidate_recommendations():
    """Invalidate recommendation cache."""
    return invalidate_cache(key_pattern="recommendations:*")


def invalidate_benchmarks():
    """Invalidate benchmark cache."""
    return invalidate_cache(key_pattern="benchmarks:*")


def invalidate_models():
    """Invalidate model cache."""
    return invalidate_cache(key_pattern="models:*")
