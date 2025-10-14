"""API layer with routes, dependencies, and middleware."""

from .dependencies import (
    get_db,
    get_model_repository,
    get_benchmark_repository,
    get_hardware_repository,
    get_model_service,
    get_current_user,
)

__all__ = [
    "get_db",
    "get_model_repository",
    "get_benchmark_repository",
    "get_hardware_repository",
    "get_model_service",
    "get_current_user",
]
