import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import os
from typing import Optional

def setup_logging(name: str = None, log_file: Optional[Path] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        log_file: Path to log file
        log_level: Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name or __name__)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    # Clear existing handlers to prevent duplicate logging
    if logger.handlers:
        logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified and directory exists
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Use different file handler based on platform
            if os.name == 'nt':  # Windows
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
            else:  # Unix-like systems
                file_handler = WatchedFileHandler(str(log_file))
                
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # Log to console if can't create log file
            logger.warning(f"Could not set up file logging: {e}")

    return logger

