#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel/CSVFile读取器
用于读取网站列表File
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Any, Union

from .logger import setup_logger


class ExcelReader:
    """Excel/CSVFile读取器 - 读取网站列表"""
    
    def __init__(self):
        self.logger = setup_logger('ExcelReader', console_output=False)
    
    def read_websites(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        从Excel/CSVFile中读取网站列表
        
        Args:
            file_path: File路径
        
        Returns:
            网站数据列表
        """
        file_path = Path(file_path)
        self.logger.info(f"Reading file: {file_path}")

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return []

        try:
            # 根据File扩展名选择读取方式
            if file_path.suffix.lower() == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_path.suffix.lower() == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            elif file_path.suffix.lower() == '.csv':
                # 读取CSVFile，自动Detect encoding
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='latin-1')
            else:
                self.logger.error(f"Unsupported file format: {file_path.suffix}")
                return []

            self.logger.info(f"Successfully read file, {len(df)} rows")

            # 解析网站数据
            websites = self._parse_website_data(df)

            self.logger.info(f"Parsed {len(websites)} valid websites")
            return websites

        except Exception as e:
            self.logger.error(f"Failed to read file: {e}")
            return []
    
    def _parse_website_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析网站数据"""
        websites = []
        
        # 识别列名
        column_mapping = self._identify_columns(df.columns.tolist())
        
        for index, row in df.iterrows():
            try:
                website_data = self._extract_website_info(row, column_mapping, index)
                if website_data and self._validate_website_data(website_data):
                    websites.append(website_data)
                    
            except Exception as e:
                self.logger.warning(f"Failed to parse row {index+1}: {e}")
        
        return websites
    
    def _identify_columns(self, columns: List[str]) -> Dict[str, str]:
        """识别列名对应的字段"""
        column_mapping = {}

        patterns = {
            'name': [r'name', r'网站名', r'站点名', r'名称', r'title', r'网站', r'website_name'],
            'url': [r'url', r'网址', r'链接', r'地址', r'domain', r'website', r'site'],
            'rank': [r'rank', r'排名', r'排序', r'序号', r'position', r'#'],
            'category': [r'category', r'分类', r'类别', r'类型', r'type'],
            'country': [r'country', r'国家', r'地区', r'region'],
            'traffic_tier': [r'traffic_tier', r'流量', r'traffic']
        }

        for col in columns:
            col_lower = col.lower().strip()
            for field, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, col_lower):
                        column_mapping[field] = col
                        break
                if field in column_mapping:
                    break

        return column_mapping
    
    def _extract_website_info(self, row: pd.Series, column_mapping: Dict[str, str], index: int) -> Dict[str, Any]:
        """从行数据中提取网站信息"""
        
        # 获取URL（必需字段）
        url = self._get_column_value(row, column_mapping, 'url')
        if not url:
            # 尝试从第一列获取
            for col in row.index:
                value = str(row[col]).strip()
                if value.startswith(('http://', 'https://', 'www.')):
                    url = value
                    break
        
        if not url:
            return None
        
        # 标准化URL
        url = self._normalize_url(url)
        
        website_data = {
            'name': self._get_column_value(row, column_mapping, 'name') or self._extract_domain_name(url),
            'domain': self._extract_domain_name(url),
            'url': url,
            'rank': self._get_numeric_value(row, column_mapping, 'rank', index + 1),
            'category': self._get_column_value(row, column_mapping, 'category') or 'unknown',
            'country': self._get_column_value(row, column_mapping, 'country') or 'unknown',
            'traffic_tier': self._get_column_value(row, column_mapping, 'traffic_tier') or 'unknown',
            'source_row': index + 1
        }
        
        return website_data
    
    def _get_column_value(self, row: pd.Series, column_mapping: Dict[str, str], field: str) -> str:
        """获取列值"""
        if field in column_mapping and column_mapping[field] in row.index:
            value = row[column_mapping[field]]
            if pd.notna(value):
                return str(value).strip()
        return ''
    
    def _get_numeric_value(self, row: pd.Series, column_mapping: Dict[str, str], field: str, default: int) -> int:
        """获取数值列值"""
        value_str = self._get_column_value(row, column_mapping, field)
        if value_str:
            try:
                # 移除逗号等分隔符
                value_str = value_str.replace(',', '').replace(' ', '')
                return int(float(value_str))
            except (ValueError, TypeError):
                pass
        return default
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        url = url.strip()
        
        # 移除尾部斜杠
        url = url.rstrip('/')
        
        # 如果没有协议，添加https://
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                url = 'https://www.' + url
        
        return url
    
    def _extract_domain_name(self, url: str) -> str:
        """从URL提取域名"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            
            # 移除www.前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
            
        except Exception:
            return url
    
    def _validate_website_data(self, website_data: Dict[str, Any]) -> bool:
        """验证网站数据是否有效"""
        if not website_data.get('url'):
            return False
        
        url = website_data['url']
        
        # 基本URL验证
        if not any(url.startswith(prefix) for prefix in ['http://', 'https://']):
            return False
        
        # 排除明显无效的URL
        invalid_patterns = ['example.com', 'test.com', 'localhost']
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
        
        return True






















