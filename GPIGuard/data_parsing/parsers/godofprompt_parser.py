#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GodOfPrompt 数据解析器
解析从 GodOfPrompt.ai 收集的提示词数据
"""

import json
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import FileUtils, TextExtractor


class GodOfPromptParser(BaseParser):
    """GodOfPrompt 提示词数据解析器"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('godofprompt', enable_interference_filter, filter_config)
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """获取所有 JSON File"""
        return list(directory.glob('*.json'))
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析单个 GodOfPrompt JSON File
        
        Args:
            file_path: JSON File路径
            
        Returns:
            解析结果字典
        """
        self.logger.info(f"Parsing GodOfPrompt file: {file_path}")
        
        try:
            # 读取File内容
            content = FileUtils.safe_read_file(file_path)
            
            # 解析 JSON
            data = json.loads(content)
            
            # 提取文本entries目（简化格式：只保留 value, slug, category）
            text_entries = []
            
            if isinstance(data, list):
                # 如果是数组，遍历每个提示词对象
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        # 提取 prompt 字段作为主要内容
                        prompt_text = item.get('prompt', '')
                        slug = item.get('slug', f'prompt_{idx}')
                        category = item.get('category', '')
                        
                        # 只保留 value, slug, category
                        if prompt_text and prompt_text.strip():
                            # 应用干扰字符过滤器
                            filtered_text = self._process_extracted_text(prompt_text)
                            text_entries.append({
                                'value': filtered_text,
                                'slug': slug,
                                'category': category
                            })
            elif isinstance(data, dict):
                # 如果是单个对象，直接提取
                prompt_text = data.get('prompt', '')
                slug = data.get('slug', 'unknown')
                category = data.get('category', '')
                
                # 只保留 value, slug, category
                if prompt_text and prompt_text.strip():
                    # 应用干扰字符过滤器
                    filtered_text = self._process_extracted_text(prompt_text)
                    text_entries.append({
                        'value': filtered_text,
                        'slug': slug,
                        'category': category
                    })
            
            # 构建解析结果
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'godofprompt',
                    'total_text_entries': len(text_entries),
                    'total_prompts': len(text_entries),  # 每个entries目都是一个提示词
                    'encoding': FileUtils.detect_encoding(file_path),
                    'status': 'success'
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
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """创建Error结果"""
        return {
            'file_info': FileUtils.get_file_info(file_path),
            'parsing_info': {
                'parser_type': 'godofprompt',
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
        print(f"\n找到 {len(files)} 个GodOfPromptFile待解析")
        
        self.stats['total_files'] = len(files)
        
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

