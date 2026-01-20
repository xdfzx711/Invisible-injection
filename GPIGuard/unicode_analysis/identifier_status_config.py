#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Set
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from data_collection.utils.logger import setup_logger


class IdentifierStatusConfig:

    
    def __init__(self, lookup_file: Union[str, Path] = None):
        # Set default lookup table file path
        if lookup_file is None:
            # Find testscan directory by going up from current file location
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            lookup_file = testscan_dir / "testscan_data" / "unicode_analysis" / "identifier_status_lookup.json"

        self.lookup_file = Path(lookup_file)
        self.logger = setup_logger('IdentifierStatusConfig', 'identifier_status_config.log')
        
        # Load lookup table
        self.allowed_characters = self._load_lookup_table()
        
        # Detection settings (simplified)
        self.detection_settings = {
            "enable_identifier_status_detection": True,
            "enable_normalization_detection": True,  # Keep normalization detection
            "output_format": "simple"  # simple or detailed
        }
        
        self.logger.info(f"Identifier status configuration has been loaded, containing {len(self.allowed_characters)} allowed characters")
    
    def _load_lookup_table(self) -> Set[str]:
        """Load identifier status lookup table"""
        try:
            if not self.lookup_file.exists():
                self.logger.error(f"Lookup table file does not exist: {self.lookup_file}")
                return set()
            
            with open(self.lookup_file, 'r', encoding='utf-8') as f:
                lookup_data = json.load(f)
            
            # Convert lookup table to a set for faster lookup
            # lookup_data format: {"U+0041": "Allowed", "U+0042": "Allowed", ...}
            allowed_chars = set()
            for unicode_point, status in lookup_data.items():
                if status == "Allowed":
                    allowed_chars.add(unicode_point)
            
            self.logger.info(f"Successfully loaded lookup table: {self.lookup_file}")
            return allowed_chars
            
        except Exception as e:
            self.logger.error(f"Failed to load lookup table: {e}")
            return set()
    
    def is_character_allowed(self, char: str) -> bool:
        """Check if a character is allowed"""
        if not char:
            return False
        
        unicode_point = f"U+{ord(char):04X}"
        return unicode_point in self.allowed_characters
    
    def is_character_restricted(self, char: str) -> bool:
        """Check if a character is restricted"""
        return not self.is_character_allowed(char)
    
    def get_character_status(self, char: str) -> str:
        """Get character status"""
        if self.is_character_allowed(char):
            return "Allowed"
        else:
            return "Restricted"
    
    def analyze_string_status(self, text: str) -> Dict[str, Any]:

        if not text:
            return {
                "total_chars": 0,
                "allowed_chars": 0,
                "restricted_chars": 0,
                "allowed_percentage": 0.0,
                "has_restricted_chars": False
            }
        
        allowed_count = 0
        restricted_count = 0
        
        for char in text:
            if self.is_character_allowed(char):
                allowed_count += 1
            else:
                restricted_count += 1
        
        total_chars = len(text)
        allowed_percentage = (allowed_count / total_chars) * 100 if total_chars > 0 else 0
        
        return {
            "total_chars": total_chars,
            "allowed_chars": allowed_count,
            "restricted_chars": restricted_count,
            "allowed_percentage": allowed_percentage,
            "has_restricted_chars": restricted_count > 0
        }
    
    def get_detection_settings(self) -> Dict[str, Any]:
   
        return self.detection_settings.copy()
    
    def is_detection_enabled(self, detection_type: str = "identifier_status") -> bool:
      
        setting_key = f"enable_{detection_type}_detection"
        return self.detection_settings.get(setting_key, True)
    
    def update_detection_setting(self, detection_type: str, enabled: bool):
      
        setting_key = f"enable_{detection_type}_detection"
        self.detection_settings[setting_key] = enabled
        self.logger.info(f"Detection setting has been updated: {setting_key} = {enabled}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        return {
            "total_allowed_characters": len(self.allowed_characters),
            "lookup_file": str(self.lookup_file),
            "detection_settings": self.detection_settings,
            "config_status": "loaded" if self.allowed_characters else "error"
        }
    
    def reload_lookup_table(self) -> bool:
        """Reload lookup table"""
        try:
            self.allowed_characters = self._load_lookup_table()
            self.logger.info("Lookup table reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload lookup table: {e}")
            return False
    
    def validate_lookup_table(self) -> Dict[str, Any]:
        """Validate the integrity of the lookup table"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            # Check if file exists
            if not self.lookup_file.exists():
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Lookup table file does not exist: {self.lookup_file}")
                return validation_result
            
            # Check if data exists
            if not self.allowed_characters:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Lookup table is empty")
                return validation_result
            
            # Statistics
            validation_result["statistics"] = {
                "total_allowed_chars": len(self.allowed_characters),
                "file_size": self.lookup_file.stat().st_size,
                "sample_chars": list(self.allowed_characters)[:10]  # Sample of first 10 characters
            }
            
            # Check if basic characters exist
            basic_chars = ["U+0041", "U+0061", "U+0030"]  # A, a, 0
            missing_basic = []
            for char_code in basic_chars:
                if char_code not in self.allowed_characters:
                    missing_basic.append(char_code)
            
            if missing_basic:
                validation_result["warnings"].append(f"Missing basic characters: {missing_basic}")
            
            self.logger.info("Lookup table validation completed")
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Error during validation: {e}")
        
        return validation_result


def main():
    """Test function"""
    print("=== Identifier Status Configuration Test ===\n")
    
    # Create configuration manager
    config = IdentifierStatusConfig()
    
    # Validate configuration
    validation = config.validate_lookup_table()
    print(f"Configuration validation: {'Passed' if validation['is_valid'] else 'Failed'}")
    if validation['errors']:
        print(f"Error: {validation['errors']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings']}")
    
    # Get statistics
    stats = config.get_statistics()
    print(f"\nStatistics:")
    print(f"  Allowed characters: {stats['total_allowed_characters']}")
    print(f"  Configuration status: {stats['config_status']}")
    
    # Test character status
    test_chars = ["a", "A", "1", "中", "α", "а", "🙂", "_", "-", "."]
    print(f"\nCharacter status test:")
    for char in test_chars:
        status = config.get_character_status(char)
        unicode_point = f"U+{ord(char):04X}"
        print(f"  '{char}' ({unicode_point}): {status}")
    
    # Test string analysis
    test_strings = ["hello_world", "test123", "café", "测试文本", "hello-world"]
    print(f"\nString analysis test:")
    for text in test_strings:
        analysis = config.analyze_string_status(text)
        print(f"  '{text}': {analysis['allowed_chars']}/{analysis['total_chars']} allowed "
              f"({analysis['allowed_percentage']:.1f}%) "
              f"{'with restricted characters' if analysis['has_restricted_chars'] else 'all allowed'}")


if __name__ == "__main__":
    main()
