import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name):
    """Set up logger with rotating file handler"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create rotating file handler
    handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger