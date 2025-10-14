"""Repository layer for data access abstraction."""

from .protocols import (
    BaseRepositoryProtocol,
    ModelRepositoryProtocol,
    BenchmarkRepositoryProtocol,
    HardwareRepositoryProtocol,
)
from .base_repository import BaseRepository
from .model_repository import ModelRepository
from .benchmark_repository import BenchmarkRepository
from .hardware_repository import HardwareRepository

__all__ = [
    # Protocols
    "BaseRepositoryProtocol",
    "ModelRepositoryProtocol",
    "BenchmarkRepositoryProtocol",
    "HardwareRepositoryProtocol",
    # Implementations
    "BaseRepository",
    "ModelRepository",
    "BenchmarkRepository",
    "HardwareRepository",
]
