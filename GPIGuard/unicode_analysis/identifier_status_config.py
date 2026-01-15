#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
标识符状态配置管理器
基于 Unicode IdentifierStatus 标准的简化配置系统
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Set
import sys
import os

# 添加项目根directory到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目工具
from data_collection.utils.logger import setup_logger


class IdentifierStatusConfig:
    """标识符状态配置管理器"""
    
    def __init__(self, lookup_file: Union[str, Path] = None):
        # 设置默认查找表File路径
        if lookup_file is None:
            # 从当前File位置向上找到testscandirectory
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            lookup_file = testscan_dir / "testscan_data" / "unicode_analysis" / "identifier_status_lookup.json"

        self.lookup_file = Path(lookup_file)
        self.logger = setup_logger('IdentifierStatusConfig', 'identifier_status_config.log')
        
        # 加载查找表
        self.allowed_characters = self._load_lookup_table()
        
        # 检测设置（简化版）
        self.detection_settings = {
            "enable_identifier_status_detection": True,
            "enable_normalization_detection": True,  # 保留规范化检测
            "output_format": "simple"  # simple 或 detailed
        }
        
        self.logger.info(f"标识符状态配置has been加载，包含 {len(self.allowed_characters)} 个允许字符")
    
    def _load_lookup_table(self) -> Set[str]:
        """加载标识符状态查找表"""
        try:
            if not self.lookup_file.exists():
                self.logger.error(f"查找表File不exists: {self.lookup_file}")
                return set()
            
            with open(self.lookup_file, 'r', encoding='utf-8') as f:
                lookup_data = json.load(f)
            
            # 将查找表转换为集合以提高查询性能
            # lookup_data 格式: {"U+0041": "Allowed", "U+0042": "Allowed", ...}
            allowed_chars = set()
            for unicode_point, status in lookup_data.items():
                if status == "Allowed":
                    allowed_chars.add(unicode_point)
            
            self.logger.info(f"成功加载查找表: {self.lookup_file}")
            return allowed_chars
            
        except Exception as e:
            self.logger.error(f"加载查找表Failed: {e}")
            return set()
    
    def is_character_allowed(self, char: str) -> bool:
        """Check字符是否被允许使用"""
        if not char:
            return False
        
        unicode_point = f"U+{ord(char):04X}"
        return unicode_point in self.allowed_characters
    
    def is_character_restricted(self, char: str) -> bool:
        """Check字符是否被限制使用"""
        return not self.is_character_allowed(char)
    
    def get_character_status(self, char: str) -> str:
        """获取字符状态"""
        if self.is_character_allowed(char):
            return "Allowed"
        else:
            return "Restricted"
    
    def analyze_string_status(self, text: str) -> Dict[str, Any]:
        """分析字符串中每个字符的状态"""
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
        """获取检测设置"""
        return self.detection_settings.copy()
    
    def is_detection_enabled(self, detection_type: str = "identifier_status") -> bool:
        """Check某种检测是否启用"""
        setting_key = f"enable_{detection_type}_detection"
        return self.detection_settings.get(setting_key, True)
    
    def update_detection_setting(self, detection_type: str, enabled: bool):
        """更新检测设置"""
        setting_key = f"enable_{detection_type}_detection"
        self.detection_settings[setting_key] = enabled
        self.logger.info(f"检测设置has been更新: {setting_key} = {enabled}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取配置Statistics"""
        return {
            "total_allowed_characters": len(self.allowed_characters),
            "lookup_file": str(self.lookup_file),
            "detection_settings": self.detection_settings,
            "config_status": "loaded" if self.allowed_characters else "error"
        }
    
    def reload_lookup_table(self) -> bool:
        """重新加载查找表"""
        try:
            self.allowed_characters = self._load_lookup_table()
            self.logger.info("查找表重新加载成功")
            return True
        except Exception as e:
            self.logger.error(f"重新加载查找表Failed: {e}")
            return False
    
    def validate_lookup_table(self) -> Dict[str, Any]:
        """验证查找表的完整性"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            # CheckFile是否exists
            if not self.lookup_file.exists():
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"查找表File不exists: {self.lookup_file}")
                return validation_result
            
            # Check是否有数据
            if not self.allowed_characters:
                validation_result["is_valid"] = False
                validation_result["errors"].append("查找表为空")
                return validation_result
            
            # Statistics
            validation_result["statistics"] = {
                "total_allowed_chars": len(self.allowed_characters),
                "file_size": self.lookup_file.stat().st_size,
                "sample_chars": list(self.allowed_characters)[:10]  # 前10个字符作为样本
            }
            
            # Check基本字符是否exists
            basic_chars = ["U+0041", "U+0061", "U+0030"]  # A, a, 0
            missing_basic = []
            for char_code in basic_chars:
                if char_code not in self.allowed_characters:
                    missing_basic.append(char_code)
            
            if missing_basic:
                validation_result["warnings"].append(f"缺少基本字符: {missing_basic}")
            
            self.logger.info("查找表验证Completed")
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"验证过程出错: {e}")
        
        return validation_result


def main():
    """Test function"""
    print("=== 标识符状态配置测试 ===\n")
    
    # 创建配置管理器
    config = IdentifierStatusConfig()
    
    # 验证配置
    validation = config.validate_lookup_table()
    print(f"配置验证: {'通过' if validation['is_valid'] else 'Failed'}")
    if validation['errors']:
        print(f"Error: {validation['errors']}")
    if validation['warnings']:
        print(f"Warning: {validation['warnings']}")
    
    # 获取Statistics
    stats = config.get_statistics()
    print(f"\nStatistics:")
    print(f"  允许字符数: {stats['total_allowed_characters']}")
    print(f"  配置状态: {stats['config_status']}")
    
    # 测试字符检测
    test_chars = ["a", "A", "1", "中", "α", "а", "🙂", "_", "-", "."]
    print(f"\n字符状态测试:")
    for char in test_chars:
        status = config.get_character_status(char)
        unicode_point = f"U+{ord(char):04X}"
        print(f"  '{char}' ({unicode_point}): {status}")
    
    # 测试字符串分析
    test_strings = ["hello_world", "test123", "café", "测试文本", "hello-world"]
    print(f"\n字符串分析测试:")
    for text in test_strings:
        analysis = config.analyze_string_status(text)
        print(f"  '{text}': {analysis['allowed_chars']}/{analysis['total_chars']} 允许 "
              f"({analysis['allowed_percentage']:.1f}%) "
              f"{'有限制字符' if analysis['has_restricted_chars'] else '全部允许'}")


if __name__ == "__main__":
    main()
