#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Homoglyph Character配置管理器
加载和管理 unicode_confusables.json 数据
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union, Set
import sys
import os

# 添加项目根directory到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目工具
from data_collection.utils.logger import setup_logger


class HomographConfig:
    """Homoglyph Character配置管理器"""
    
    def __init__(self, confusables_file: Union[str, Path] = None):
        # 设置默认confusablesFile路径
        if confusables_file is None:
            # 从当前File位置向上找到testscandirectory
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            confusables_file = testscan_dir / "testscan_data" / "unicode_analysis" / "unicode_confusables.json"

        self.confusables_file = Path(confusables_file)
        self.logger = setup_logger('HomographConfig', 'homograph_config.log')
        
        # Load confusables data
        self.confusables_data = self._load_confusables_data()
        
        # 创建快速查找集合（只包含会引起混淆的字符）
        self.confusable_unicode_points = set()
        self.confusable_characters = set()
        
        if self.confusables_data:
            # 尝试从不同的数据结构中获取confusables映射
            confusables_map = self.confusables_data.get("confusables_map", {})

            # 如果没有找到confusables_map，尝试latin_related_confusables
            if not confusables_map:
                confusables_map = self.confusables_data.get("latin_related_confusables", {})
                self.logger.info("使用latin_related_confusables数据结构")

            for unicode_point, char_data in confusables_map.items():
                self.confusable_unicode_points.add(unicode_point)
                character = char_data.get("character", "")
                if character:
                    self.confusable_characters.add(character)
        
        self.logger.info(f"Homoglyph Character配置has been加载，包含 {len(self.confusable_unicode_points)} 个混淆字符")
    
    def _load_confusables_data(self) -> Dict[str, Any]:
        """Load confusables dataFile"""
        if not self.confusables_file.exists():
            self.logger.warning(f"Confusables数据File不exists: {self.confusables_file}")
            return {}
        
        try:
            with open(self.confusables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"成功Load confusables data: {self.confusables_file}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析confusables数据FileFailed: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Load confusables dataFileFailed: {e}")
            return {}
    
    def is_confusable_character(self, unicode_point: str) -> bool:
        """Check指定的Unicode码点是否是混淆字符"""
        return unicode_point in self.confusable_unicode_points
    
    def is_confusable_char(self, character: str) -> bool:
        """Check指定的字符是否是混淆字符"""
        return character in self.confusable_characters
    
    def get_confusable_info(self, unicode_point: str) -> Dict[str, Any]:
        """获取指定Unicode码点的混淆信息"""
        if not self.confusables_data:
            return {}

        # 尝试从不同的数据结构中获取confusables映射
        confusables_map = self.confusables_data.get("confusables_map", {})

        # 如果没有找到confusables_map，尝试latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        return confusables_map.get(unicode_point, {})
    
    def get_confusables_count(self) -> int:
        """获取混淆字符总数"""
        return len(self.confusable_unicode_points)
    
    def get_confusables_metadata(self) -> Dict[str, Any]:
        """获取confusables数据的元数据"""
        if not self.confusables_data:
            return {}
        
        return self.confusables_data.get("metadata", {})
    
    def validate_confusables_data(self) -> Dict[str, Any]:
        """验证confusables数据的完整性"""
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        if not self.confusables_data:
            validation_result["errors"].append("Confusables数据为空")
            return validation_result
        
        # Check必要字段
        confusables_map = self.confusables_data.get("confusables_map", {})

        # 如果没有找到confusables_map，尝试latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        if not confusables_map:
            validation_result["errors"].append("缺少confusables_map或latin_related_confusables字段")
            return validation_result
        
        # Statistics
        validation_result["statistics"] = {
            "total_confusables": len(confusables_map),
            "confusable_types": {}
        }
        
        # 验证每个entries目
        valid_entries = 0
        for unicode_point, char_data in confusables_map.items():
            try:
                # Check必要字段
                required_fields = ["character", "confusable_with"]
                for field in required_fields:
                    if field not in char_data:
                        validation_result["warnings"].append(f"entries目 {unicode_point} 缺少字段: {field}")
                        continue
                
                # 统计类型
                conf_type = char_data.get("confusable_type", "unknown")
                validation_result["statistics"]["confusable_types"][conf_type] = \
                    validation_result["statistics"]["confusable_types"].get(conf_type, 0) + 1
                
                valid_entries += 1
                
            except Exception as e:
                validation_result["warnings"].append(f"验证entries目 {unicode_point} 时出错: {e}")
        
        validation_result["statistics"]["valid_entries"] = valid_entries
        
        # 判断是否有效
        if not validation_result["errors"] and valid_entries > 0:
            validation_result["is_valid"] = True
        
        return validation_result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取confusables数据Statistics"""
        if not self.confusables_data:
            return {"total_confusables": 0, "config_status": "not_loaded"}
        
        # 尝试从不同的数据结构中获取confusables映射
        confusables_map = self.confusables_data.get("confusables_map", {})

        # 如果没有找到confusables_map，尝试latin_related_confusables
        if not confusables_map:
            confusables_map = self.confusables_data.get("latin_related_confusables", {})

        # 统计类型分布
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
    print("=== Homoglyph Character配置测试 ===\n")
    
    # 创建配置管理器
    config = HomographConfig()
    
    # 验证配置
    validation = config.validate_confusables_data()
    print(f"配置验证: {'通过' if validation['is_valid'] else 'Failed'}")
    if validation['errors']:
        print(f"Error: {validation['errors']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings'][:3]}...")  # 只显示前3个Warning
    
    # 获取Statistics
    stats = config.get_statistics()
    print(f"\nStatistics:")
    print(f"  混淆字符数: {stats['total_confusables']}")
    print(f"  配置状态: {stats['config_status']}")
    
    # 测试字符检测
    test_chars = [
        ("U+0430", "а"),  # 西里尔字母 a
        ("U+0061", "a"),  # 拉丁字母 a
        ("U+043E", "о"),  # 西里尔字母 o
        ("U+006F", "o"),  # 拉丁字母 o
    ]
    
    print(f"\n字符检测测试:")
    for unicode_point, char in test_chars:
        is_confusable = config.is_confusable_character(unicode_point)
        print(f"  '{char}' ({unicode_point}): {'是混淆字符' if is_confusable else '不是混淆字符'}")
        
        if is_confusable:
            info = config.get_confusable_info(unicode_point)
            confusable_with = info.get("confusable_with", {})
            target_char = confusable_with.get("character", "?")
            target_point = confusable_with.get("unicode_point", "?")
            print(f"    混淆于: '{target_char}' ({target_point})")


if __name__ == "__main__":
    main()
