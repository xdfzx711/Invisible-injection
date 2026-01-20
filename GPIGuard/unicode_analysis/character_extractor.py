#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_collection.utils.logger import setup_logger

class CharacterExtractor:
    """Character Extractor - Extract characters from parsed results one by one"""
    
    def __init__(self, output_dir: Union[str, Path] = "testscan", data_sources: List[str] = None):
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('CharacterExtractor', 'character_extraction.log')

        # Set data sources to process
        self.data_sources = data_sources or ['json', 'csv', 'xml', 'html', 'reddit', 'twitter', 'github', 'godofprompt']
        self.logger.info(f"Character Extractor enabled data sources: {', '.join(self.data_sources)}")

        # Create Output directory
        self.char_output_dir = self.output_dir / "unicode_analysis" / "character_extraction"
        self.char_output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_from_parsed_data(self, parsed_data_dir: Union[str, Path]) -> List[Dict[str, Any]]:
        """Extract all characters from Parsed data directory"""
        parsed_data_dir = Path(parsed_data_dir)
        self.logger.info(f"Starting character extraction from parsed data: {parsed_data_dir}")

        all_characters = []
        source_characters = {}  # Characters grouped by data source
        char_id_counter = 0


        source_handlers = {
            'json': ('json_analysis', self._extract_from_json_results),
            'csv': ('csv_analysis', self._extract_from_csv_results),
            'xml': ('xml_analysis', self._extract_from_xml_results),
            'html': ('html_analysis', self._extract_from_html_results),
            'reddit': ('reddit_analysis', self._extract_from_reddit_results),
            'twitter': ('twitter_analysis', self._extract_from_twitter_results),
            'github': ('github_analysis', self._extract_from_github_results),
            'godofprompt': ('godofprompt_analysis', self._extract_from_godofprompt_results)
        }

        for source_type in self.data_sources:
            handler = None
            dir_name = None
            
            if source_type in source_handlers:
                dir_name, handler = source_handlers[source_type]
            else:
                # Attempt to handle dynamic data sources
                dir_name = f"{source_type}_analysis"
                
                # Infer handler based on name
                if 'reddit' in source_type:
                    handler = self._extract_from_reddit_results
                elif 'twitter' in source_type:
                    handler = self._extract_from_twitter_results
                elif 'github' in source_type:
                    handler = self._extract_from_github_results
                elif 'godofprompt' in source_type:
                    handler = self._extract_from_godofprompt_results
                elif 'html' in source_type:
                    handler = self._extract_from_html_results
                elif 'xml' in source_type:
                    handler = self._extract_from_xml_results
                elif 'csv' in source_type:
                    handler = self._extract_from_csv_results
                elif 'json' in source_type:
                    handler = self._extract_from_json_results
            
            if dir_name and handler:
                source_dir = parsed_data_dir / dir_name

                if source_dir.exists():
                    self.logger.info(f"Processing {source_type.upper()} data source...")
                    source_chars = []
                    char_id_counter = handler(source_dir, source_chars, char_id_counter)

                    # Correct the source_type of extracted characters to ensure consistency with the current source_type
                    # This is especially important for dynamic data sources (e.g., reddit_top)
                    for char in source_chars:
                        if "source_info" in char:
                            char["source_info"]["source_type"] = source_type
                        
                        # Update char_id prefix to match source_type
                        if "char_id" in char:
                            parts = char["char_id"].rsplit('_', 1)
                            if len(parts) == 2 and parts[1].isdigit():
                                char["char_id"] = f"{source_type}_{parts[1]}"

                    if source_chars:
                        source_characters[source_type] = source_chars
                        all_characters.extend(source_chars)
                        self.logger.info(f"{source_type.upper()} data source extracted {len(source_chars)} characters")
                else:
                    self.logger.info(f"{source_type.upper()} data source directory does not exist: {source_dir}")
            else:
                self.logger.warning(f"Unrecognized data source type or no handler found: {source_type}")

        self.logger.info(f"Character extraction completed, total characters extracted: {len(all_characters)}")

        # Save extraction results separately by data source
        self._save_extracted_characters_by_source(source_characters, all_characters)

        return all_characters

    def extract_from_parsed_data_smart(self, parsed_data_dir: Union[str, Path], force_extract: bool = False) -> List[Dict[str, Any]]:
        """Smart character extraction - skip extraction if results already exist"""

        if force_extract:
            self.logger.info("Force re-extracting characters")
            return self.extract_from_parsed_data(parsed_data_dir)

        # Check existing extraction files
        existing_sources, missing_sources = self._check_existing_extractions()

        if not missing_sources:
            # All data sources have been extracted, load existing data directly
            self.logger.info("Characters for all data sources have been extracted, skipping extraction step")
            loaded_characters = self._load_existing_extractions(existing_sources)

            if not loaded_characters:
                self.logger.warning(f"Although extraction files were detected, the number of loaded characters is 0. Data sources: {existing_sources}")
                self.logger.warning("This may be due to file corruption, format errors, or indeed no characters to extract")

            return loaded_characters

        if existing_sources:
            # Some data sources have been extracted, only extract the missing ones
            self.logger.info(f"Found already extracted data sources: {existing_sources}")
            self.logger.info(f"Data sources to extract: {missing_sources}")

            # Temporarily modify the data source list to only process the missing ones
            original_sources = self.data_sources
            self.data_sources = missing_sources

            try:
                # Extract missing data sources
                new_characters = self.extract_from_parsed_data(parsed_data_dir)

                # Load existing data and merge
                existing_characters = self._load_existing_extractions(existing_sources)

                # Merge all characters
                all_characters = existing_characters + new_characters
                self.logger.info(f"Merge completed, total characters: {len(all_characters)}")

                if not all_characters:
                    self.logger.warning(f"Number of characters after merge is 0. Existing characters: {len(existing_characters)}, New extracted characters: {len(new_characters)}")

                return all_characters
            finally:
                # Restore original data source list
                self.data_sources = original_sources
        else:
            # No existing extractions, extract normally
            self.logger.info("Starting extraction of characters from all data sources")
            extracted_characters = self.extract_from_parsed_data(parsed_data_dir)

            if not extracted_characters:
                self.logger.warning(f"Number of characters extracted from parsed data is 0. Data sources: {self.data_sources}")
                self.logger.warning(f"Parsed data directory: {parsed_data_dir}")

            return extracted_characters

    def _check_existing_extractions(self) -> tuple[List[str], List[str]]:
        """Check existing character extraction files (simplified check)"""
        existing_sources = []
        missing_sources = []

        for source in self.data_sources:
            extraction_file = self.char_output_dir / f"character_extraction_{source}.json"

            # Simplified check: only check existence and size > 0
            if extraction_file.exists() and extraction_file.stat().st_size > 0:
                existing_sources.append(source)
                self.logger.debug(f"Found valid extraction file: {extraction_file.name}")
            else:
                missing_sources.append(source)
                self.logger.debug(f"Missing or invalid extraction file: {extraction_file.name}")

        return existing_sources, missing_sources

    def _load_existing_extractions(self, source_list: List[str]) -> List[Dict[str, Any]]:
        """Load existing character extraction data"""
        all_characters = []

        for source in source_list:
            extraction_file = self.char_output_dir / f"character_extraction_{source}.json"

            try:
                if not extraction_file.exists():
                    self.logger.error(f"Loading {source} extraction file failed: File does not exist - {extraction_file}")
                    continue

                file_size = extraction_file.stat().st_size
                if file_size == 0:
                    self.logger.error(f"Loading {source} extraction file failed: File is empty - {extraction_file}")
                    continue

                # Check file size, warn if over 1GB and provide suggestions
                file_size_gb = file_size / (1024 * 1024 * 1024)
                if file_size_gb > 1.0:
                    self.logger.warning(f"Detected large file: {source} extraction file size is {file_size_gb:.2f}GB")
                    self.logger.warning(f"Loading large files may cause memory issues, consider using --force-extract to regenerate smaller files")

                    # If file is over 8GB, skip loading
                    if file_size_gb > 8.0:
                        self.logger.error(f"File too large ({file_size_gb:.2f}GB), skipping loading to avoid memory issues")
                        self.logger.error(f"Please use --force-extract to regenerate extraction files")
                        continue

                self.logger.info(f"Loading {source} extraction file ({file_size_gb:.2f}GB)...")

                # For large files, try chunked loading
                if file_size_gb > 2.0:
                    self.logger.info(f"File is large ({file_size_gb:.2f}GB), attempting chunked loading...")
                    characters = self._load_large_file_chunked(extraction_file, source)
                    if characters:
                        all_characters.extend(characters)
                        self.logger.info(f"Chunked loading {source.upper()} characters: {len(characters)}")
                        continue
                    else:
                        self.logger.warning(f"Chunked loading failed, attempting regular loading...")

                with open(extraction_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    self.logger.error(f"Loading {source} extraction file failed: File format error, not a valid JSON object - {extraction_file}")
                    continue

                # Check file format
                extraction_info = data.get('extraction_info', {})
                file_format = extraction_info.get('format', 'standard')

                if file_format == 'compressed':
                    # Handle compressed format
                    characters = self._load_compressed_characters(data, source)
                else:
                    # Handle standard format
                    characters = data.get('characters', [])
                    if not isinstance(characters, list):
                        self.logger.error(f"Loading {source} extraction file failed: 'characters' field is not a list - {extraction_file}")
                        continue

                all_characters.extend(characters)
                self.logger.info(f"Loaded {source.upper()} characters: {len(characters)} (format: {file_format})")

            except MemoryError as e:
                file_size_gb = extraction_file.stat().st_size / (1024 * 1024 * 1024)
                self.logger.error(f"Loading {source} extraction file failed: MemoryError - File size {file_size_gb:.2f}GB")
                self.logger.error(f"Solutions: 1) Increase system memory 2) Use --force-extract to regenerate files 3) Process data in chunks")
            except json.JSONDecodeError as e:
                self.logger.error(f"Loading {source} extraction file failed: JSON decode error - {extraction_file}, Error: {e}")
            except PermissionError as e:
                self.logger.error(f"Loading {source} extraction file failed: Permission error - {extraction_file}, Error: {e}")
            except FileNotFoundError as e:
                self.logger.error(f"Loading {source} extraction file failed: File not found - {extraction_file}, Error: {e}")
            except Exception as e:
                self.logger.error(f"Loading {source} extraction file failed: Unknown error - {extraction_file}, Error type: {type(e).__name__}, Error: {e}")

        # Record loading summary information
        self.logger.info(f"Character loading completed, total {len(all_characters)} characters loaded, sources: {source_list}")

        if not all_characters and source_list:
            self.logger.warning(f"Although attempted to load from {len(source_list)} data sources, no characters were successfully loaded")

        return all_characters

    def _load_large_file_chunked(self, extraction_file: Path, source: str) -> List[Dict[str, Any]]:
        """Load large files in chunks to avoid memory issues"""
        self.logger.info(f"Attempting chunked loading of large file: {extraction_file}")
        try:
            # Attempt to use ijson for streaming parsing
            import ijson

            characters = []
            with open(extraction_file, 'rb') as f:
                # Parse each object in the characters array
                parser = ijson.items(f, 'characters.item')

                chunk_size = 10000  # Process 10000 characters at a time
                chunk = []

                for char_obj in parser:
                    chunk.append(char_obj)

                    if len(chunk) >= chunk_size:
                        characters.extend(chunk)
                        self.logger.info(f"Loaded {len(characters)} characters so far...")
                        chunk = []

                # Process the last batch
                if chunk:
                    characters.extend(chunk)

                self.logger.info(f"Chunked loading completed, total {len(characters)} characters loaded")
                return characters

        except ImportError:
            self.logger.error("Chunked loading requires the ijson library, please install: pip install ijson")
            return []
        except Exception as e:
            self.logger.error(f"Chunked loading failed: {e}")
            return []

    def _extract_from_json_results(self, json_dir: Path, all_characters: List, char_id_counter: int) -> int:
        self.logger.info(f"Processing JSON results: {json_dir}")
        
        for json_file in json_dir.glob("*_parsed.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'json', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"Processing JSON file failed {json_file}: {e}")
        
        return char_id_counter

    def _extract_from_github_results(self, github_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from GitHub parsing results"""
        self.logger.info(f"Processing GitHub results: {github_dir}")

        for gh_file in github_dir.glob("*_parsed.json"):
            try:
                with open(gh_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result.get('file_info', {})
                text_entries = parsed_result.get('text_entries', [])

                owner = file_info.get('owner', '')
                repo = file_info.get('repo', '')
                repository_url = file_info.get('repository_url', '')

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if not string_value:
                        continue
                    # General text entry for GitHub
                    source_info = {
                        "source_type": "github",
                        "content_type": entry.get('field_type', 'github_content'),
                        "owner": owner,
                        "repo": repo,
                        "repository_url": repository_url,
                        "file_name": gh_file.name,
                        "file_path": str(gh_file.relative_to(self.output_dir.parent))
                    }
                    char_id_counter = self._extract_characters_from_text(
                        text=string_value,
                        source_info=source_info,
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            except Exception as e:
                self.logger.error(f"Processing GitHub file failed {gh_file}: {e}")

        return char_id_counter
    
    def _extract_from_godofprompt_results(self, godofprompt_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from GodOfPrompt parsing results"""
        self.logger.info(f"Processing GodOfPrompt results: {godofprompt_dir}")

        for gp_file in godofprompt_dir.glob("*_parsed.json"):
            try:
                with open(gp_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result.get('file_info', {})
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if not string_value:
                        continue
                    
                    # Get slug and category as context information
                    slug = entry.get('slug', '')
                    category = entry.get('category', '')
                    
                    # Text entry for GodOfPrompt
                    source_info = {
                        "source_type": "godofprompt",
                        "content_type": "prompt",
                        "slug": slug,
                        "category": category,
                        "file_name": gp_file.name,
                        "file_path": str(gp_file.relative_to(self.output_dir.parent))
                    }
                    char_id_counter = self._extract_characters_from_text(
                        text=string_value,
                        source_info=source_info,
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            except Exception as e:
                self.logger.error(f"Processing GodOfPrompt file failed {gp_file}: {e}")

        return char_id_counter
    
    def _extract_from_csv_results(self, csv_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from CSV parsing results"""
        self.logger.info(f"Processing CSV results: {csv_dir}")
        
        for csv_file in csv_dir.glob("*_parsed.json"):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'csv', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"Processing CSV file failed {csv_file}: {e}")
        
        return char_id_counter
    
    def _extract_from_xml_results(self, xml_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from XML parsing results"""
        self.logger.info(f"Processing XML results: {xml_dir}")
        
        for xml_file in xml_dir.glob("*_parsed.json"):
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'xml', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"Processing XML file failed {xml_file}: {e}")
        
        return char_id_counter

    def _extract_from_html_results(self, html_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from HTML parsing results"""
        self.logger.info(f"Processing HTML results: {html_dir}")

        for html_file in html_dir.glob("*_extracted.json"):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                # Check for parsing errors
                page_info = parsed_result.get('page_info', {})
                if 'error' in page_info:
                    continue

                # Get file information
                file_info = {
                    'file_name': html_file.name,
                    'relative_path': str(html_file.relative_to(html_dir.parent.parent)),
                    'url': page_info.get('url', ''),
                    'website_name': page_info.get('website_name', ''),
                    'page_type': page_info.get('page_type', '')
                }

                # Extract text entries
                extracted_content = parsed_result.get('extracted_content', {})
                text_entries = extracted_content.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'html', all_characters, char_id_counter
                        )

                # Also extract characters from meta information
                meta_info = extracted_content.get('meta_info', {})
                for meta_key, meta_value in meta_info.items():
                    if isinstance(meta_value, str) and meta_value:
                        # Create meta entries
                        meta_entry = {
                            'element_type': 'meta',
                            'tag_name': 'meta',
                            'meta_key': meta_key,
                            'field_type': 'meta'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            meta_value, meta_entry, file_info, 'html', all_characters, char_id_counter
                        )

                # Extract characters from link texts
                links = extracted_content.get('links', [])
                for link in links:
                    link_text = link.get('text', '')
                    if link_text:
                        link_entry = {
                            'element_type': 'link_text',
                            'tag_name': 'a',
                            'url': link.get('url', ''),
                            'field_type': 'link'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            link_text, link_entry, file_info, 'html', all_characters, char_id_counter
                        )

                # Extract characters from image alt texts
                images = extracted_content.get('images', [])
                for image in images:
                    alt_text = image.get('alt', '')
                    if alt_text:
                        img_entry = {
                            'element_type': 'image_alt',
                            'tag_name': 'img',
                            'src': image.get('src', ''),
                            'field_type': 'alt_text'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            alt_text, img_entry, file_info, 'html', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理HTMLFileFailed {html_file}: {e}")

        return char_id_counter

    def _detect_normalization_changes(self, original: str, nfc: str, nfkc: str) -> List[Dict[str, Any]]:
        """Detect Unicode normalization changes"""
        changes = []

        # NFC change detection
        if original != nfc:
            changes.append({
                "type": "nfc_change",
                "original": original,
                "normalized": nfc,
                "risk_level": "medium",
                "description": "String changed after NFC normalization",
                "character_count_change": len(nfc) - len(original)
            })

        # NFKC change detection
        if original != nfkc:
            risk_level = "high" if nfc != nfkc else "medium"
            changes.append({
                "type": "nfkc_change",
                "original": original,
                "normalized": nfkc,
                "risk_level": risk_level,
                "description": "String changed after NFKC normalization",
                "character_count_change": len(nfkc) - len(original)
            })

        # Significant length change detection (potential security risk)
        if len(original) != len(nfkc) and abs(len(original) - len(nfkc)) > 1:
            changes.append({
                "type": "significant_length_change",
                "original_length": len(original),
                "normalized_length": len(nfkc),
                "length_difference": len(nfkc) - len(original),
                "risk_level": "high",
                "description": "Normalization caused significant change in string length"
            })

        return changes

    def _assess_normalization_risk(self, changes: List[Dict[str, Any]]) -> str:
        """Assess the risk level of normalization changes"""
        if not changes:
            return "none"

        risk_levels = [change["risk_level"] for change in changes]

        if "high" in risk_levels:
            return "high"
        elif "medium" in risk_levels:
            return "medium"
        else:
            return "low"

    def _find_original_position(self, char: str, normalized_pos: int, original: str, normalized: str) -> int:
        """Attempt to find the position of a character in the original string"""
        # Simple heuristic: if the strings are the same length, positions should correspond
        if len(original) == len(normalized):
            return normalized_pos

        # If lengths differ, try to find approximate position through character matching
        # This is a simplified implementation; more complex cases may require a more precise algorithm
        if normalized_pos < len(original):
            return normalized_pos
        else:
            return len(original) - 1

    def _extract_characters_from_string(self, string_value: str, entry: Dict, file_info: Dict,
                                      source_type: str, all_characters: List, char_id_counter: int) -> int:
        """Extract all characters from a single string"""

        # 1. Perform Unicode normalization
        original_string = string_value
        nfc_normalized = unicodedata.normalize('NFC', string_value)
        nfkc_normalized = unicodedata.normalize('NFKC', string_value)

        # 2. Detect normalization changes
        normalization_changes = self._detect_normalization_changes(
            original_string, nfc_normalized, nfkc_normalized
        )

        # 3. Assess risk level
        normalization_risk = self._assess_normalization_risk(normalization_changes)

        # 4. Use NFKC normalized string for character extraction (stricter normalization)
        final_string = nfkc_normalized

        # 5. Record string-level normalization information
        string_normalization_info = {
            "original_string": original_string,
            "nfc_normalized": nfc_normalized,
            "nfkc_normalized": nfkc_normalized,
            "final_string_used": final_string,
            "has_normalization_changes": len(normalization_changes) > 0,
            "normalization_changes": normalization_changes,
            "normalization_risk_level": normalization_risk,
            "original_length": len(original_string),
            "final_length": len(final_string)
        }

        for position, char in enumerate(final_string):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "position_in_original": self._find_original_position(char, position, original_string, final_string),
                "source_info": {
                    "string_value": final_string,  
                    "string_length": len(final_string),
                    "file_path": file_info.get('relative_path', ''),
                    "file_name": file_info.get('file_name', ''),
                    "source_type": source_type,
                    "field_type": entry.get('field_type', 'unknown')
                },
                "normalization_info": string_normalization_info
            }
            
            # Add source-type-specific location information
            if source_type == 'json':
                char_info["source_info"]["json_path"] = entry.get('json_path', '')
            elif source_type == 'csv':
                char_info["source_info"]["csv_row"] = entry.get('row', 0)
                char_info["source_info"]["csv_column"] = entry.get('column_name', '')
            elif source_type == 'xml':
                char_info["source_info"]["xml_path"] = entry.get('xml_path', '')
                char_info["source_info"]["element_type"] = entry.get('element_type', '')
            elif source_type == 'html':
                char_info["source_info"]["html_element_type"] = entry.get('element_type', '')
                char_info["source_info"]["html_tag_name"] = entry.get('tag_name', '')
                char_info["source_info"]["xpath"] = entry.get('xpath', '')
                char_info["source_info"]["attributes"] = entry.get('attributes', {})
                char_info["source_info"]["url"] = file_info.get('url', '')
                char_info["source_info"]["website_name"] = file_info.get('website_name', '')
                char_info["source_info"]["page_type"] = file_info.get('page_type', '')

                # Add additional information for specific element types
                if entry.get('element_type') == 'link_text':
                    char_info["source_info"]["link_url"] = entry.get('url', '')
                elif entry.get('element_type') == 'image_alt':
                    char_info["source_info"]["image_src"] = entry.get('src', '')
                elif entry.get('element_type') == 'meta':
                    char_info["source_info"]["meta_key"] = entry.get('meta_key', '')
            elif source_type == 'twitter':
                # Add Twitter-specific context information
                context = entry.get('context', {})
                char_info["source_info"]["content_type"] = entry.get('field_type', 'unknown')
                char_info["source_info"]["tweet_id"] = context.get('tweet_id', '')
                char_info["source_info"]["author"] = context.get('author', '')
                char_info["source_info"]["created_at"] = context.get('created_at', '')
                char_info["source_info"]["lang"] = context.get('lang', '')
                char_info["source_info"]["query"] = context.get('query', '')

                # Add context preview (text before and after the character)
                context_length = 20
                start_pos = max(0, position - context_length)
                end_pos = min(len(string_value), position + context_length + 1)
                char_info["source_info"]["context_before"] = string_value[start_pos:position]
                char_info["source_info"]["context_after"] = string_value[position + 1:end_pos]
            elif source_type == 'reddit':
                # Add Reddit-specific context information
                context = entry.get('context', {})
                char_info["source_info"]["content_type"] = entry.get('field_type', 'unknown')
                char_info["source_info"]["subreddit"] = context.get('subreddit', '')
                char_info["source_info"]["post_id"] = context.get('post_id', '')
                char_info["source_info"]["comment_id"] = context.get('comment_id', '')
                char_info["source_info"]["submission_id"] = context.get('submission_id', '')

                # Add context preview
                context_length = 20
                start_pos = max(0, position - context_length)
                end_pos = min(len(string_value), position + context_length + 1)
                char_info["source_info"]["context_before"] = string_value[start_pos:position]
                char_info["source_info"]["context_after"] = string_value[position + 1:end_pos]

            all_characters.append(char_info)
            char_id_counter += 1
        
        return char_id_counter

    def _save_extracted_characters_by_source(self, source_characters: Dict[str, List[Dict[str, Any]]], all_characters: List[Dict[str, Any]]):
        """Save extracted characters separately by data source"""

        # Save separate files for each data source
        for source_type, characters in source_characters.items():
            output_file = self.char_output_dir / f"character_extraction_{source_type}.json"

            # Create source-specific results
            source_result = {
                "extraction_info": {
                    "source_type": source_type,
                    "total_characters": len(characters),
                    "unique_characters": len(set(char["character"] for char in characters)),
                    "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "characters": characters
            }

            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(source_result, f, ensure_ascii=False, indent=2)
                self.logger.info(f"{source_type.upper()} character extraction results have been saved: {output_file} ({len(characters)} characters)")
            except Exception as e:
                self.logger.error(f"Failed to save {source_type} character extraction results: {e}")

    # Removed summary generation method for simplicity

    def get_character_summary(self, all_characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get character extraction summary information"""
        if not all_characters:
            return {"total_characters": 0, "unique_characters": 0}
        
        return {
            "total_characters": len(all_characters),
            "unique_characters": len(set(char["character"] for char in all_characters)),
            "source_types": list(set(char["source_info"]["source_type"] for char in all_characters)),
            "sample_characters": all_characters[:10]  # First 10 characters as sample
        }

    def _extract_from_json_results(self, json_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from JSON parsing results"""
        self.logger.info(f"Processing JSON parsing results: {json_dir}")

        for json_file in json_dir.glob("*_parsed.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'json', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"Failed to process JSON file {json_file}: {e}")

        return char_id_counter

    def _extract_from_csv_results(self, csv_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from CSV parsing results"""
        self.logger.info(f"Processing CSV parsing results: {csv_dir}")

        for csv_file in csv_dir.glob("*_parsed.json"):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'csv', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"Failed to process CSV file {csv_file}: {e}")

        return char_id_counter

    def _extract_from_xml_results(self, xml_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from XML parsing results"""
        self.logger.info(f"Processing XML parsing results: {xml_dir}")

        for xml_file in xml_dir.glob("*_parsed.json"):
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'xml', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"Failed to process XML file {xml_file}: {e}")

        return char_id_counter



    def _extract_from_reddit_results(self, reddit_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from Reddit parsing results"""
        self.logger.info(f"Processing Reddit parsing results: {reddit_dir}")

        # Process posts files
        for posts_file in reddit_dir.glob("*_posts_parsed.json"):
            char_id_counter = self._extract_from_reddit_posts(posts_file, all_characters, char_id_counter)

        # 处理评论File
        for comments_file in reddit_dir.glob("*_comments_parsed.json"):
            char_id_counter = self._extract_from_reddit_comments(comments_file, all_characters, char_id_counter)

        return char_id_counter

    def _extract_from_twitter_results(self, twitter_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from Twitter parsing results"""
        self.logger.info(f"Processing Twitter parsing results: {twitter_dir}")

        for twitter_file in twitter_dir.glob("*.json"):
            try:
                with open(twitter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'error' in data.get('parsing_info', {}):
                    continue

                # Twitter data format: {"parsing_info": {...}, "tweets": [...]}
                tweets = data.get('tweets', [])
                if not tweets:
                    continue

                parsing_info = data.get('parsing_info', {})
                query = parsing_info.get('query', 'unknown')

                for tweet in tweets:
                    text_content = tweet.get('text_content', '')
                    if text_content:
                        char_id_counter = self._extract_characters_from_text(
                            text=text_content,
                            source_info={
                                "source_type": "twitter",
                                "content_type": "tweet",
                                "query": query,
                                "tweet_id": tweet.get('id', ''),
                                "author": tweet.get('author_username', ''),
                                "file_name": twitter_file.name,
                                "file_path": str(twitter_file.relative_to(self.output_dir.parent))
                            },
                            all_characters=all_characters,
                            char_id_counter=char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"Failed to process Twitter file {twitter_file}: {e}")

        return char_id_counter

    def _extract_from_reddit_posts(self, posts_file: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from Reddit posts"""
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data or 'posts' not in data:
                return char_id_counter

            subreddit = data.get('parsing_info', {}).get('subreddit', 'unknown')

            for post in data['posts']:
                # Extract title characters
                if post.get('title'):
                    char_id_counter = self._extract_characters_from_text(
                        text=post['title'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "post_title",
                            "subreddit": subreddit,
                            "post_id": post.get('id', ''),
                            "file_name": posts_file.name,
                            "file_path": str(posts_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

                # Extract post content characters
                if post.get('selftext'):
                    char_id_counter = self._extract_characters_from_text(
                        text=post['selftext'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "post_content",
                            "subreddit": subreddit,
                            "post_id": post.get('id', ''),
                            "file_name": posts_file.name,
                            "file_path": str(posts_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            return char_id_counter

        except Exception as e:
            self.logger.error(f"Failed to process Reddit posts file {posts_file}: {e}")
            return char_id_counter

    def _extract_from_reddit_comments(self, comments_file: Path, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from Reddit comments"""
        try:
            with open(comments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data or 'comments' not in data:
                return char_id_counter

            subreddit = data.get('parsing_info', {}).get('subreddit', 'unknown')

            for comment in data['comments']:
                if comment.get('body'):
                    char_id_counter = self._extract_characters_from_text(
                        text=comment['body'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "comment",
                            "subreddit": subreddit,
                            "comment_id": comment.get('id', ''),
                            "submission_id": comment.get('submission_id', ''),
                            "file_name": comments_file.name,
                            "file_path": str(comments_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            return char_id_counter

        except Exception as e:
            self.logger.error(f"Failed to process Reddit comments file {comments_file}: {e}")
            return char_id_counter

    def _extract_characters_from_text(self, text: str, source_info: Dict, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from text (general method supporting multiple data sources)"""
        source_type = source_info.get("source_type", "unknown")
        content_type = source_info.get("content_type", f"{source_type}_content")
        
        for position, char in enumerate(text):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "source_info": {
                    **source_info,
                    "string_value": text,
                    "string_length": len(text),
                    "field_type": content_type
                }
            }

            all_characters.append(char_info)
            char_id_counter += 1

        return char_id_counter

    def _extract_characters_from_string(self, string_value: str, entry: Dict, file_info: Dict, source_type: str, all_characters: List, char_id_counter: int) -> int:
        """Extract characters from string (general method)"""
        for position, char in enumerate(string_value):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "source_info": {
                    "source_type": source_type,
                    "field_type": entry.get('field_type', 'text'),
                    "string_value": string_value,
                    "string_length": len(string_value),
                    "file_name": file_info.get('file_name', ''),
                    "file_path": file_info.get('file_path', ''),
                    "context": entry.get('context', {})
                }
            }

            all_characters.append(char_info)
            char_id_counter += 1

        return char_id_counter
