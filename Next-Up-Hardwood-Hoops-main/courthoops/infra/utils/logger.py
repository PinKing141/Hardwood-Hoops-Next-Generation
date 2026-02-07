import logging
from typing import Optional


def get_logger(name: str, level: int = logging.INFO, filename: Optional[str] = None) -> logging.Logger:
    """
    Configures and returns a logger with an optional file handler.
    Keeping logging centralized avoids ad-hoc setups across layers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.FileHandler(filename) if filename else logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


