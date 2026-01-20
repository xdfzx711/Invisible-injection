#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Logger Manager
All modules use unified logging configuration
"""

import logging
from pathlib import Path
from typing import Optional
from .path_manager import PathManager


def setup_logger(name: str, 
                log_file: Optional[str] = None,
                level: int = logging.INFO,
                console_output: bool = True) -> logging.Logger:
    """
    Setup standardized logger
    
    Args:
        name: Logger name
        log_file: Log file name (optional, defaults to name.log)
        level: Log level
        console_output: Whether to output to console
    
    Returns:
        Configured logger object
    """
    # Get unified log directory
    path_manager = PathManager()
    log_dir = path_manager.get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine log file path
    if log_file is None:
        log_file = f"{name.lower().replace(' ', '_')}.log"
    log_path = log_dir / log_file
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Filehandler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger
    
    Args:
        name: Logger name
    
    Returns:
        Logger object
    """
    return logging.getLogger(name)






















