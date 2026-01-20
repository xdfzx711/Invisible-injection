#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV Data Parser
Parse CSV format data file
"""

import csv
from pathlib import Path
from typing import Dict, Any, List
from io import StringIO

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import TextExtractor, FileUtils


class CSVParser(BaseParser):
    """CSV File Parser (Compatible with old format)"""
    
    def __init__(self):
        super().__init__('csv')
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single CSV file
        
        Args:
            file_path: CSV file path
        
        Returns:
            Parsing result dictionary (compatible with old format)
        """
        self.logger.info(f"Parsing CSV file: {file_path}")
        
        try:
            # Detect encoding
            encoding = FileUtils.detect_encoding(file_path)
            content = FileUtils.safe_read_file(file_path)
            
            # Detect CSV dialect
            dialect = csv.excel
            try:
                sample = content[:1024]
                if sample:
                    dialect = csv.Sniffer().sniff(sample)
            except:
                pass
            
            # Parse CSV
            text_entries = []
            headers = []
            row_count = 0
            
            csv_file = StringIO(content)
            reader = csv.reader(csv_file, dialect=dialect)
            
            # Read headers
            try:
                headers = next(reader)
                for col_index, header in enumerate(headers):
                    if header and header.strip():
                        text_entries.append({
                            'row': 0,
                            'column': col_index,
                            'column_name': header,
                            'value': header,
                            'field_type': 'header',
                            'is_header': True
                        })
            except StopIteration:
                headers = []
            
            # Read data rows
            for row_index, row in enumerate(reader, 1):
                row_count = row_index
                
                for col_index, cell_value in enumerate(row):
                    if cell_value and cell_value.strip():
                        column_name = headers[col_index] if col_index < len(headers) else f"column_{col_index}"
                        
                        text_entries.append({
                            'row': row_index,
                            'column': col_index,
                            'column_name': column_name,
                            'value': cell_value,
                            'field_type': TextExtractor.identify_field_type(column_name, cell_value),
                            'is_header': False,
                            'length': len(cell_value)
                        })
            
            # Build parsing result (same format as old format)
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'csv',
                    'total_text_entries': len(text_entries),
                    'total_rows': row_count + 1,
                    'total_columns': len(headers),
                    'encoding': encoding
                },
                'headers': headers,
                'text_entries': text_entries
            }
            
            self.logger.info(f"Successfully parsed {file_path.name}: {row_count+1} rows x {len(headers)} cols, {len(text_entries)} entries")
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_error_result(file_path, f"Parsing error: {e}")
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """Get all CSV files"""
        return list(directory.glob('*.csv'))
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            'file_info': FileUtils.get_file_info(file_path),
            'parsing_info': {
                'parser_type': 'csv',
                'status': 'failed',
                'error': error_message
            },
            'text_entries': []
        }
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """Parse entire directory (save each file separately)"""
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        print(f"\nFound {len(files)} CSV files to parse")
        
        self.stats['total_files'] = len(files)
        results = []
        
        for i, file_path in enumerate(files, 1):
            try:
                print(f"[{i}/{len(files)}] Parsing: {file_path.name}")
                result = self.parse_file(file_path)
                
                if result and result.get('parsing_info', {}).get('status') != 'failed':
                    output_filename = f"{file_path.stem}_parsed.json"
                    output_path = self.output_dir / output_filename
                    self.save_parsed_data(result, output_path)
                    
                    results.append(result)
                    self.stats['successful_files'] += 1
                    self.stats['total_texts_extracted'] += len(result.get('text_entries', []))
                    print(f"  Success: {len(result.get('text_entries', []))} text entries")
                else:
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
        
        return results
