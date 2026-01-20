#!/usr/bin/env python3
# -*- coding: utf-8 -*-



from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import tools from Data Collection Module (reuse)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_collection.utils import PathManager, setup_logger

# Import filter module
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
    """Base parser class"""
    
    def __init__(self, parser_type: str, enable_interference_filter: bool = True, 
                 filter_config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser
        
        Args:
            parser_type: Parser type (json, csv, xml, html, reddit, twitter)
            enable_interference_filter: Whether to enable interference character filter
            filter_config: Filter configuration, use default if None
        """
        self.parser_type = parser_type
        self.logger = setup_logger(f'{self.__class__.__name__}')
        self.path_manager = PathManager()
        
        # Set input/output directories
        self.input_dir = self.path_manager.get_origin_data_dir(parser_type)
        # Output to parsed_data/{parser_type}/ directory, corresponding to original data directory structure
        self.output_dir = self.path_manager.get_parsed_data_dir(parser_type)
        
        # 确保Output directoryexists（PathManagerhas been经创建了，但为了保险再确认一次）
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize interference character filter
        self.enable_interference_filter = enable_interference_filter
        self.interference_filter = None
        
        if enable_interference_filter:
            try:
                # Use provided configuration or default configuration
                config = filter_config or INTERFERENCE_FILTER_CONFIG.copy()
                config['enabled'] = True  # Ensure enabled
                self.interference_filter = InterferenceCharacterFilter(config)
                self.logger.info("Interference character filter enabled")
            except Exception as e:
                self.logger.warning(f"Unable to initialize interference character filter: {e}")
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
        Process extracted text (apply filters, etc.)
        
        Args:
            text: Original extracted text
            
        Returns:
            Processed text
        """
        if not text:
            return text
            
        processed_text = text
        
        # Apply interference character filter
        if self.enable_interference_filter and self.interference_filter:
            original_length = len(text)
            processed_text = self.interference_filter.clean_text(text)
            
            # Update statistics
            if len(processed_text) != original_length:
                self.stats['filtered_texts'] += 1
                chars_removed = original_length - len(processed_text)
                self.stats['interference_chars_removed'] += chars_removed
                
                self.logger.debug(f"Filter removed {chars_removed} interference characters")
        
        return processed_text
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        Get filter statistics
        
        Returns:
            Filter statistics dictionary
        """
        if self.enable_interference_filter and self.interference_filter:
            return self.interference_filter.get_statistics()
        return {'stats': {'texts_processed': 0}}
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single file
        
        Args:
            file_path: File path
        
        Returns:
            Parsing result dictionary containing parsing_info and extracted_texts
        """
        pass
    
    def parse_directory(self, directory: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Parse entire directory
        
        Args:
            directory: Directory path, use self.input_dir by default
        
        Returns:
            List of parsing results
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        results = []
        files = self._get_files_to_parse(directory)
        
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\nFound {len(files)} files to parse")
        
        self.stats['total_files'] = len(files)
        self.stats['start_time'] = datetime.now().isoformat()
        
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] Parsing: {file_path.name}")
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
        Get list of files to parse
        Subclasses can override this method to specify file extensions
        
        Args:
            directory: Directory path
        
        Returns:
            List of file paths
        """
        # Return all files in directory by default
        return [f for f in directory.iterdir() if f.is_file()]
    
    def save_parsed_data(self, data: Dict[str, Any], output_file: Path):
        """
        Save parsed data
        
        Args:
            data: Parsed data
            output_file: Output file path
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
        Save batch parsing results
        
        Args:
            results: List of parsing results
            output_filename: Output file name
        """
        if not results:
            self.logger.warning("No results to save")
            return
        
        output_file = self.output_dir / output_filename
        
        # Get filter statistics
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
        print(f"\nBatch parsing results saved: {output_file}")
    
    def create_parsing_result(self, 
                            source_file: Path, 
                            extracted_texts: List[str],
                            metadata: Optional[Dict[str, Any]] = None,
                            status: str = 'success',
                            error_message: str = None) -> Dict[str, Any]:
        """
        Create standardized parsing result
        
        Args:
            source_file: Source file path
            extracted_texts: List of extracted texts
            metadata: Metadata
            status: Parsing status (success, failed)
            error_message: Error message
        
        Returns:
            Standardized parsing result dictionary
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
        """Get statistics"""
        return self.stats.copy()
    
    def log_summary(self):
        self.logger.info("="*60)
        self.logger.info(f"Parsing Summary - {self.parser_type.upper()}")
        self.logger.info("="*60)
        self.logger.info(f"Total files: {self.stats['total_files']}")
        self.logger.info(f"Successful: {self.stats['successful_files']}")
        self.logger.info(f"Failed: {self.stats['failed_files']}")
        self.logger.info(f"Texts extracted: {self.stats['total_texts_extracted']}")
        
        # Add filter statistics
        if self.enable_interference_filter:
            self.logger.info(f"Interference filter enabled: True")
            self.logger.info(f"Filtered texts: {self.stats.get('filtered_texts', 0)}")
            self.logger.info(f"Interference chars removed: {self.stats.get('interference_chars_removed', 0)}")
        
        self.logger.info(f"Start time: {self.stats['start_time']}")
        self.logger.info(f"End time: {self.stats['end_time']}")
        self.logger.info("="*60)
        
        # Also print to console
        print(f"\n{'='*70}")
        print(f"Parsing Summary - {self.parser_type.upper()}")
        print(f"{'='*70}")
        print(f"Total files: {self.stats['total_files']}")
        print(f"Successful: {self.stats['successful_files']}")
        print(f"Failed: {self.stats['failed_files']}")
        print(f"Texts extracted: {self.stats['total_texts_extracted']}")
        
        # Add filter information to console output
        if self.enable_interference_filter:
            print(f"Interference character filter: Enabled")
            print(f"Filtered texts: {self.stats.get('filtered_texts', 0)}")
            print(f"Interference characters removed: {self.stats.get('interference_chars_removed', 0)}")
        else:
            print(f"Interference character filter: Disabled")
        
        print(f"{'='*70}\n")
    
    def __repr__(self):
        return f"{self.__class__.__name__}(parser_type='{self.parser_type}', input_dir='{self.input_dir}')"

