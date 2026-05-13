"""
Logging system for the application
"""

import logging
import logging.handlers
from pathlib import Path
from config.constants import (
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)
from utils.paths import get_logs_dir


def setup_logger(name: str = None) -> logging.Logger:
    """
    Setup application logger with file and console handlers
    
    Args:
        name: Logger name (default: root logger)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Ensure logs directory exists
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    log_file = log_dir / LOG_FILE_NAME
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
