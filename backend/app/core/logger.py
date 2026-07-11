"""
Module establishing structured logging configurations for the Nexus AI Operations Platform.

Produces JSON structured logs in production environments and highly readable,
monospaced log line formats during development / debug sessions.
"""

import logging
import sys
import json
from typing import Any, Dict
from datetime import datetime, timezone
from app.core.config import settings


class StructuredJSONFormatter(logging.Formatter):
    """
    Log formatter that outputs dictionary records serialized as single-line JSON.
    
    Perfect for Cloud Logging aggregates (GCP Logging, Datadog, Grafana Loki).
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "line_number": record.lineno,
        }
        
        # Include additional extra values attached to the LogRecord dict if any
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_payload.update(record.extra_fields)
            
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_payload)


def configure_logger() -> logging.Logger:
    """
    Configures and establishes the application-wide root logging system.
    
    Returns:
        A fully configured logging.Logger instance.
    """
    logger = logging.getLogger("nexus_ai")
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Avoid duplicate duplicate log bindings if handlers are already configured
    if logger.handlers:
        return logger
        
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.DEBUG:
        # Development Monospaced Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Production JSON Formatter
        formatter = StructuredJSONFormatter()
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Optional: silence default external logging verbose handlers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return logger


# Instantiate application singleton logger
logger = configure_logger()
