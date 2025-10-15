"""Prometheus metrics middleware for monitoring and observability."""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator


# ============================================================================
# Custom Application Metrics
# ============================================================================

# Request metrics
REQUEST_COUNT = Counter(
    'model_catalog_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'model_catalog_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

# Recommendation metrics
RECOMMENDATION_COUNT = Counter(
    'model_catalog_recommendations_total',
    'Total recommendation requests',
    ['use_case', 'cache_hit']
)

RECOMMENDATION_DURATION = Histogram(
    'model_catalog_recommendation_duration_seconds',
    'Time to generate recommendations',
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# Cache metrics
CACHE_HIT_RATE = Gauge(
    'model_catalog_cache_hit_rate_percent',
    'Cache hit rate percentage'
)

CACHE_OPERATIONS = Counter(
    'model_catalog_cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

# Model metrics
MODELS_TOTAL = Gauge(
    'model_catalog_models_total',
    'Total number of models in catalog'
)

BENCHMARK_RESULTS_TOTAL = Gauge(
    'model_catalog_benchmark_results_total',
    'Total number of benchmark results'
)

# Hardware metrics
GPU_CONFIGS_TOTAL = Gauge(
    'model_catalog_gpu_configs_total',
    'Total number of GPU configurations'
)

# Application info
APP_INFO = Info(
    'model_catalog_app',
    'Application information'
)


def setup_metrics(app):
    """Setup Prometheus metrics instrumentation.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        FastAPI app with metrics instrumentation
    """
    # Setup instrumentator with custom configuration
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="model_catalog_inprogress",
        inprogress_labels=True,
    )
    
    # Instrument the app
    instrumentator.instrument(app)
    
    # Expose metrics endpoint at /metrics
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    
    # Set application info
    try:
        from src.core.config import settings
        APP_INFO.info({
            'version': settings.VERSION,
            'app_name': settings.APP_NAME,
            'python_version': '3.11+'
        })
    except Exception:
        pass
    
    return app


def update_cache_metrics(hit_rate: float):
    """Update cache hit rate metric.
    
    Args:
        hit_rate: Cache hit rate percentage (0-100)
    """
    CACHE_HIT_RATE.set(hit_rate)


def record_cache_operation(operation: str, result: str):
    """Record a cache operation.
    
    Args:
        operation: Operation type (get, set, delete)
        result: Operation result (hit, miss, error)
    """
    CACHE_OPERATIONS.labels(operation=operation, result=result).inc()


def record_recommendation(use_case: str, cache_hit: bool, duration: float):
    """Record a recommendation request.
    
    Args:
        use_case: Use case category
        cache_hit: Whether result came from cache
        duration: Time taken in seconds
    """
    RECOMMENDATION_COUNT.labels(
        use_case=use_case,
        cache_hit='true' if cache_hit else 'false'
    ).inc()
    
    RECOMMENDATION_DURATION.observe(duration)

