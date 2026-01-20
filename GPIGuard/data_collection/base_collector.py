#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Collector Base Class
All data collectors must inherit from this class and implement specified methods
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import time
from datetime import datetime

from .utils.logger import setup_logger
from .utils.path_manager import PathManager


class BaseCollector(ABC):
    """Data Collector Base Class"""
    
    def __init__(self, collector_type: str):
        """
        Initialize collector
        
        Args:
            collector_type: Collector type (html, api, reddit, twitter)
        """
        self.collector_type = collector_type
        self.logger = setup_logger(f'{self.__class__.__name__}')
        
        # Use unified Path Manager
        self.path_manager = PathManager()
        self.output_dir = self.path_manager.get_origin_data_dir(collector_type)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Collection statistics
        self.stats = {
            'total_items': 0,
            'successful_items': 0,
            'failed_items': 0,
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0
        }
        
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.logger.info(f"Output directory: {self.output_dir}")
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Execute data collection (must be implemented)
        
        Returns:
            Collection result dictionary containing:
                - success: Whether successful
                - file_count: Number of files collected
                - total_size: Total size (bytes)
                - output_dir: Output directory
                - stats: Statistics
                - message: Result message
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate whether configuration is valid (must be implemented)
        
        Returns:
            Whether configuration is valid
        """
        pass
    
    def get_config_path(self, config_name: str) -> Path:
        """Get configuration file path"""
        return self.path_manager.get_config_dir() / config_name
    
    def start_collection(self):
        """Start collection, record start time"""
        self.stats['start_time'] = time.time()
        self.logger.info(f"Starting data collection for {self.collector_type}")
    
    def end_collection(self):
        """End collection, record end time"""
        self.stats['end_time'] = time.time()
        if self.stats['start_time']:
            self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']
        self.logger.info(f"Collection completed in {self.stats['duration_seconds']:.2f} seconds")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return self.stats.copy()
    
    def log_summary(self):
        """Log collection summary"""
        self.logger.info("="*60)
        self.logger.info(f"Collection Summary - {self.collector_type.upper()}")
        self.logger.info("="*60)
        self.logger.info(f"Total items: {self.stats['total_items']}")
        self.logger.info(f"Successful: {self.stats['successful_items']}")
        self.logger.info(f"Failed: {self.stats['failed_items']}")
        self.logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info("="*60)
    
    def increment_success(self):
        """Increment success count"""
        self.stats['successful_items'] += 1
    
    def increment_failure(self):
        """Increment failure count"""
        self.stats['failed_items'] += 1
    
    def set_total_items(self, count: int):
        """Set total items count"""
        self.stats['total_items'] = count
    
    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.collector_type}, output={self.output_dir})"






















