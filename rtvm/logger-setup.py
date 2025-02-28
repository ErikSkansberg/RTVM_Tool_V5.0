# rtvm/utils/logger.py - Configures logging for the RTVM Tool

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """
    Configures and returns a logger for the application.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.expanduser("~"), ".rtvm_tool", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(logs_dir, f"rtvm_tool_{timestamp}.log")
    
    # Configure root logger
    logger = logging.getLogger()
    
    # Set the log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create a rotating file handler (10 MB max, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    
    # Set format for handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log startup information
    logger.info("Logging initialized")
    logger.debug(f"Log file: {log_file}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger.
    
    Args:
        name: The name for the logger
        
    Returns:
        A named logger instance
    """
    return logging.getLogger(name)
