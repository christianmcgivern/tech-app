"""Logging utilities for the AI-Powered Technician Workflow System."""

import logging
from rich.logging import RichHandler
import os

def setup_logger(name):
    """Set up a logger with the specified name."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        
        handler = RichHandler(rich_tracebacks=True)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 