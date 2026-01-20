#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GodOfPrompt Data Parser
Parse prompt word data collected from GodOfPrompt.ai
"""

import json
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import FileUtils, TextExtractor


class GodOfPromptParser(BaseParser):
    """GodOfPrompt Prompt Word Data Parser"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('godofprompt', enable_interference_filter, filter_config)
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """Get all JSON files"""
        return list(directory.glob('*.json'))
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single GodOfPrompt JSON file
        
        Args:
            file_path: JSON file path
            
        Returns:
            Parsing result dictionary
        """
        self.logger.info(f"Parsing GodOfPrompt file: {file_path}")
        
        try:
            # Read file content
            content = FileUtils.safe_read_file(file_path)
            
            # Parse JSON
            data = json.loads(content)
            
            # Extract text entries (simplified format: keep only value, slug, category)
            text_entries = []
            
            if isinstance(data, list):
                # If it is an array, iterate through each prompt object
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        # Extract 'prompt' field as main content
                        prompt_text = item.get('prompt', '')
                        slug = item.get('slug', f'prompt_{idx}')
                        category = item.get('category', '')
                        
                        # Keep only value, slug, category
                        if prompt_text and prompt_text.strip():
                            # Apply interference character filter
                            filtered_text = self._process_extracted_text(prompt_text)
                            text_entries.append({
                                'value': filtered_text,
                                'slug': slug,
                                'category': category
                            })
            elif isinstance(data, dict):
                # If it is a single object, extract directly
                prompt_text = data.get('prompt', '')
                slug = data.get('slug', 'unknown')
                category = data.get('category', '')
                
                # Keep only value, slug, category
                if prompt_text and prompt_text.strip():
                    # Apply interference character filter
                    filtered_text = self._process_extracted_text(prompt_text)
                    text_entries.append({
                        'value': filtered_text,
                        'slug': slug,
                        'category': category
                    })
            
            # Build parsing result
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'godofprompt',
                    'total_text_entries': len(text_entries),
                    'total_prompts': len(text_entries),  # Each entry is a prompt
                    'encoding': FileUtils.detect_encoding(file_path),
                    'status': 'success'
                },
                'text_entries': text_entries
            }
            
            self.logger.info(f"Successfully parsed {file_path.name}: {len(text_entries)} text entries")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            return self._create_error_result(file_path, f"JSON format error: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_error_result(file_path, f"Parsing error: {e}")
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """Create error result"""
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
        Parse entire directory (rewrite to support saving each file separately)
        
        Args:
            directory: Directory path
            
        Returns:
            List of parsing results
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\nFound {len(files)} GodOfPrompt files to parse")
        
        self.stats['total_files'] = len(files)
        
        results = []
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] Parsing: {file_path.name}")
                result = self.parse_file(file_path)
                
                if result and result.get('parsing_info', {}).get('status') != 'failed':
                    # Save parsing results for each file separately
                    output_filename = f"{file_path.stem}_parsed.json"
                    output_path = self.output_dir / output_filename
                    self.save_parsed_data(result, output_path)
                    
                    results.append(result)
                    self.stats['successful_files'] += 1
                    self.stats['total_texts_extracted'] += len(result.get('text_entries', []))
                    print(f"  Success: {len(result.get('text_entries', []))} text entries")
                else:
                    self.stats['failed_files'] += 1
                    print(f"  Failed")
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
                print(f"  Failed: {e}")
        
        return results

