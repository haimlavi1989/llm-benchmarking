"""Main application entry point for LLM Benchmarking Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings

# Create FastAPI application
app = FastAPI(
    title="LLM Benchmarking Platform - Model Catalog Backend",
    description="A comprehensive backend service for large-scale AI model performance testing and cataloging with 9,000+ configurations per model",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LLM Benchmarking Platform API", 
        "version": "0.1.0",
        "description": "Large-scale AI model performance testing and cataloging with 9,000+ configurations per model"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
