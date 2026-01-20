#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel/CSV File Reader
For reading website list files
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Any, Union

from .logger import setup_logger


class ExcelReader:
    """Excel/CSV File Reader - Read website list"""
    
    def __init__(self):
        self.logger = setup_logger('ExcelReader', console_output=False)
    
    def read_websites(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Read website list from Excel/CSV file
        
        Args:
            file_path: File path
        
        Returns:
            Website data list
        """
        file_path = Path(file_path)
        self.logger.info(f"Reading file: {file_path}")

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return []

        try:
            # Select read method based on file extension
            if file_path.suffix.lower() == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_path.suffix.lower() == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            elif file_path.suffix.lower() == '.csv':
                # Read CSV file, auto-detect encoding
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
            websites = self._parse_website_data(df)

            self.logger.info(f"Parsed {len(websites)} valid websites")
            return websites

        except Exception as e:
            self.logger.error(f"Failed to read file: {e}")
            return []
    
    def _parse_website_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse website data"""
        websites = []
        
        # Identify column names
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
        """Identify column names mapping to fields"""
        column_mapping = {}

        patterns = {
            'name': [r'name', r'website name', r'site name', r'title', r'website'],
            'url': [r'url', r'website address', r'link', r'address', r'domain', r'website', r'site'],
            'rank': [r'rank', r'ranking', r'order', r'number', r'position', r'#'],
            'category': [r'category', r'categories', r'type', r'classification'],
            'country': [r'country', r'region', r'location'],
            'traffic_tier': [r'traffic_tier', r'traffic', r'volume']
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
        """Extract website information from row data"""
        
        # Get URL (required field)
        url = self._get_column_value(row, column_mapping, 'url')
        if not url:
            # Try to get from first column
            for col in row.index:
                value = str(row[col]).strip()
                if value.startswith(('http://', 'https://', 'www.')):
                    url = value
                    break
        
        if not url:
            return None
        
        # Normalize URL
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
        """Get column value"""
        if field in column_mapping and column_mapping[field] in row.index:
            value = row[column_mapping[field]]
            if pd.notna(value):
                return str(value).strip()
        return ''
    
    def _get_numeric_value(self, row: pd.Series, column_mapping: Dict[str, str], field: str, default: int) -> int:
        """Get numeric column value"""
        value_str = self._get_column_value(row, column_mapping, field)
        if value_str:
            try:
                # Remove comma and space separators
                value_str = value_str.replace(',', '').replace(' ', '')
                return int(float(value_str))
            except (ValueError, TypeError):
                pass
        return default
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL"""
        url = url.strip()
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Add https:// if no protocol
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                url = 'https://www.' + url
        
        return url
    
    def _extract_domain_name(self, url: str) -> str:
        """Extract domain name from URL"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
            
        except Exception:
            return url
    
    def _validate_website_data(self, website_data: Dict[str, Any]) -> bool:
        """Validate if website data is valid"""
        if not website_data.get('url'):
            return False
        
        url = website_data['url']
        
        # Basic URL validation
        if not any(url.startswith(prefix) for prefix in ['http://', 'https://']):
            return False
        
        # Exclude obviously invalid URLs
        invalid_patterns = ['example.com', 'test.com', 'localhost']
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
        
        return True























