#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解析器基类
所有数据解析器的抽象基类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# 导入Data Collection Module的工具（复用）
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_collection.utils import PathManager, setup_logger

# 导入过滤器模块
try:
    from .filters import InterferenceCharacterFilter, INTERFERENCE_FILTER_CONFIG
except ImportError:
    # 如果过滤器模块不exists，创建一个空的过滤器类
    class InterferenceCharacterFilter:
        def __init__(self, config=None):
            pass
        def clean_text(self, text):
            return text
        def get_statistics(self):
            return {'stats': {'texts_processed': 0}}
    INTERFERENCE_FILTER_CONFIG = {'enabled': False}


class BaseParser(ABC):
    """解析器基类"""
    
    def __init__(self, parser_type: str, enable_interference_filter: bool = True, 
                 filter_config: Optional[Dict[str, Any]] = None):
        """
        初始化解析器
        
        Args:
            parser_type: 解析器类型（json, csv, xml, html, reddit, twitter）
            enable_interference_filter: 是否启用干扰字符过滤器
            filter_config: 过滤器配置，如果为None则使用默认配置
        """
        self.parser_type = parser_type
        self.logger = setup_logger(f'{self.__class__.__name__}')
        self.path_manager = PathManager()
        
        # 设置输入Output directory
        self.input_dir = self.path_manager.get_origin_data_dir(parser_type)
        # 输出到 parsed_data/{parser_type}/ directory，与Origin data directory结构对应
        self.output_dir = self.path_manager.get_parsed_data_dir(parser_type)
        
        # 确保Output directoryexists（PathManagerhas been经创建了，但为了保险再确认一次）
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化干扰字符过滤器
        self.enable_interference_filter = enable_interference_filter
        self.interference_filter = None
        
        if enable_interference_filter:
            try:
                # 使用提供的配置或默认配置
                config = filter_config or INTERFERENCE_FILTER_CONFIG.copy()
                config['enabled'] = True  # 确保启用
                self.interference_filter = InterferenceCharacterFilter(config)
                self.logger.info("干扰字符过滤器has been启用")
            except Exception as e:
                self.logger.warning(f"无法初始化干扰字符过滤器: {e}")
                self.enable_interference_filter = False
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_texts_extracted': 0,
            'filtered_texts': 0,
            'interference_chars_removed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _process_extracted_text(self, text: str) -> str:
        """
        处理提取的文本（应用过滤器等）
        
        Args:
            text: 原始提取的文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return text
            
        processed_text = text
        
        # 应用干扰字符过滤器
        if self.enable_interference_filter and self.interference_filter:
            original_length = len(text)
            processed_text = self.interference_filter.clean_text(text)
            
            # 更新Statistics
            if len(processed_text) != original_length:
                self.stats['filtered_texts'] += 1
                chars_removed = original_length - len(processed_text)
                self.stats['interference_chars_removed'] += chars_removed
                
                self.logger.debug(f"过滤器移除了 {chars_removed} 个干扰字符")
        
        return processed_text
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        获取过滤器Statistics
        
        Returns:
            过滤器Statistics字典
        """
        if self.enable_interference_filter and self.interference_filter:
            return self.interference_filter.get_statistics()
        return {'stats': {'texts_processed': 0}}
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析单个File
        
        Args:
            file_path: File路径
        
        Returns:
            解析结果字典，包含 parsing_info 和 extracted_texts
        """
        pass
    
    def parse_directory(self, directory: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        解析整个directory
        
        Args:
            directory: directory路径，默认使用 self.input_dir
        
        Returns:
            解析结果列表
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        results = []
        files = self._get_files_to_parse(directory)
        
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\n找到 {len(files)} 个File待解析")
        
        self.stats['total_files'] = len(files)
        self.stats['start_time'] = datetime.now().isoformat()
        
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] 解析: {file_path.name}")
                result = self.parse_file(file_path)
                
                if result and result.get('parsing_info', {}).get('status') == 'success':
                    results.append(result)
                    self.stats['successful_files'] += 1
                    self.stats['total_texts_extracted'] += len(result.get('extracted_texts', []))
                else:
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
                print(f"  Failed: {e}")
        
        self.stats['end_time'] = datetime.now().isoformat()
        
        return results
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """
        获取需要解析的File列表
        子类可以重写此方法来指定File扩展名
        
        Args:
            directory: directory路径
        
        Returns:
            File路径列表
        """
        # 默认返回directory下所有File
        return [f for f in directory.iterdir() if f.is_file()]
    
    def save_parsed_data(self, data: Dict[str, Any], output_file: Path):
        """
        保存解析后的数据
        
        Args:
            data: 解析后的数据
            output_file: 输出File路径
        """
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved parsed data to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save parsed data to {output_file}: {e}")
            raise
    
    def save_batch_results(self, results: List[Dict[str, Any]], output_filename: str):
        """
        保存批量解析结果
        
        Args:
            results: 解析结果列表
            output_filename: 输出File名
        """
        if not results:
            self.logger.warning("No results to save")
            return
        
        output_file = self.output_dir / output_filename
        
        # 获取过滤器Statistics
        filter_stats = {}
        if self.enable_interference_filter and self.interference_filter:
            filter_stats = self.get_filter_statistics()
        
        batch_data = {
            'parsing_info': {
                'parser_type': self.parser_type,
                'total_files': len(results),
                'timestamp': datetime.now().isoformat(),
                'interference_filter_enabled': self.enable_interference_filter,
                'stats': self.stats,
                'filter_stats': filter_stats
            },
            'results': results
        }
        
        self.save_parsed_data(batch_data, output_file)
        print(f"\n批量解析结果has been保存: {output_file}")
    
    def create_parsing_result(self, 
                            source_file: Path, 
                            extracted_texts: List[str],
                            metadata: Optional[Dict[str, Any]] = None,
                            status: str = 'success',
                            error_message: str = None) -> Dict[str, Any]:
        """
        创建标准化的解析结果
        
        Args:
            source_file: 源File路径
            extracted_texts: 提取的文本列表
            metadata: 元数据
            status: 解析状态 (success, failed)
            error_message: Error信息
        
        Returns:
            标准化的解析结果字典
        """
        result = {
            'parsing_info': {
                'source_file': str(source_file),
                'parser_type': self.parser_type,
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'texts_count': len(extracted_texts)
            },
            'extracted_texts': extracted_texts
        }
        
        if metadata:
            result['metadata'] = metadata
        
        if error_message:
            result['parsing_info']['error'] = error_message
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Statistics"""
        return self.stats.copy()
    
    def log_summary(self):
        """记录解析摘要"""
        self.logger.info("="*60)
        self.logger.info(f"Parsing Summary - {self.parser_type.upper()}")
        self.logger.info("="*60)
        self.logger.info(f"Total files: {self.stats['total_files']}")
        self.logger.info(f"Successful: {self.stats['successful_files']}")
        self.logger.info(f"Failed: {self.stats['failed_files']}")
        self.logger.info(f"Texts extracted: {self.stats['total_texts_extracted']}")
        
        # 添加过滤器Statistics
        if self.enable_interference_filter:
            self.logger.info(f"Interference filter enabled: True")
            self.logger.info(f"Filtered texts: {self.stats.get('filtered_texts', 0)}")
            self.logger.info(f"Interference chars removed: {self.stats.get('interference_chars_removed', 0)}")
        
        self.logger.info(f"Start time: {self.stats['start_time']}")
        self.logger.info(f"End time: {self.stats['end_time']}")
        self.logger.info("="*60)
        
        # 同时打印到控制台
        print(f"\n{'='*70}")
        print(f"解析摘要 - {self.parser_type.upper()}")
        print(f"{'='*70}")
        print(f"总File数: {self.stats['total_files']}")
        print(f"成功: {self.stats['successful_files']}")
        print(f"Failed: {self.stats['failed_files']}")
        print(f"提取文本数: {self.stats['total_texts_extracted']}")
        
        # 添加过滤器信息到控制台输出
        if self.enable_interference_filter:
            print(f"干扰字符过滤: has been启用")
            print(f"过滤文本数: {self.stats.get('filtered_texts', 0)}")
            print(f"移除干扰字符数: {self.stats.get('interference_chars_removed', 0)}")
        else:
            print(f"干扰字符过滤: 未启用")
        
        print(f"{'='*70}\n")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(parser_type='{self.parser_type}', input_dir='{self.input_dir}')"

