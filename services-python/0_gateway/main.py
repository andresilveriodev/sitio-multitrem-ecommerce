"""
Main entry point para o Gateway Service
"""

import uvicorn
from config import settings
from app import app

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
