#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志管理器
所有模块使用统一的日志配置
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
    设置标准化的日志器
    
    Args:
        name: 日志器名称
        log_file: 日志File名（可选，默认使用name.log）
        level: 日志级别
        console_output: 是否输出到控制台
    
    Returns:
        配置好的logger对象
    """
    # 获取统一的Log directory
    path_manager = PathManager()
    log_dir = path_manager.get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 确定日志File路径
    if log_file is None:
        log_file = f"{name.lower().replace(' ', '_')}.log"
    log_path = log_dir / log_file
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # Filehandler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(level)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台handler（可选）
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取has beenexists的logger
    
    Args:
        name: logger名称
    
    Returns:
        logger对象
    """
    return logging.getLogger(name)






















