#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本提取工具
从各种数据结构中提取文本内容
"""

import re
from typing import List, Any, Dict, Union


class TextExtractor:
    """文本提取工具类"""
    
    @staticmethod
    def extract_from_dict(data: Dict[str, Any], 
                         skip_keys: List[str] = None,
                         max_depth: int = 10) -> List[str]:
        """
        从字典中递归提取所有文本
        
        Args:
            data: 字典数据
            skip_keys: 要跳过的键名列表
            max_depth: 最大递归深度
        
        Returns:
            提取的文本列表
        """
        if skip_keys is None:
            skip_keys = ['id', 'url', 'link', 'href', 'timestamp', 'created_at', 'updated_at']
        
        texts = []
        
        def _extract(obj, depth=0):
            if depth > max_depth:
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in skip_keys:
                        continue
                    _extract(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _extract(item, depth + 1)
            elif isinstance(obj, str):
                # 提取非空字符串
                text = obj.strip()
                if text and not TextExtractor.is_url(text):
                    texts.append(text)
            elif obj is not None:
                # 其他类型转换为字符串
                text = str(obj).strip()
                if text:
                    texts.append(text)
        
        _extract(data)
        return texts
    
    @staticmethod
    def extract_from_list(data: List[Any]) -> List[str]:
        """
        从列表中提取所有文本
        
        Args:
            data: 列表数据
        
        Returns:
            提取的文本列表
        """
        texts = []
        for item in data:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    texts.append(text)
            elif isinstance(item, dict):
                texts.extend(TextExtractor.extract_from_dict(item))
            elif isinstance(item, list):
                texts.extend(TextExtractor.extract_from_list(item))
        return texts
    
    @staticmethod
    def is_url(text: str) -> bool:
        """判断文本是否为URL"""
        return bool(re.match(r'https?://', text))
    
    @staticmethod
    def is_email(text: str) -> bool:
        """判断文本是否为邮箱地址"""
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
        
        Returns:
            清理后的文本
        """
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        text = text.strip()
        return text
    
    @staticmethod
    def filter_texts(texts: List[str], 
                    min_length: int = 1,
                    max_length: int = 10000,
                    remove_duplicates: bool = True) -> List[str]:
        """
        过滤文本列表
        
        Args:
            texts: 文本列表
            min_length: 最小文本长度
            max_length: 最大文本长度
            remove_duplicates: 是否去重
        
        Returns:
            过滤后的文本列表
        """
        # 清理和过滤
        filtered = []
        seen = set()
        
        for text in texts:
            text = TextExtractor.clean_text(text)
            
            # 长度过滤
            if len(text) < min_length or len(text) > max_length:
                continue
            
            # 去重
            if remove_duplicates:
                if text in seen:
                    continue
                seen.add(text)
            
            filtered.append(text)
        
        return filtered
    
    @staticmethod
    def identify_field_type(field_name: str, value: str) -> str:
        """
        识别字段类型
        
        Args:
            field_name: 字段名
            value: 字段值
        
        Returns:
            字段类型
        """
        field_name_lower = field_name.lower()
        
        # URL类型
        if TextExtractor.is_url(value):
            return 'url'
        
        # 邮箱类型
        if TextExtractor.is_email(value):
            return 'email'
        
        # 根据字段名判断
        if any(keyword in field_name_lower for keyword in ['name', 'title', 'label']):
            return 'name'
        elif any(keyword in field_name_lower for keyword in ['url', 'link', 'href']):
            return 'url'
        elif any(keyword in field_name_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in field_name_lower for keyword in ['city', 'country', 'location']):
            return 'location'
        elif any(keyword in field_name_lower for keyword in ['user', 'login', 'username']):
            return 'username'
        elif any(keyword in field_name_lower for keyword in ['desc', 'description', 'content', 'body', 'text']):
            return 'description'
        elif any(keyword in field_name_lower for keyword in ['date', 'time', 'created', 'updated']):
            return 'datetime'
        elif any(keyword in field_name_lower for keyword in ['id', 'key', 'code']):
            return 'identifier'
        else:
            return 'text'





















