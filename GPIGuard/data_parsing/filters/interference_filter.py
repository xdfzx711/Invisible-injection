#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
干扰字符过滤器
移除干扰字符（emoji、数学符号、kaomoji等），保留正常字符和攻击字符
"""

import re
import unicodedata
from typing import Dict, List, Any, Tuple
from pathlib import Path
import sys

# 添加项目根directory到路径
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
    """干扰字符过滤器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化过滤器

        Args:
            config: 过滤器配置，如果为None则使用默认配置
        """
        self.config = config or INTERFERENCE_FILTER_CONFIG.copy()
        self.logger = setup_logger('InterferenceCharacterFilter')

        # 干扰字符范围
        self.interference_ranges = INTERFERENCE_RANGES
        
        # 干扰字符集合
        self.interference_chars = INTERFERENCE_CHARS
        
        # 受保护的攻击字符范围
        self.protected_attack_ranges = PROTECTED_ATTACK_RANGES
        
        # Kaomoji模式
        self.kaomoji_patterns = [re.compile(pattern) for pattern in KAOMOJI_PATTERNS]
        
        # 需要保留的格式控制字符
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

        self.logger.info("干扰字符过滤器初始化Completed")
        self.logger.info(f"配置: {self.config}")

    def _is_interference_char(self, char: str) -> bool:
        """Check字符是否是干扰字符"""
        # 首先Check是否在具体的干扰字符集合中
        if char in self.interference_chars:
            return True
            
        code_point = ord(char)
        
        # Check是否在干扰字符范围内
        for start, end in self.interference_ranges:
            if start <= code_point <= end:
                return True
        
        # Check是否匹配kaomoji模式
        for pattern in self.kaomoji_patterns:
            if pattern.search(char):
                return True
        
        return False

    def _is_protected_char(self, char: str) -> bool:
        """Check字符是否是受保护的攻击字符"""
        code_point = ord(char)
        
        # Check是否在受保护的攻击字符范围内
        for start, end in self.protected_attack_ranges:
            if start <= code_point <= end:
                return True
                
        return False

    def clean_text(self, text: str) -> str:
        """
        清理文本中的干扰字符

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        if not text or not self.config.get('enabled', False):
            return text

        self.stats['texts_processed'] += 1
        original_length = len(text)
        preserved_chars = []
        removed_details = []

        for i, char in enumerate(text):
            self.stats['total_chars_processed'] += 1

            # 1. 首先Check是否是格式控制字符（始终保留）
            if char in self.preserved_format_chars:
                preserved_chars.append(char)
                continue

            # 2. Check是否是受保护的攻击字符（始终保留）
            if self._is_protected_char(char):
                preserved_chars.append(char)
                self.stats['attack_chars_preserved'] += 1
                
                if self.config.get('log_filtered_chars', False):
                    self.logger.debug(f"保留攻击字符: '{char}' (U+{ord(char):04X}) at position {i}")
                continue

            # 3. Check是否是干扰字符（移除）
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
                    self.logger.debug(f"移除干扰字符: '{char}' (U+{ord(char):04X}) at position {i}")
                continue

            # 4. 其他字符（正常字符）保留
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
            self.logger.info(f"从文本中移除了 {len(removed_details)} 个干扰字符")

        return result_text

    def clean_text_list(self, texts: List[str]) -> List[str]:
        """批量清理文本列表"""
        return [self.clean_text(text) for text in texts]

    def get_statistics(self) -> Dict[str, Any]:
        """获取过滤Statistics"""
        return {
            'config': self.config,
            'stats': self.stats.copy(),
            'interference_ranges_count': len(self.interference_ranges),
            'protected_ranges_count': len(self.protected_attack_ranges),
            'kaomoji_patterns_count': len(self.kaomoji_patterns)
        }

    def generate_filter_report(self) -> Dict[str, Any]:
        """生成详细的过滤报告"""
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
        """重置Statistics"""
        self.stats = {
            'total_chars_processed': 0,
            'interference_chars_removed': 0,
            'attack_chars_preserved': 0,
            'normal_chars_preserved': 0,
            'texts_processed': 0,
            'filtered_char_details': []
        }
        self.logger.info("Statisticshas been重置")


def create_default_filter() -> InterferenceCharacterFilter:
    """创建默认配置的干扰字符过滤器"""
    return InterferenceCharacterFilter()


def create_enabled_filter() -> InterferenceCharacterFilter:
    """创建启用的干扰字符过滤器"""
    config = INTERFERENCE_FILTER_CONFIG.copy()
    config['enabled'] = True
    return InterferenceCharacterFilter(config)

if __name__ == "__main__":
    # 测试代码
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

    print("=== 干扰字符过滤器测试 ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试 {i}:")
        print(f"原文: {text}")
        cleaned = filter_instance.clean_text(text)
        print(f"清理后: {cleaned}")

    print("\n=== Statistics ===")
    stats = filter_instance.get_statistics()
    print(f"处理文本数: {stats['stats']['texts_processed']}")
    print(f"处理字符数: {stats['stats']['total_chars_processed']}")
    print(f"移除干扰字符数: {stats['stats']['interference_chars_removed']}")
    print(f"保留攻击字符数: {stats['stats']['attack_chars_preserved']}")
    print(f"保留正常字符数: {stats['stats']['normal_chars_preserved']}")