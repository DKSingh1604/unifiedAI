#!/usr/bin/env python3
"""
Script to start the FastAPI server
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 80)
    print("Starting Electric Vehicle Analytics API")
    print("=" * 80)
    print(f"Host: {settings.api_host}")
    print(f"Port: {settings.api_port}")
    print(f"API Docs: http://{settings.api_host}:{settings.api_port}/api/docs")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
