"""
Server startup script bootstrapping the ASGI web application interface.

Utilizes Uvicorn to run the FastAPI app instance, dynamically resolving port and debug settings
from the central Config settings module.
"""

import uvicorn
from app.core.config import settings
from app.core.logger import logger


def start_server() -> None:
    """
    Launches the Uvicorn application server instance based on settings configurations.
    """
    host = "127.0.0.1" if settings.DEBUG else "0.0.0.0"
    port = settings.PORT
    
    logger.info(f"Starting Nexus AI Operations Platform on http://{host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="warning" if not settings.DEBUG else "debug",
    )


if __name__ == "__main__":
    start_server()
