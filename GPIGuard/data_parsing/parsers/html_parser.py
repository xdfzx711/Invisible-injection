#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML Data Parsing器
从HTMLFile中提取文本内容
"""

from pathlib import Path
from typing import Dict, Any, List
import re
import html

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import TextExtractor, FileUtils


class HTMLParser(BaseParser):
    """HTMLFile解析器（兼容旧格式）"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('html', enable_interference_filter, filter_config)
        
        if not BS4_AVAILABLE:
            self.logger.warning("BeautifulSoup4 not available, will use basic text extraction")
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析单个HTMLFile
        
        Args:
            file_path: HTMLFile路径
        
        Returns:
            Parsing result dictionary (compatible with old format)
        """
        self.logger.info(f"Parsing HTML file: {file_path}")
        
        try:
            # 读取File内容
            content = FileUtils.safe_read_file(file_path)
            
            # 提取文本entries目
            text_entries = []
            
            if BS4_AVAILABLE:
                self._extract_with_bs4(content, text_entries)
            else:
                self._extract_basic(content, text_entries)
            
            # 构建解析结果（与旧格式相同）
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'html',
                    'total_text_entries': len(text_entries),
                    'html_length': len(content),
                    'encoding': FileUtils.detect_encoding(file_path),
                    'extraction_method': 'beautifulsoup4' if BS4_AVAILABLE else 'basic'
                },
                'text_entries': text_entries
            }
            
            self.logger.info(f"Successfully parsed {file_path.name}: {len(text_entries)} text entries")
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_error_result(file_path, f"解析Error: {e}")
    
    def _extract_with_bs4(self, html_content: str, entries: List[Dict]):
        """使用BeautifulSoup提取文本（兼容旧格式）"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除script和style标签
        for script in soup(['script', 'style']):
            script.decompose()
        
        # 提取文本节点
        text = soup.get_text(separator='\n')
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if line and len(line) > 2:
                entries.append({
                    'line_number': line_num,
                    'value': line,
                    'field_type': 'text',
                    'length': len(line)
                })
    
    def _extract_basic(self, html_content: str, entries: List[Dict]):
        """基础文本提取（兼容旧格式）"""
        # 移除script和style标签
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # HTML实体解码
        text = html.unescape(text)
        
        # 分行并清理
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if line and len(line) > 2:
                entries.append({
                    'line_number': line_num,
                    'value': line,
                    'field_type': 'text',
                    'length': len(line)
                })
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """获取所有HTMLFile"""
        html_files = list(directory.glob('*.html'))
        htm_files = list(directory.glob('*.htm'))
        return html_files + htm_files
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """创建Error结果"""
        return {
            'file_info': FileUtils.get_file_info(file_path),
            'parsing_info': {
                'parser_type': 'html',
                'status': 'failed',
                'error': error_message
            },
            'text_entries': []
        }
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """解析整个directory（单File单独保存）"""
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        print(f"\n找到 {len(files)} 个HTMLFile待解析")
        
        self.stats['total_files'] = len(files)
        results = []
        
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] 解析: {file_path.name}")
                result = self.parse_file(file_path)
                
                if result and result.get('parsing_info', {}).get('status') != 'failed':
                    output_filename = f"{file_path.stem}_parsed.json"
                    output_path = self.output_dir / output_filename
                    self.save_parsed_data(result, output_path)
                    
                    results.append(result)
                    self.stats['successful_files'] += 1
                    self.stats['total_texts_extracted'] += len(result.get('text_entries', []))
                    print(f"  成功: {len(result.get('text_entries', []))} 个文本entries目")
                else:
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
        
        return results
