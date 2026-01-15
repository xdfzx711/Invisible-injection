#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据收集器基类
所有数据收集器必须继承此类并实现指定方法
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import time
from datetime import datetime

from .utils.logger import setup_logger
from .utils.path_manager import PathManager


class BaseCollector(ABC):
    """数据收集器基类"""
    
    def __init__(self, collector_type: str):
        """
        初始化收集器
        
        Args:
            collector_type: 收集器类型 (html, api, reddit, twitter)
        """
        self.collector_type = collector_type
        self.logger = setup_logger(f'{self.__class__.__name__}')
        
        # 使用统一的Path Manager
        self.path_manager = PathManager()
        self.output_dir = self.path_manager.get_origin_data_dir(collector_type)
        
        # 确保Output directoryexists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 收集统计
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
        执行数据收集（必须实现）
        
        Returns:
            收集结果字典，包含:
                - success: 是否成功
                - file_count: 收集的File数量
                - total_size: 总大小（字节）
                - output_dir: Output directory
                - stats: Statistics
                - message: 结果消息
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效（必须实现）
        
        Returns:
            配置是否有效
        """
        pass
    
    def get_config_path(self, config_name: str) -> Path:
        """获取配置File路径"""
        return self.path_manager.get_config_dir() / config_name
    
    def start_collection(self):
        """开始收集，记录开始时间"""
        self.stats['start_time'] = time.time()
        self.logger.info(f"Starting data collection for {self.collector_type}")
    
    def end_collection(self):
        """结束收集，记录结束时间"""
        self.stats['end_time'] = time.time()
        if self.stats['start_time']:
            self.stats['duration_seconds'] = self.stats['end_time'] - self.stats['start_time']
        self.logger.info(f"Collection completed in {self.stats['duration_seconds']:.2f} seconds")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取收集统计"""
        return self.stats.copy()
    
    def log_summary(self):
        """记录收集摘要"""
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
        """增加成功计数"""
        self.stats['successful_items'] += 1
    
    def increment_failure(self):
        """增加Failed计数"""
        self.stats['failed_items'] += 1
    
    def set_total_items(self, count: int):
        """设置总项目数"""
        self.stats['total_items'] = count
    
    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.collector_type}, output={self.output_dir})"






















