"""Custom exceptions for the LLM Benchmarking Platform."""


class ModelCatalogException(Exception):
    """Base exception for model catalog operations."""
    pass


class ModelNotFoundError(ModelCatalogException):
    """Raised when a model is not found."""
    pass


class BenchmarkError(ModelCatalogException):
    """Raised when benchmark operations fail."""
    pass


class HardwareConfigError(ModelCatalogException):
    """Raised when hardware configuration is invalid."""
    pass


class VRAMCalculationError(ModelCatalogException):
    """Raised when VRAM calculation fails."""
    pass


class TOPSISCalculationError(ModelCatalogException):
    """Raised when TOPSIS algorithm fails."""
    pass


class CacheError(ModelCatalogException):
    """Raised when cache operations fail."""
    pass


class RecommendationError(ModelCatalogException):
    """Raised when recommendation generation fails."""
    pass
