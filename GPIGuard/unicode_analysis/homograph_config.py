#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union, Set
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_collection.utils.logger import setup_logger


class HomographConfig:
    
    def __init__(self, confusables_file: Union[str, Path] = None):
        # Set default confusables file path
        if confusables_file is None:
            # Find testscan directory by going up from current file location
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            confusables_file = testscan_dir / "testscan_data" / "unicode_analysis" / "unicode_confusables.json"

        self.confusables_file = Path(confusables_file)
        self.logger = setup_logger('HomographConfig', 'homograph_config.log')
        
        # Load confusables data
        self.confusables_data = self._load_confusables_data()
        
        # Create quick lookup sets (only include characters that can cause confusion)
        self.confusable_unicode_points = set()
        self.confusable_characters = set()
        
        if self.confusables_data:
            # Try to get confusables mapping from different data structures
            confusables_map = self.confusables_data.get("confusables_map", {})

            # If confusables_map not found, try latin_related_confusables
            if not confusables_map:
                confusables_map = self.confusables_data.get("latin_related_confusables", {})
                self.logger.info("Using latin_related_confusables data structure")

            for unicode_point, char_data in confusables_map.items():
                self.confusable_unicode_points.add(unicode_point)
                character = char_data.get("character", "")
                if character:
                    self.confusable_characters.add(character)
        
        self.logger.info(f"Homoglyph Characters have been loaded, containing {len(self.confusable_unicode_points)} confusable characters")
    
    def _load_confusables_data(self) -> Dict[str, Any]:
        """Load confusables data file"""
        if not self.confusables_file.exists():
            self.logger.warning(f"Confusables data file does not exist: {self.confusables_file}")
            return {}
        
        try:
            with open(self.confusables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Successfully loaded confusables data: {self.confusables_file}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse confusables data file: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load confusables data file: {e}")
            return {}
    
    def is_confusable_character(self, unicode_point: str) -> bool:
        """Check if the specified Unicode code point is a confusable character"""
        return unicode_point in self.confusable_unicode_points
    
    def is_confusable_char(self, character: str) -> bool:
        """Check if the specified character is a confusable character"""
        return character in self.confusable_characters
    
    def get_confusable_info(self, unicode_point: str) -> Dict[str, Any]:
        """Get confusable information for the specified Unicode code point"""
        if not self.confusables_data:
            return {}

        # Try to get confusables mapping from different data structures
        confusables_map = self.confusables_data.get("confusables_map", {})

        # If confusables_map not found, try latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        return confusables_map.get(unicode_point, {})
    
    def get_confusables_count(self) -> int:
        """Get total number of confusable characters"""
        return len(self.confusable_unicode_points)
    
    def get_confusables_metadata(self) -> Dict[str, Any]:
        """Get metadata of confusables data"""
        if not self.confusables_data:
            return {}
        
        return self.confusables_data.get("metadata", {})
    
    def validate_confusables_data(self) -> Dict[str, Any]:
        """Validate the integrity of confusables data"""
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        if not self.confusables_data:
            validation_result["errors"].append("Confusables data is empty")
            return validation_result
        
        # Check required fields
        confusables_map = self.confusables_data.get("confusables_map", {})

        # If confusables_map not found, try latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        if not confusables_map:
            validation_result["errors"].append("Missing confusables_map or latin_related_confusables field")
            return validation_result
        
        # Statistics
        validation_result["statistics"] = {
            "total_confusables": len(confusables_map),
            "confusable_types": {}
        }
        
        # Validate each entry
        valid_entries = 0
        for unicode_point, char_data in confusables_map.items():
            try:
                # Check required fields
                required_fields = ["character", "confusable_with"]
                for field in required_fields:
                    if field not in char_data:
                        validation_result["warnings"].append(f"Entry {unicode_point} is missing field: {field}")
                        continue
                
                # Count types
                conf_type = char_data.get("confusable_type", "unknown")
                validation_result["statistics"]["confusable_types"][conf_type] = \
                    validation_result["statistics"]["confusable_types"].get(conf_type, 0) + 1
                
                valid_entries += 1
                
            except Exception as e:
                validation_result["warnings"].append(f"Error validating entry {unicode_point}: {e}")
        
        validation_result["statistics"]["valid_entries"] = valid_entries
        
        # Determine if valid
        if not validation_result["errors"] and valid_entries > 0:
            validation_result["is_valid"] = True
        
        return validation_result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics of confusables data"""
        if not self.confusables_data:
            return {"total_confusables": 0, "config_status": "not_loaded"}
        
        # Try to get confusables map from different data structures
        confusables_map = self.confusables_data.get("confusables_map", {})

        # If confusables_map not found, try latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        # Count type distribution
        type_distribution = {}
        for char_data in confusables_map.values():
            conf_type = char_data.get("confusable_type", "unknown")
            type_distribution[conf_type] = type_distribution.get(conf_type, 0) + 1
        
        return {
            "total_confusables": len(confusables_map),
            "type_distribution": type_distribution,
            "config_status": "loaded",
            "config_file": str(self.confusables_file),
            "metadata": self.get_confusables_metadata()
        }


def main():
    """Test function"""
    print("=== Homoglyph Character Configuration Test ===\n")
    
    # Create configuration manager
    config = HomographConfig()
    
    # Validate configuration
    validation = config.validate_confusables_data()
    print(f"Configuration validation: {'Passed' if validation['is_valid'] else 'Failed'}")
    if validation['errors']:
        print(f"Error: {validation['errors']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings'][:3]}...")  # Only show first 3 warnings
    
    # Get statistics
    stats = config.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total confusables: {stats['total_confusables']}")
    print(f"  Configuration status: {stats['config_status']}")
    
    # Test character detection
    test_chars = [
        ("U+0430", "а"),  # Cyrillic letter a
        ("U+0061", "a"),  # Latin letter a
        ("U+043E", "о"),  # Cyrillic letter o
        ("U+006F", "o"),  # Latin letter o
    ]
    
    print(f"\nCharacter Detection Test:")
    for unicode_point, char in test_chars:
        is_confusable = config.is_confusable_character(unicode_point)
        print(f"  '{char}' ({unicode_point}): {'Is confusable character' if is_confusable else 'Is not confusable character'}")
        
        if is_confusable:
            info = config.get_confusable_info(unicode_point)
            confusable_with = info.get("confusable_with", {})
            target_char = confusable_with.get("character", "?")
            target_point = confusable_with.get("unicode_point", "?")
            print(f"    Confusable with: '{target_char}' ({target_point})")


if __name__ == "__main__":
    main()
