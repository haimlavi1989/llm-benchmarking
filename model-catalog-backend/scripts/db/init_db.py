#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import create_engine, text
from src.core.config import settings


async def init_database():
    """Initialize the database."""
    print("🔄 Initializing database...")
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Run Alembic migrations
        print("🔄 Running database migrations...")
        os.system("alembic upgrade head")
        print("✅ Database migrations completed")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    print("🎉 Database initialization completed successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
