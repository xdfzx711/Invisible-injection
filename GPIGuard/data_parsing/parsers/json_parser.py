#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON数据解析器
解析JSON格式的数据File
"""

import json
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import TextExtractor, FileUtils


class JSONParser(BaseParser):
    """JSONFile解析器"""
    
    def __init__(self):
        super().__init__('json')
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析单个JSONFile
        
        Args:
            file_path: JSONFile路径
        
        Returns:
            Parsing result dictionary (compatible with old format)
        """
        self.logger.info(f"Parsing JSON file: {file_path}")
        
        try:
            # 读取File内容
            content = FileUtils.safe_read_file(file_path)
            
            # 解析JSON
            data = json.loads(content)
            
            # 提取文本entries目（保留详细结构，兼容旧格式）
            text_entries = []
            self._extract_text_recursive(data, text_entries, "")
            
            # 构建解析结果（与旧格式完全相同）
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'json',
                    'total_text_entries': len(text_entries),
                    'json_structure_depth': self._calculate_depth(data),
                    'encoding': FileUtils.detect_encoding(file_path)
                },
                'text_entries': text_entries
            }
            
            self.logger.info(f"Successfully parsed {file_path.name}: {len(text_entries)} text entries")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            return self._create_error_result(file_path, f"JSON格式Error: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_error_result(file_path, f"解析Error: {e}")
    
    def _extract_text_recursive(self, obj: Any, text_entries: List[Dict], json_path: str, parent_key: str = ""):
        """递归提取JSON中的所有文本内容（兼容旧格式）"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{json_path}.{key}" if json_path else key
                
                # 如果键本身包含文本，也要提取
                if isinstance(key, str) and key.strip():
                    text_entries.append({
                        'json_path': f"{json_path}.<key>",
                        'value': key,
                        'field_type': 'json_key',
                        'parent_key': parent_key,
                        'value_type': 'string',
                        'is_key': True
                    })
                
                self._extract_text_recursive(value, text_entries, current_path, key)
                
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                current_path = f"{json_path}[{index}]"
                self._extract_text_recursive(item, text_entries, current_path, parent_key)
                
        elif isinstance(obj, str) and obj.strip():
            # 提取字符串值
            text_entries.append({
                'json_path': json_path,
                'value': obj,
                'field_type': TextExtractor.identify_field_type(parent_key, obj),
                'parent_key': parent_key,
                'value_type': 'string',
                'is_key': False,
                'length': len(obj)
            })
        
        elif isinstance(obj, (int, float, bool)) and obj is not None:
            # 提取数值和布尔值
            text_entries.append({
                'json_path': json_path,
                'value': str(obj),
                'field_type': TextExtractor.identify_field_type(parent_key, str(obj)),
                'parent_key': parent_key,
                'value_type': type(obj).__name__,
                'is_key': False,
                'length': len(str(obj))
            })
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """获取所有JSONFile"""
        return list(directory.glob('*.json'))
    
    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """计算JSON结构的深度"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """创建Error结果"""
        return {
            'file_info': FileUtils.get_file_info(file_path),
            'parsing_info': {
                'parser_type': 'json',
                'status': 'failed',
                'error': error_message
            },
            'text_entries': []
        }
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """
        解析整个directory（重写以支持单File单独保存）
        
        Args:
            directory: directory路径
        
        Returns:
            解析结果列表
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\n找到 {len(files)} 个JSONFile待解析")
        
        self.stats['total_files'] = len(files)
        self.stats['start_time'] = Path(__file__).parent
        
        results = []
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] 解析: {file_path.name}")
                result = self.parse_file(file_path)
                
                if result and result.get('parsing_info', {}).get('status') != 'failed':
                    # 单独保存每个File的解析结果
                    output_filename = f"{file_path.stem}_parsed.json"
                    output_path = self.output_dir / output_filename
                    self.save_parsed_data(result, output_path)
                    
                    results.append(result)
                    self.stats['successful_files'] += 1
                    self.stats['total_texts_extracted'] += len(result.get('text_entries', []))
                    print(f"  成功: {len(result.get('text_entries', []))} 个文本entries目")
                else:
                    self.stats['failed_files'] += 1
                    print(f"  Failed")
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
                print(f"  Failed: {e}")
        
        return results
