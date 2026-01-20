#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_collection.utils.logger import setup_logger

class ConfusablesParser:
    def __init__(self, output_dir: Union[str, Path] = None):
        if output_dir is None:
            current_file = Path(__file__).resolve()
            testscan_root = current_file.parent.parent  
            output_dir = testscan_root / "testscan_data" / "unicode_analysis"

        self.output_dir = Path(output_dir)
        self.logger = setup_logger('ConfusablesParser', 'confusables_parser.log')

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Confusables Output directory: {self.output_dir.absolute()}")
    
    def parse_confusables_file(self, confusables_file: Union[str, Path]) -> Dict[str, Any]:
        """Parse confusables.txt file"""
        confusables_file = Path(confusables_file)

        if not confusables_file.exists():
            self.logger.error(f"Confusables file does not exist: {confusables_file}")
            return {}

        self.logger.info(f"Starting to parse confusables file: {confusables_file}")

        # Simplified data structure without danger levels
        confusables_data = {
            "metadata": {
                "source_file": str(confusables_file.absolute()),
                "parsed_time": "",
                "total_entries": 0
            },
            "confusables_map": {}  # Main confusable character mapping
        }

        parse_stats = {
            "total_lines": 0,
            "comment_lines": 0,
            "empty_lines": 0,
            "parsed_entries": 0,
            "error_lines": 0,
            "confusable_types": {}
        }
        
        try:
            with open(confusables_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parse_stats["total_lines"] += 1
                    
                    if not line.strip():
                        parse_stats["empty_lines"] += 1
                        continue
                    
                    if line.strip().startswith('#'):
                        parse_stats["comment_lines"] += 1
                        continue
                    
                    # Parse data line
                    try:
                        entry = self._parse_confusable_line(line, line_num)
                        if entry:
                            unicode_point = entry["unicode_point"]
                            confusables_data["confusables_map"][unicode_point] = entry
                            parse_stats["parsed_entries"] += 1

                            # Count types
                            conf_type = entry.get("confusable_type", "unknown")
                            parse_stats["confusable_types"][conf_type] = parse_stats["confusable_types"].get(conf_type, 0) + 1
                    
                    except Exception as e:
                        self.logger.warning(f"Failed to parse line {line_num}: {e}")
                        parse_stats["error_lines"] += 1
        
        except Exception as e:
            self.logger.error(f"Failed to read confusables file: {e}")
            return {}

        # Update metadata
        import datetime
        confusables_data["metadata"]["parsed_time"] = datetime.datetime.now().isoformat()
        confusables_data["metadata"]["total_entries"] = parse_stats["parsed_entries"]

        self.logger.info(f"Confusables parsing completed: {parse_stats['parsed_entries']} entries")
        self._log_parse_stats(parse_stats)

        return confusables_data

    def save_confusables_data(self, confusables_data: Dict[str, Any], filename: str = "unicode_confusables.json") -> Path:
        """Save parsed confusables data to the specified directory"""
        output_file = self.output_dir / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(confusables_data, f, ensure_ascii=False, indent=2)

            total_entries = confusables_data.get("metadata", {}).get("total_entries", 0)
            self.logger.info(f"Confusables data has been saved: {output_file.absolute()}")
            self.logger.info(f"Contains {total_entries} confusable character entries")
            return output_file

        except Exception as e:
            self.logger.error(f"Failed to save confusables data: {e}")
            raise

    def parse_and_save(self, confusables_file: Union[str, Path], output_filename: str = "unicode_confusables.json") -> Path:
        """Parse confusables file and save the results"""
        self.logger.info("Starting to parse and save confusables data")
        # Parse file
        confusables_data = self.parse_confusables_file(confusables_file)

        if not confusables_data or not confusables_data.get("confusables_map"):
            self.logger.error("Parsing failed or no valid data found")
            return None

        # Save results
        output_file = self.save_confusables_data(confusables_data, output_filename)

        # Print summary
        self.print_parse_summary(confusables_data)

        return output_file

    def _parse_confusable_line(self, line: str, line_num: int) -> Dict[str, Any]:
        
        # Remove trailing comments and whitespace
        line = line.strip()
        if '#' in line:
            data_part = line.split('#')[0].strip()
            comment_part = line.split('#', 1)[1].strip()
        else:
            data_part = line
            comment_part = ""
        
        if not data_part:
            return None
        
        # Parse data part: source ; target ; type
        parts = [part.strip() for part in data_part.split(';')]
        if len(parts) < 3:
            self.logger.warning(f"Line {line_num} has incorrect format: {line}")
            return None
        
        source_code = parts[0]
        target_code = parts[1]
        conf_type = parts[2]
        
        try:
            # Convert Unicode code points to characters
            source_char = self._unicode_point_to_char(source_code)
            target_char = self._unicode_point_to_char(target_code)
            
            # Extract character names from comment
            source_name, target_name = self._extract_names_from_comment(comment_part)
            
            # Simplified entry structure without danger level
            entry = {
                "unicode_point": f"U+{source_code}",
                "character": source_char,
                "name": source_name or f"U+{source_code}",
                "confusable_with": {
                    "character": target_char,
                    "unicode_point": f"U+{target_code}",
                    "name": target_name or f"U+{target_code}"
                },
                "confusable_type": conf_type,
                "description": f"Confusable with {target_char} (type: {conf_type})",
                "source": "confusables.txt"
            }

            return entry
            
        
        except Exception as e:
            self.logger.warning(f"Line {line_num} character conversion Failed: {e}")
            return None
    
    def _unicode_point_to_char(self, unicode_point: str) -> str:
        """Convert Unicode code point to character"""
        try:
            # Remove possible prefixes and whitespace
            unicode_point = unicode_point.strip().upper()
            if unicode_point.startswith('U+'):
                unicode_point = unicode_point[2:]
            
            # Handle multiple code points (separated by spaces)
            if ' ' in unicode_point:
                code_points = unicode_point.split()
                chars = [chr(int(cp, 16)) for cp in code_points]
                return ''.join(chars)
            else:
                return chr(int(unicode_point, 16))
        
        except ValueError as e:
            self.logger.warning(f"Invalid Unicode code point: {unicode_point}")
            return ""
    
    def _extract_names_from_comment(self, comment: str) -> tuple:
        """Extract character names from comment"""
        try:
            # Comment format is usually: ( char → char ) NAME → NAME
            if '→' in comment and ')' in comment:
                # Extract part after the parenthesis
                if ')' in comment:
                    names_part = comment.split(')', 1)[1].strip()
                    if '→' in names_part:
                        parts = names_part.split('→')
                        source_name = parts[0].strip()
                        target_name = parts[1].strip() if len(parts) > 1 else ""
                        return source_name, target_name
            
            return "", ""
        
        except Exception:
            return "", ""
    
    def _log_parse_stats(self, stats: Dict[str, Any]):
        """Log parse statistics"""
        self.logger.info("Parse Statistics:")
        self.logger.info(f"  Total lines: {stats['total_lines']}")
        self.logger.info(f"  Comment lines: {stats['comment_lines']}")
        self.logger.info(f"  Empty lines: {stats['empty_lines']}")
        self.logger.info(f"  Parsed entries: {stats['parsed_entries']}")
        self.logger.info(f"  Error lines: {stats['error_lines']}")
        
        if stats['confusable_types']:
            self.logger.info("  Type distribution:")
            for conf_type, count in sorted(stats['confusable_types'].items()):
                self.logger.info(f"    {conf_type}: {count}")
    
    def convert_to_config_format(self, confusables_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert confusables data to config format"""

        config_characters = {}

        for unicode_point, data in confusables_data.items():
            # Convert to existing config format
            config_entry = {
                "char": data["char"],
                "name": data["name"],
                "similar_to": data["similar_to"],
                "description": data["description"],
                "confusable_type": data["confusable_type"],
                "unicode_source": data["unicode_source"]
                # Note: Do not add risk_level, use default level based on category
            }

            config_characters[unicode_point] = config_entry

        return config_characters
    
    def save_confusables_config(self, confusables_data: Dict[str, Any], 
                              output_file: Union[str, Path] = None) -> Path:
        """Save confusables config data"""
        
        if output_file is None:
            output_file = self.parser_output_dir / "confusables_config.json"
        else:
            output_file = Path(output_file)
        
        # Convert to config format
        config_data = self.convert_to_config_format(confusables_data)
        
        # Create full config structure
        full_config = {
            "confusables_info": {
                "source": "Unicode confusables.txt",
                "total_characters": len(config_data),
                "description": "Unicode confusable characters for homograph attack detection"
            },
            "characters": config_data
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Confusables config has been saved: {output_file}")
            self.logger.info(f"Contains {len(config_data)} characters")
            
            return output_file
        
        except Exception as e:
            self.logger.error(f"Saving confusables config failed: {e}")
            raise
    
    def print_parse_summary(self, confusables_data: Dict[str, Any]):
        """Print parse summary"""
        print("\n" + "="*60)
        print("📋 Unicode Confusables Parse Summary")
        print("="*60)

        metadata = confusables_data.get("metadata", {})
        confusables_map = confusables_data.get("confusables_map", {})

        print(f"📊 Total characters: {len(confusables_map)}")
        print(f"📅 Parse time: {metadata.get('parsed_time', 'Unknown')}")
        print(f"📁 Source file: {metadata.get('source_file', 'Unknown')}")

        # Count type distribution
        type_stats = {}
        for data in confusables_map.values():
            conf_type = data.get("confusable_type", "unknown")
            type_stats[conf_type] = type_stats.get(conf_type, 0) + 1

        print(f"\n📈 Type distribution:")
        for conf_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {conf_type}: {count:,} characters")

        # Show some examples
        print(f"\n📝 Character examples (first 5):")
        for i, (unicode_point, data) in enumerate(list(confusables_map.items())[:5]):
            char = data["character"]
            name = data["name"]
            confusable_with = data.get("confusable_with", {})
            target_char = confusable_with.get("character", "?")
            target_point = confusable_with.get("unicode_point", "?")

            print(f"   {i+1}. '{char}' ({unicode_point}) - {name}")
            print(f"      Confusable with: '{target_char}' ({target_point})")
        print("="*60)


def main():
    """Main function - Parse confusables.txt file"""
    print("🔧 Unicode Confusables Parser")
    print("="*50)

    # Create parser instance
    parser = ConfusablesParser()

    # Locate confusables.txt file
    current_dir = Path(__file__).parent.parent  # Go back to testscan directory
    confusables_file = current_dir / "confusables.txt"

    if not confusables_file.exists():
        print(f"❌ Confusables.txt file not found: {confusables_file}")
        print("Please ensure confusables.txt file is located in the testscan directory")
        return

    print(f"📁 Confusables file found: {confusables_file}")
    try:
        # 解析并保存
        output_file = parser.parse_and_save(confusables_file)

        if output_file:
            print(f"\n✅ Parsing Completed!")
            print(f"📄 Output File: {output_file.absolute()}")
        else:
            print(f"\n❌ Parsing Failed")

    except Exception as e:
        print(f"\n❌ Error during parsing: {e}")


if __name__ == "__main__":
    main()
