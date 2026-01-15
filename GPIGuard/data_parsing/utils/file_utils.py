#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File处理工具
用于File编码检测、读取等操作
"""

import chardet
from pathlib import Path
from typing import Optional, Union, Dict, Any


class FileUtils:
    """File处理工具类"""
    
    @staticmethod
    def detect_encoding(file_path: Union[str, Path]) -> str:
        """
        检测File编码
        
        Args:
            file_path: File路径
        
        Returns:
            检测到的编码
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10KB用于检测
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # 如果置信度太低，默认使用utf-8
                if confidence < 0.7:
                    encoding = 'utf-8'
                    
                return encoding
        except Exception:
            return 'utf-8'
    
    @staticmethod
    def safe_read_file(file_path: Union[str, Path], 
                      encoding: Optional[str] = None) -> str:
        """
        安全读取File内容
        
        Args:
            file_path: File路径
            encoding: 指定编码，None则自动检测
        
        Returns:
            File内容
        """
        if encoding is None:
            encoding = FileUtils.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # 如果指定编码Failed，尝试其他常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # 最后尝试忽略Error
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取File基本信息
        
        Args:
            file_path: File路径
        
        Returns:
            File信息字典
        """
        file_path = Path(file_path)
        stat = file_path.stat()
        
        return {
            'name': file_path.name,
            'size': stat.st_size,
            'extension': file_path.suffix,
            'modified_time': stat.st_mtime,
            'path': str(file_path)
        }





















