from loguru import logger
import sys
from pathlib import Path


def setup_logging():
    # Remove default handler
    logger.remove()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan> | {message}",
        colorize=True
    )
    
    logger.add(
        "logs/payment_app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    logger.add(
        "logs/errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} | {message}",
        rotation="5 MB",
        retention="2 weeks"
    )

def get_logger():
    """Get the configured logger"""
    return logger

# Make it easy to import
__all__ = ["logger", "setup_logging", "get_logger"]