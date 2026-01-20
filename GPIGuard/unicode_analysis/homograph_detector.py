#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import unicodedata


sys.path.append(str(Path(__file__).parent.parent))
from data_collection.utils.logger import setup_logger

# Fix relative import issues
try:
    from .homograph_config import HomographConfig
except ImportError:
    from homograph_config import HomographConfig


class HomographDetector:
    """Homoglyph Character detector"""

    def __init__(self, config: HomographConfig, output_dir: Union[str, Path] = "testscan_data/unicode_analysis", data_sources: List[str] = None):
        self.config = config
        self.base_output_dir = Path(output_dir)
        self.data_sources = data_sources or ['general']

        # Create output directory for each data source
        self.output_dirs = {}
        for source in self.data_sources:
            source_output_dir = self.base_output_dir / f"threat_detection_{source}"
            source_output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dirs[source] = source_output_dir

        # Set up logger
        self.logger = setup_logger('HomographDetector', 'homograph_detector.log')
        
        # Detection statistics
        self.detection_stats = {
            "total_characters_checked": 0,
            "homograph_characters_found": 0,
            "detection_time": 0.0
        }
        
        self.logger.info(f"Homoglyph Character detector has been initialized, data sources: {', '.join(self.data_sources)}")
        self.logger.info(f"Can detect {self.config.get_confusables_count()} confusable characters")
    
    def detect_homographs_in_characters(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect Homoglyph Characters in a list of characters"""
        if not all_characters:
            self.logger.warning("No characters to detect")
            return []
        
        self.logger.info(f"Starting detection of Homoglyph Characters in {len(all_characters)} characters")
        start_time = time.time()
        
        # Reset statistics
        self.detection_stats = {
            "total_characters_checked": 0,
            "homograph_characters_found": 0,
            "detection_time": 0.0
        }
        
        # Group characters by data source
        characters_by_source = self._group_characters_by_source(all_characters)
        
        all_detections = []
        
        # Detect and save separately for each data source
        for source_type, source_characters in characters_by_source.items():
            self.logger.info(f"Detecting {len(source_characters)} characters from {source_type} data source")
            
            source_detections = self._detect_homographs_for_source(source_type, source_characters)
            
            if source_detections:
                # Save to corresponding data source directory
                self._save_homograph_detections(source_type, source_detections)
                all_detections.extend(source_detections)
                
                self.logger.info(f"{source_type} data source found {len(source_detections)} Homoglyph Characters")
            else:
                self.logger.info(f"{source_type} data source found no Homoglyph Characters")
        
        # Update statistics
        end_time = time.time()
        self.detection_stats["detection_time"] = end_time - start_time
        
        self.logger.info(f"Homoglyph Character detection completed, found {len(all_detections)} confusable characters")
        self.logger.info(f"Detection time: {self.detection_stats['detection_time']:.3f} seconds")
        
        return all_detections
    
    def _group_characters_by_source(self, all_characters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group characters by their data source type"""
        characters_by_source = {}
        
        for char_info in all_characters:
            # Get data source type from source_info
            source_info = char_info.get("source_info", {})
            source_type = source_info.get("source_type", "unknown")
            
            # If source_type is not in configured data sources, try to infer from file path
            if source_type == "unknown" or source_type not in self.data_sources:
                source_type = self._infer_source_type(char_info)
            
            if source_type not in characters_by_source:
                characters_by_source[source_type] = []
            
            characters_by_source[source_type].append(char_info)
        
        return characters_by_source
    
    def _infer_source_type(self, char_info: Dict[str, Any]) -> str:
        """Infer data source type from character information"""
        source_info = char_info.get("source_info", {})
        

        file_path = source_info.get("file_path", "")
        if file_path:
            if "godofprompt" in file_path.lower():
                return "godofprompt"
            elif "github" in file_path.lower():
                return "github"
            elif "reddit" in file_path.lower():
                return "reddit"
            elif "twitter" in file_path.lower():
                return "twitter"
            elif "html" in file_path.lower():
                return "html"
            elif "json" in file_path.lower():
                return "json"
            elif "csv" in file_path.lower():
                return "csv"
            elif "xml" in file_path.lower():
                return "xml"
        
        # Default to the first configured data source
        return self.data_sources[0] if self.data_sources else "general"
    
    def _detect_homographs_for_source(self, source_type: str, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect Homoglyph Characters for a specific data source"""
        detections = []
        
        for char_info in characters:
            self.detection_stats["total_characters_checked"] += 1
            
            unicode_point = char_info.get("unicode_point", "")
            character = char_info.get("character", "")

            # Skip punctuation, symbols, etc.
            if character:
                category = unicodedata.category(character[0])
                if not (category.startswith('L') or category.startswith('N')):
                    continue

            
                if '0' <= character <= '9':
                    continue
            
            
            if self.config.is_confusable_character(unicode_point):
                confusable_info = self.config.get_confusable_info(unicode_point)
                
                if confusable_info:
                    detection = self._create_homograph_detection(char_info, confusable_info)
                    detections.append(detection)
                    self.detection_stats["homograph_characters_found"] += 1
        
        return detections
    
    def _create_homograph_detection(self, char_info: Dict[str, Any], confusable_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Homoglyph Character detection record"""
        return {
            "detection_id": f"homograph_{uuid.uuid4().hex[:8]}",
            "detection_type": "homograph_character",
            "character": char_info["character"],
            "unicode_point": char_info["unicode_point"],

            # Confusable information
            "confusable_with": confusable_info.get("confusable_with", {}),
            "confusable_type": confusable_info.get("confusable_type", "unknown"),
            "description": confusable_info.get("description", ""),

            # Source information
            "source_info": {
                **char_info.get("source_info", {}),
                "position_in_string": char_info.get("position_in_string")
            },
            # Removed context field to simplify report structure

            # Detection metadata
            "detection_time": datetime.now().isoformat(),
            "detector_version": "1.0.0"
        }
    
    def _save_homograph_detections(self, source_type: str, detections: List[Dict[str, Any]]):
        """Save Homoglyph character detection results to the corresponding data source directory"""
        output_dir = self.output_dirs.get(source_type)
        if not output_dir:
            self.logger.warning(f"Output directory for data source {source_type} not found")
            return
        
        # Save detailed detection results
        detections_file = output_dir / "homograph_detections.json"
        
        detection_data = {
            "metadata": {
                "source_type": source_type,
                "total_detections": len(detections),
                "detection_time": datetime.now().isoformat(),
                "detector_version": "1.0.0"
            },
            "detections": detections
        }
        
        try:
            with open(detections_file, 'w', encoding='utf-8') as f:
                json.dump(detection_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Homoglyph character detection results have been saved to: {detections_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save Homoglyph character detection results: {e}")
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return self.detection_stats.copy()


def main():
    """Test function"""
    print("=== Homoglyph Character Detector Test ===\n")
    
    
    config = HomographConfig()
    detector = HomographDetector(config, "testscan_data/unicode_analysis", ["test"])
    
    
    test_characters = [
        {
            "character": "а",  
            "unicode_point": "U+0430",
            "source_info": {"source_type": "test", "file_path": "test.txt"},
            "context": {"string_value": "test", "position": 0}
        },
        {
            "character": "a", 
            "unicode_point": "U+0061",
            "source_info": {"source_type": "test", "file_path": "test.txt"},
            "context": {"string_value": "test", "position": 1}
        }
    ]
    
   
    detections = detector.detect_homographs_in_characters(test_characters)
    

    print(f"Detection Completed, found {len(detections)} Homoglyph Characters")
    for detection in detections:
        char = detection.get("character", "")
        unicode_point = detection.get("unicode_point", "")
        confusable_with = detection.get("confusable_with", {})
        target_char = confusable_with.get("character", "?")
        target_point = confusable_with.get("unicode_point", "?")
        
        print(f"  '{char}' ({unicode_point}) is confusable with '{target_char}' ({target_point})")
    
    # Display statistics
    stats = detector.get_detection_statistics()
    print(f"\nStatistics:")
    print(f"  Total characters checked: {stats['total_characters_checked']}")
    print(f"  Homoglyph characters found: {stats['homograph_characters_found']}")
    print(f"  Detection time: {stats['detection_time']:.3f} seconds")


if __name__ == "__main__":
    main()
