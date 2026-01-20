#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import TextExtractor, FileUtils


class XMLParser(BaseParser):
    """XML file parser (compatible with old format)"""
    
    def __init__(self):
        super().__init__('xml')
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single XML file
        
        Args:
            file_path: XML file path
        
        Returns:
            Parsing result dictionary (compatible with old format)
        """
        self.logger.info(f"Parsing XML file: {file_path}")
        
        try:
            # Read file content
            content = FileUtils.safe_read_file(file_path)
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Extract text entries
            text_entries = []
            self._extract_text_from_element(root, text_entries, root.tag)
            
            # Build parsing result (identical to old format)
            result = {
                'file_info': FileUtils.get_file_info(file_path),
                'parsing_info': {
                    'parser_type': 'xml',
                    'total_text_entries': len(text_entries),
                    'root_tag': root.tag,
                    'element_count': len(list(root.iter())),
                    'encoding': FileUtils.detect_encoding(file_path)
                },
                'text_entries': text_entries
            }
            
            self.logger.info(f"Successfully parsed {file_path.name}: {len(text_entries)} text entries")
            return result
            
        except ET.ParseError as e:
            self.logger.error(f"XML parse error in {file_path}: {e}")
            return self._create_error_result(file_path, f"XML format error: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return self._create_error_result(file_path, f"Parsing error: {e}")
    
    def _extract_text_from_element(self, element: ET.Element, entries: List[Dict], path: str):
        """Recursively extract text from XML elements (compatible with old format)"""
        # Extract element text
        if element.text and element.text.strip():
            entries.append({
                'xml_path': path,
                'element_tag': element.tag,
                'value': element.text.strip(),
                'field_type': 'element_text',
                'is_attribute': False,
                'length': len(element.text.strip())
            })
        
        # Extract attribute values
        for attr_name, attr_value in element.attrib.items():
            if attr_value and not TextExtractor.is_url(attr_value):
                entries.append({
                    'xml_path': f"{path}@{attr_name}",
                    'element_tag': element.tag,
                    'attribute_name': attr_name,
                    'value': attr_value,
                    'field_type': TextExtractor.identify_field_type(attr_name, attr_value),
                    'is_attribute': True,
                    'length': len(attr_value)
                })
        
        # Recursively process child elements
        for child in element:
            child_path = f"{path}/{child.tag}"
            self._extract_text_from_element(child, entries, child_path)
            
            # Extract tail text
            if child.tail and child.tail.strip():
                entries.append({
                    'xml_path': f"{child_path}#tail",
                    'element_tag': child.tag,
                    'value': child.tail.strip(),
                    'field_type': 'tail_text',
                    'is_attribute': False,
                    'length': len(child.tail.strip())
                })
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """Get all XML files"""
        return list(directory.glob('*.xml'))
    
    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            'file_info': FileUtils.get_file_info(file_path),
            'parsing_info': {
                'parser_type': 'xml',
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
        print(f"\nFound {len(files)} XML files to parse")
        
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
                    print(f"  Success: {len(result.get('text_entries', []))} text entries extracted")
                else:
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path.name}: {e}")
                self.stats['failed_files'] += 1
        
        return results
