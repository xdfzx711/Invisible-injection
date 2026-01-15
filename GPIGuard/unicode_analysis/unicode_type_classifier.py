#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unicode Type Classifier
Classify Unicode threat characters into 5 categories:
0 - tag_chars (Unicode Tag Characters)
1 - zero_width (Zero-Width Characters)
2 - confusables (Confusable/Homoglyph Characters)
3 - bidi (Bidirectional Text Override Characters)
4 - zero_width_confusables_combined (Combined Type)
"""

from typing import Dict, Set, List, Any
from pathlib import Path
import json


class UnicodeTypeClassifier:
    """Unicode Threat Type Classifier"""
    
    # Unicode type definitions
    UNICODE_TYPES = {
        0: {
            "name": "tag_chars",
            "description": "Unicode Tag Characters",
            "range_start": 0xE0000,
            "range_end": 0xE007F
        },
        1: {
            "name": "zero_width",
            "description": "Zero-Width Characters",
            "chars": [
                "U+200B",  # ZERO WIDTH SPACE
                "U+200C",  # ZERO WIDTH NON-JOINER
                "U+200D",  # ZERO WIDTH JOINER
                "U+FEFF",  # ZERO WIDTH NO-BREAK SPACE
                "U+2060",  # WORD JOINER
                "U+180E",  # MONGOLIAN VOWEL SEPARATOR
                "U+FE0F",  # VARIATION SELECTOR-16
                "U+FE0E",  # VARIATION SELECTOR-15
            ]
        },
        2: {
            "name": "confusables",
            "description": "Confusable Characters (Homographs)"
        },
        3: {
            "name": "bidi",
            "description": "Bidirectional Text Override Characters",
            "chars": [
                "U+202A",  # LEFT-TO-RIGHT EMBEDDING
                "U+202B",  # RIGHT-TO-LEFT EMBEDDING
                "U+202C",  # POP DIRECTIONAL FORMATTING
                "U+202D",  # LEFT-TO-RIGHT OVERRIDE
                "U+202E",  # RIGHT-TO-LEFT OVERRIDE
                "U+2066",  # LEFT-TO-RIGHT ISOLATE
                "U+2067",  # RIGHT-TO-LEFT ISOLATE
                "U+2068",  # FIRST STRONG ISOLATE
                "U+2069",  # POP DIRECTIONAL ISOLATE
            ]
        },
        4: {
            "name": "zero_width_confusables_combined",
            "description": "Combined Zero-Width and Confusables in same string"
        }
    }
    
    def __init__(self, confusables_file: Path = None):
        """
        Initialize the classifier
        
        Args:
            confusables_file: Path to confusables data file
        """
        # Build fast lookup sets
        self.zero_width_chars = set()
        for char_code in self.UNICODE_TYPES[1]["chars"]:
            self.zero_width_chars.add(char_code)
        
        self.bidi_chars = set()
        for char_code in self.UNICODE_TYPES[3]["chars"]:
            self.bidi_chars.add(char_code)
        
        # Load confusables data
        self.confusables_chars = set()
        if confusables_file and confusables_file.exists():
            self._load_confusables(confusables_file)
    
    def _load_confusables(self, confusables_file: Path):
        """Load confusables character set"""
        try:
            with open(confusables_file, 'r', encoding='utf-8') as f:
                confusables_data = json.load(f)
            
            # confusables_data format: {"U+0430": {...}, ...}
            self.confusables_chars = set(confusables_data.keys())
            
        except Exception as e:
            print(f"Warning: Failed to load confusables data: {e}")
    
    def classify_character(self, unicode_point: str) -> List[int]:
        """
        Classify a single character and return list of type IDs
        
        Args:
            unicode_point: Unicode code point (format: "U+XXXX")
        
        Returns:
            List of type IDs (a character may belong to multiple types)
        """
        types = []
        
        # Check for tag_chars (type 0)
        if self._is_tag_char(unicode_point):
            types.append(0)
        
        # Check for zero_width (type 1)
        if unicode_point in self.zero_width_chars:
            types.append(1)
        
        # Check for confusables (type 2)
        if unicode_point in self.confusables_chars:
            types.append(2)
        
        # Check for bidi (type 3)
        if unicode_point in self.bidi_chars:
            types.append(3)
        
        return types
    
    def _is_tag_char(self, unicode_point: str) -> bool:
        """Check if character is a Tag character"""
        try:
            # Remove "U+" prefix and convert to integer
            code_point = int(unicode_point[2:], 16)
            range_def = self.UNICODE_TYPES[0]
            return range_def["range_start"] <= code_point <= range_def["range_end"]
        except:
            return False
    
    def classify_string_threats(self, text: str, detected_chars: List[Dict[str, Any]]) -> int:
        """
        Classify threat types in a string
        
        Args:
            text: Original text
            detected_chars: List of detected threat characters
        
        Returns:
            Unicode type ID (0-4)
        """
        if not detected_chars:
            return None
        
        # Count characters by type
        type_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        
        for char_info in detected_chars:
            unicode_point = char_info.get("unicode_point", "")
            char_types = self.classify_character(unicode_point)
            
            for type_id in char_types:
                type_counts[type_id] += 1
        
        # Check if this is combined type (type 4)
        has_zero_width = type_counts[1] > 0
        has_confusables = type_counts[2] > 0
        
        if has_zero_width and has_confusables:
            return 4  # Combined type
        
        # Return the most common type
        for type_id in [3, 2, 1, 0]:  # Priority order
            if type_counts[type_id] > 0:
                return type_id
        
        return None
    
    def get_type_name(self, type_id: int) -> str:
        """Get type name"""
        return self.UNICODE_TYPES.get(type_id, {}).get("name", "unknown")
    
    def get_type_description(self, type_id: int) -> str:
        """Get type description"""
        return self.UNICODE_TYPES.get(type_id, {}).get("description", "Unknown Type")
    
    def get_all_types(self) -> Dict[int, Dict[str, str]]:
        """Get all type definitions"""
        return {
            type_id: {
                "name": info["name"],
                "description": info["description"]
            }
            for type_id, info in self.UNICODE_TYPES.items()
        }


# Example usage
if __name__ == "__main__":
    classifier = UnicodeTypeClassifier()
    
    # Test character classification
    test_chars = [
        "U+200B",  # Zero-width space
        "U+202E",  # BiDi override
        "U+0430",  # Cyrillic letter a (confusable)
        "U+E0020", # Tag character
    ]
    
    print("Unicode Type Classification Test:\n")
    for char in test_chars:
        types = classifier.classify_character(char)
        print(f"{char}: Type {types}")
    
    print("\nAll Type Definitions:")
    for type_id, info in classifier.get_all_types().items():
        print(f"{type_id}: {info['name']} - {info['description']}")

