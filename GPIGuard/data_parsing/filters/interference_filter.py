#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import unicodedata
from typing import Dict, List, Any, Tuple
from pathlib import Path
import sys

# Add project root directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_collection.utils.logger import setup_logger
from .filter_config import (
    INTERFERENCE_FILTER_CONFIG,
    INTERFERENCE_RANGES,
    INTERFERENCE_CHARS,
    PROTECTED_ATTACK_RANGES,
    KAOMOJI_PATTERNS,
    PRESERVED_FORMAT_CHARS
)


class InterferenceCharacterFilter:
    """Interference Character Filter"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize filter

        Args:
            config: Filter config, use default if None
        """
        self.config = config or INTERFERENCE_FILTER_CONFIG.copy()
        self.logger = setup_logger('InterferenceCharacterFilter')

        # Interference character ranges
        self.interference_ranges = INTERFERENCE_RANGES
        
        # Interference character set
        self.interference_chars = INTERFERENCE_CHARS
        
        # Protected attack character ranges
        self.protected_attack_ranges = PROTECTED_ATTACK_RANGES
        
        # Kaomoji patterns
        self.kaomoji_patterns = [re.compile(pattern) for pattern in KAOMOJI_PATTERNS]
        
        # Format control characters to preserve
        self.preserved_format_chars = PRESERVED_FORMAT_CHARS

        # Statistics
        self.stats = {
            'total_chars_processed': 0,
            'interference_chars_removed': 0,
            'attack_chars_preserved': 0,
            'normal_chars_preserved': 0,
            'texts_processed': 0,
            'filtered_char_details': []
        }

        self.logger.info("Interference character filter initialization completed")
        self.logger.info(f"Config: {self.config}")

    def _is_interference_char(self, char: str) -> bool:
        """Check if character is an interference character"""
        # First check if in specific interference character set
        if char in self.interference_chars:
            return True
            
        code_point = ord(char)
        
        # Check if in interference character ranges
        for start, end in self.interference_ranges:
            if start <= code_point <= end:
                return True
        
        # Check if matches kaomoji patterns
        for pattern in self.kaomoji_patterns:
            if pattern.search(char):
                return True
        
        return False

    def _is_protected_char(self, char: str) -> bool:
        """Check if character is a protected attack character"""
        code_point = ord(char)
        
        # Check if in protected attack character ranges
        for start, end in self.protected_attack_ranges:
            if start <= code_point <= end:
                return True
                
        return False

    def clean_text(self, text: str) -> str:
        """
        Clean interference characters from text

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        if not text or not self.config.get('enabled', False):
            return text

        self.stats['texts_processed'] += 1
        original_length = len(text)
        preserved_chars = []
        removed_details = []

        for i, char in enumerate(text):
            self.stats['total_chars_processed'] += 1

            # 1. First check if format control character (always preserve)
            if char in self.preserved_format_chars:
                preserved_chars.append(char)
                continue

            # 2. Check if protected attack character (always preserve)
            if self._is_protected_char(char):
                preserved_chars.append(char)
                self.stats['attack_chars_preserved'] += 1
                
                if self.config.get('log_filtered_chars', False):
                    self.logger.debug(f"Preserve attack character: '{char}' (U+{ord(char):04X}) at position {i}")
                continue

            # 3. Check if interference character (remove)
            if self._is_interference_char(char):
                removed_details.append({
                    'char': char,
                    'unicode_point': f"U+{ord(char):04X}",
                    'name': unicodedata.name(char, 'UNKNOWN'),
                    'position': i,
                    'reason': 'interference_char'
                })
                self.stats['interference_chars_removed'] += 1
                
                if self.config.get('log_filtered_chars', False):
                    self.logger.debug(f"Remove interference character: '{char}' (U+{ord(char):04X}) at position {i}")
                continue

            # 4. Other characters (normal text) preserve
            preserved_chars.append(char)
            self.stats['normal_chars_preserved'] += 1

        result_text = ''.join(preserved_chars)

        if removed_details and self.config.get('output_report', False):
            self.stats['filtered_char_details'].append({
                'original_text': text[:100] + '...' if len(text) > 100 else text,
                'cleaned_text': result_text[:100] + '...' if len(result_text) > 100 else result_text,
                'original_length': original_length,
                'cleaned_length': len(result_text),
                'removed_chars': removed_details,
                'chars_removed_count': len(removed_details)
            })

        if removed_details:
            self.logger.info(f"Removed {len(removed_details)} interference characters from text")

        return result_text

    def clean_text_list(self, texts: List[str]) -> List[str]:
        """Batch clean text list"""
        return [self.clean_text(text) for text in texts]

    def get_statistics(self) -> Dict[str, Any]:
        """Get filter statistics"""
        return {
            'config': self.config,
            'stats': self.stats.copy(),
            'interference_ranges_count': len(self.interference_ranges),
            'protected_ranges_count': len(self.protected_attack_ranges),
            'kaomoji_patterns_count': len(self.kaomoji_patterns)
        }

    def generate_filter_report(self) -> Dict[str, Any]:
        """Generate detailed filter report"""
        stats = self.get_statistics()

        char_distribution = {}
        for detail in self.stats['filtered_char_details']:
            for removed_char in detail['removed_chars']:
                unicode_point = removed_char['unicode_point']
                if unicode_point not in char_distribution:
                    char_distribution[unicode_point] = {
                        'char': removed_char['char'],
                        'name': removed_char['name'],
                        'count': 0,
                        'reason': removed_char['reason']
                    }
                char_distribution[unicode_point]['count'] += 1

        sorted_chars = sorted(
            char_distribution.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        report = {
            'summary': {
                'total_texts_processed': self.stats['texts_processed'],
                'total_chars_processed': self.stats['total_chars_processed'],
                'interference_chars_removed': self.stats['interference_chars_removed'],
                'attack_chars_preserved': self.stats['attack_chars_preserved'],
                'normal_chars_preserved': self.stats['normal_chars_preserved'],
                'unique_removed_chars': len(char_distribution),
                'filter_strategy': self.config['mode']
            },
            'config_used': self.config,
            'removed_character_distribution': dict(sorted_chars[:20]),
            'sample_filtered_texts': self.stats['filtered_char_details'][:10],
            'ranges_info': {
                'interference_ranges': len(self.interference_ranges),
                'protected_ranges': len(self.protected_attack_ranges),
                'kaomoji_patterns': len(self.kaomoji_patterns)
            }
        }
        return report

    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'total_chars_processed': 0,
            'interference_chars_removed': 0,
            'attack_chars_preserved': 0,
            'normal_chars_preserved': 0,
            'texts_processed': 0,
            'filtered_char_details': []
        }
        self.logger.info("Statistics have been reset")


def create_default_filter() -> InterferenceCharacterFilter:
    """Create default filter with default config"""
    return InterferenceCharacterFilter()


def create_enabled_filter() -> InterferenceCharacterFilter:
    """Create enabled filter with default config"""
    config = INTERFERENCE_FILTER_CONFIG.copy()
    config['enabled'] = True
    return InterferenceCharacterFilter(config)

if __name__ == "__main__":
    # Test code
    filter_instance = create_enabled_filter()

    test_texts = [
        "Hello 🚀 World! This is a test with emoji.",
        "Mathematical formula: ∑∫∆√π∞≈≠≤≥±∓",
        "Kaomoji test: (╯°□°）╯︵ ┻━┻ and ¯\\_(ツ)_/¯",
        "Chinese text: 这是中文测试文本",
        "Mixed: Hello 世界 with emoji 😊 and math ∑",
        "Unicode attack: Normal text󠁕󠁴󠁩󠁬󠁩󠁺󠁥 with tag characters",
        "Test with zero-width: A⁠B⁠C and mathematical 𝑓𝒘𝒈",
        "Normal text with punctuation: Hello, world! How are you?"
    ]

    print("=== Interference Character Filter Test ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}:")
        print(f"Original: {text}")
        cleaned = filter_instance.clean_text(text)
        print(f"Cleaned: {cleaned}")

    print("\n=== Statistics ===")
    stats = filter_instance.get_statistics()
    print(f"Texts processed: {stats['stats']['texts_processed']}")
    print(f"Characters processed: {stats['stats']['total_chars_processed']}")
    print(f"Interference characters removed: {stats['stats']['interference_chars_removed']}")
    print(f"Attack characters preserved: {stats['stats']['attack_chars_preserved']}")
    print(f"Normal characters preserved: {stats['stats']['normal_chars_preserved']}")