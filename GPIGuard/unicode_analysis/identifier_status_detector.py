#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from data_collection.utils.logger import setup_logger


try:
    from .identifier_status_config import IdentifierStatusConfig
except ImportError:
    from identifier_status_config import IdentifierStatusConfig


class IdentifierStatusDetector:


    def __init__(self, config: IdentifierStatusConfig, output_dir: Union[str, Path] = "testscan_data/unicode_analysis", data_sources: List[str] = None):
        self.config = config
        self.base_output_dir = Path(output_dir)
        self.data_sources = data_sources or ['general']


        self.output_dirs = {}
        for source in self.data_sources:
            source_output_dir = self.base_output_dir / f"threat_detection_{source}"
            source_output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dirs[source] = source_output_dir


        self.output_dir = self.base_output_dir
        

        self.logger = setup_logger('IdentifierStatusDetector', 'identifier_status_detector.log')
        
   
        self.detection_stats = {
            "total_characters_checked": 0,
            "restricted_characters_found": 0,
            "allowed_characters_found": 0,
            "normalization_issues_found": 0,
            "detection_time": 0.0
        }
    
    def detect_restrictions_in_characters(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        if not all_characters:
            self.logger.warning("No characters to detect")
            return []
        
        self.logger.info(f"Starting detection of identifier status for {len(all_characters)} characters")
        start_time = time.time()
        
        # Reset statistics
        self.detection_stats = {
            "total_characters_checked": 0,
            "restricted_characters_found": 0,
            "allowed_characters_found": 0,
            "normalization_issues_found": 0,
            "detection_time": 0.0
        }
        
        detections = []
        

        if self.config.is_detection_enabled("identifier_status"):
            detections.extend(self._detect_identifier_status(all_characters))
        

        if self.config.is_detection_enabled("normalization"):
            normalization_detections = self._detect_normalization_issues(all_characters)
            detections.extend(normalization_detections)
            self.detection_stats["normalization_issues_found"] = len(normalization_detections)
        
        end_time = time.time()
        self.detection_stats["detection_time"] = end_time - start_time
        
        self.logger.info(f"Detection completed, found {len(detections)} problematic characters")
        self.logger.info(f"  - Restricted characters: {self.detection_stats['restricted_characters_found']}")
        self.logger.info(f"  - Normalization issues: {self.detection_stats['normalization_issues_found']}")
        
        # Save detection results
        self._save_detection_results(detections)
        
        return detections
    
    def _detect_identifier_status(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect identifier status"""
        detections = []
        
        for char_info in all_characters:
            char = char_info.get("character", "")
            if not char:
                continue
            
            self.detection_stats["total_characters_checked"] += 1
            
            # Check if character is restricted
            if self.config.is_character_restricted(char):
                detection = self._create_restriction_detection(char_info)
                detections.append(detection)
                self.detection_stats["restricted_characters_found"] += 1
            else:
                self.detection_stats["allowed_characters_found"] += 1
        
        return detections
    
    def _create_restriction_detection(self, char_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create restriction detection record"""
        char = char_info.get("character", "")
        unicode_point = char_info.get("unicode_point", f"U+{ord(char):04X}")
        source_info = char_info.get("source_info", {})
        
        # Get basic character information
        try:
            char_name = unicodedata.name(char, f"UNNAMED-{unicode_point}")
            char_category = unicodedata.category(char)
        except ValueError:
            char_name = f"UNNAMED-{unicode_point}"
            char_category = "Cn"
        
        # Create simplified detection record
        detection = {
            "detection_id": f"restricted_{self.detection_stats['restricted_characters_found']:06d}",
            "character": char,
            "unicode_point": unicode_point,
            "status": "Restricted",
            "name": char_name,
            "category": char_category,
            "position_in_string": char_info.get("position_in_string", 0),
            "source_info": {
                "string_value": source_info.get("string_value", ""),
                "file_path": source_info.get("file_path", ""),
                "file_name": source_info.get("file_name", ""),
                "source_type": source_info.get("source_type", ""),
                "field_type": source_info.get("field_type", "")
            },
            "detection_info": {
                "detection_type": "identifier_status",
                "reason": "Character not in Unicode IdentifierStatus allowed list",
                "standard": "Unicode UTS #39",
                "severity": "restriction"
            }
        }
        
        return detection
    
    def _detect_normalization_issues(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect normalization issues (simplified version of existing functionality)"""
        normalization_detections = []
        processed_strings = set()
        
        for char_info in all_characters:
            normalization_info = char_info.get("normalization_info", {})
            
            if not normalization_info:
                continue
            
            # Avoid processing the same string multiple times
            original_string = normalization_info.get("original_string", "")
            if original_string in processed_strings:
                continue
            processed_strings.add(original_string)
            
            # Check if there are normalization changes
            if normalization_info.get("has_normalization_changes", False):
                detection = self._create_normalization_detection(char_info, normalization_info)
                if detection:
                    normalization_detections.append(detection)
        
        return normalization_detections
    
    def _create_normalization_detection(self, char_info: Dict[str, Any], normalization_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create normalization issue detection record"""
        source_info = char_info.get("source_info", {})
        
        detection = {
            "detection_id": f"normalization_{len(self.detection_stats):06d}",
            "detection_type": "normalization_issue",
            "original_string": normalization_info.get("original_string", ""),
            "normalized_string": normalization_info.get("final_string_used", ""),
            "normalization_changes": normalization_info.get("normalization_changes", []),
            "risk_level": normalization_info.get("normalization_risk_level", "low"),
            "source_info": {
                "file_path": source_info.get("file_path", ""),
                "file_name": source_info.get("file_name", ""),
                "source_type": source_info.get("source_type", ""),
                "field_type": source_info.get("field_type", "")
            },
            "detection_info": {
                "detection_type": "normalization",
                "reason": "String contains characters that change during Unicode normalization",
                "severity": "warning"
            }
        }
        
        return detection
    
    def _save_detection_results(self, detections: List[Dict[str, Any]]):
        """Save detection results"""
        if not detections:
            self.logger.info("No detection results to save")
            return

        # Group by source and detection type for saving
        source_detection_groups = {}
        for detection in detections:
            # Get source information
            source_type = detection.get("source_info", {}).get("source_type", "general")
            detection_type = detection.get("detection_info", {}).get("detection_type", "unknown")

            if source_type not in source_detection_groups:
                source_detection_groups[source_type] = {}
            if detection_type not in source_detection_groups[source_type]:
                source_detection_groups[source_type][detection_type] = []

            source_detection_groups[source_type][detection_type].append(detection)

      
        self.logger.info(f"Detection completed, total {len(detections)} entries (using new format threat reports)")
        

    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return self.detection_stats.copy()


def main():
    """Test function"""
    print("=== Identifier Status Detector Test ===\n")
    
    # Create config and detector
    config = IdentifierStatusConfig()
    detector = IdentifierStatusDetector(config)
    
    # Simulate character data
    test_characters = [
        {
            "character": "a",
            "unicode_point": "U+0061",
            "position_in_string": 0,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        },
        {
            "character": "а",  # Cyrillic letter a
            "unicode_point": "U+0430",
            "position_in_string": 1,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        },
        {
            "character": "🙂",  # Emoji
            "unicode_point": "U+1F642",
            "position_in_string": 2,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        }
    ]
    

    detections = detector.detect_restrictions_in_characters(test_characters)
    

    print(f"Detection completed, found {len(detections)} issues")
    for detection in detections:
        char = detection.get("character", "")
        status = detection.get("status", "")
        detection_type = detection.get("detection_info", {}).get("detection_type", "")
        print(f"  '{char}' ({detection.get('unicode_point', '')}): {status} ({detection_type})")
    
    # Show statistics
    stats = detector.get_detection_statistics()
    print(f"\nStatistics:")
    print(f"  Total characters checked: {stats['total_characters_checked']}")
    print(f"  Restricted characters found: {stats['restricted_characters_found']}")
    print(f"  Allowed characters found: {stats['allowed_characters_found']}")
    print(f"  Detection time: {stats['detection_time']:.3f} seconds")


if __name__ == "__main__":
    main()
