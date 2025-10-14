"""Main FastAPI application for LLM Benchmarking Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.api.v1.routes import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive backend service for large-scale AI model performance testing and cataloging with 9,000+ configurations per model",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - API information."""
    return JSONResponse({
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "description": "LLM Benchmarking Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "api_v1": settings.API_V1_STR
    })


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("=" * 80)
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION}")
    print("=" * 80)
    print(f"📊 API Documentation: http://localhost:8000/docs")
    print(f"📚 ReDoc: http://localhost:8000/redoc")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print(f"🌐 API prefix: {settings.API_V1_STR}")
    print("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print(f"\n👋 {settings.APP_NAME} shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
