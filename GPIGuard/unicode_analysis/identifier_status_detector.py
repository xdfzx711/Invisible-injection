#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
标识符状态检测器
基于 Unicode IdentifierStatus 标准的简化检测系统
"""

import json
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os

# 添加项目根directory到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目工具
from data_collection.utils.logger import setup_logger

# 修复相对导入问题
try:
    from .identifier_status_config import IdentifierStatusConfig
except ImportError:
    from identifier_status_config import IdentifierStatusConfig


class IdentifierStatusDetector:
    """标识符状态检测器"""

    def __init__(self, config: IdentifierStatusConfig, output_dir: Union[str, Path] = "testscan_data/unicode_analysis", data_sources: List[str] = None):
        self.config = config
        self.base_output_dir = Path(output_dir)
        self.data_sources = data_sources or ['general']

        # 为每个数据源创建Output directory
        self.output_dirs = {}
        for source in self.data_sources:
            source_output_dir = self.base_output_dir / f"threat_detection_{source}"
            source_output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dirs[source] = source_output_dir

        # 默认Output directory（用于向后兼容）
        self.output_dir = self.base_output_dir
        
        # 设置日志
        self.logger = setup_logger('IdentifierStatusDetector', 'identifier_status_detector.log')
        
        # 检测统计
        self.detection_stats = {
            "total_characters_checked": 0,
            "restricted_characters_found": 0,
            "allowed_characters_found": 0,
            "normalization_issues_found": 0,
            "detection_time": 0.0
        }
    
    def detect_restrictions_in_characters(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测字符列表中的受限字符"""
        if not all_characters:
            self.logger.warning("没有字符需要检测")
            return []
        
        self.logger.info(f"开始检测 {len(all_characters)} 个字符的标识符状态")
        start_time = time.time()
        
        # 重置统计
        self.detection_stats = {
            "total_characters_checked": 0,
            "restricted_characters_found": 0,
            "allowed_characters_found": 0,
            "normalization_issues_found": 0,
            "detection_time": 0.0
        }
        
        detections = []
        
        # 检测标识符状态
        if self.config.is_detection_enabled("identifier_status"):
            detections.extend(self._detect_identifier_status(all_characters))
        
        # 检测规范化问题（保留现有功能）
        if self.config.is_detection_enabled("normalization"):
            normalization_detections = self._detect_normalization_issues(all_characters)
            detections.extend(normalization_detections)
            self.detection_stats["normalization_issues_found"] = len(normalization_detections)
        
        end_time = time.time()
        self.detection_stats["detection_time"] = end_time - start_time
        
        self.logger.info(f"检测Completed，发现 {len(detections)} 个问题字符")
        self.logger.info(f"  - 受限字符: {self.detection_stats['restricted_characters_found']}")
        self.logger.info(f"  - 规范化问题: {self.detection_stats['normalization_issues_found']}")
        
        # 保存检测结果
        self._save_detection_results(detections)
        
        return detections
    
    def _detect_identifier_status(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测标识符状态"""
        detections = []
        
        for char_info in all_characters:
            char = char_info.get("character", "")
            if not char:
                continue
            
            self.detection_stats["total_characters_checked"] += 1
            
            # Check字符是否受限
            if self.config.is_character_restricted(char):
                detection = self._create_restriction_detection(char_info)
                detections.append(detection)
                self.detection_stats["restricted_characters_found"] += 1
            else:
                self.detection_stats["allowed_characters_found"] += 1
        
        return detections
    
    def _create_restriction_detection(self, char_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建受限字符检测记录"""
        char = char_info.get("character", "")
        unicode_point = char_info.get("unicode_point", f"U+{ord(char):04X}")
        source_info = char_info.get("source_info", {})
        
        # 获取字符的基本信息
        try:
            char_name = unicodedata.name(char, f"UNNAMED-{unicode_point}")
            char_category = unicodedata.category(char)
        except ValueError:
            char_name = f"UNNAMED-{unicode_point}"
            char_category = "Cn"
        
        # 创建简化的检测记录
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
        """检测规范化问题（保留现有功能的简化版）"""
        normalization_detections = []
        processed_strings = set()
        
        for char_info in all_characters:
            normalization_info = char_info.get("normalization_info", {})
            
            if not normalization_info:
                continue
            
            # 避免重复处理相同的字符串
            original_string = normalization_info.get("original_string", "")
            if original_string in processed_strings:
                continue
            processed_strings.add(original_string)
            
            # Check是否有规范化变化
            if normalization_info.get("has_normalization_changes", False):
                detection = self._create_normalization_detection(char_info, normalization_info)
                if detection:
                    normalization_detections.append(detection)
        
        return normalization_detections
    
    def _create_normalization_detection(self, char_info: Dict[str, Any], normalization_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建规范化问题检测记录"""
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
        """保存检测结果"""
        if not detections:
            self.logger.info("没有检测结果需要保存")
            return

        # 按数据源和检测类型分组保存
        source_detection_groups = {}
        for detection in detections:
            # 获取数据源信息
            source_type = detection.get("source_info", {}).get("source_type", "general")
            detection_type = detection.get("detection_info", {}).get("detection_type", "unknown")

            if source_type not in source_detection_groups:
                source_detection_groups[source_type] = {}
            if detection_type not in source_detection_groups[source_type]:
                source_detection_groups[source_type][detection_type] = []

            source_detection_groups[source_type][detection_type].append(detection)

        # 为每个数据源保存检测结果
        # 注意：identifier_status 模式的详细检测Filehas been废弃，使用 threat_based 模式的 formatted_threats File
        self.logger.info(f"检测Completed，共 {len(detections)} entries记录（使用新格式威胁报告）")
        
        # 旧的File保存逻辑has been注释（has been废弃 identifier_status_detections 和 identifier_status_detection_summary File）
        # for source_type, detection_groups in source_detection_groups.items():
        #     output_dir = self.output_dirs.get(source_type, self.output_dir)
        #     for detection_type, group_detections in detection_groups.items():
        #         output_file = output_dir / f"identifier_status_detections_{detection_type}.json"
        #         # ... (保存逻辑has been移除)
        #     source_summary_file = output_dir / "identifier_status_detection_summary.json"
        #     # ... (保存逻辑has been移除)
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """获取检测Statistics"""
        return self.detection_stats.copy()


def main():
    """Test function"""
    print("=== 标识符状态检测器测试 ===\n")
    
    # 创建配置和检测器
    config = IdentifierStatusConfig()
    detector = IdentifierStatusDetector(config)
    
    # 模拟字符数据
    test_characters = [
        {
            "character": "a",
            "unicode_point": "U+0061",
            "position_in_string": 0,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        },
        {
            "character": "а",  # 西里尔字母 a
            "unicode_point": "U+0430",
            "position_in_string": 1,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        },
        {
            "character": "🙂",  # 表情符号
            "unicode_point": "U+1F642",
            "position_in_string": 2,
            "source_info": {"string_value": "test", "file_name": "test.txt"}
        }
    ]
    
    # 执行检测
    detections = detector.detect_restrictions_in_characters(test_characters)
    
    # 显示结果
    print(f"检测Completed，发现 {len(detections)} 个问题")
    for detection in detections:
        char = detection.get("character", "")
        status = detection.get("status", "")
        detection_type = detection.get("detection_info", {}).get("detection_type", "")
        print(f"  '{char}' ({detection.get('unicode_point', '')}): {status} ({detection_type})")
    
    # 显示统计
    stats = detector.get_detection_statistics()
    print(f"\nStatistics:")
    print(f"  检测字符总数: {stats['total_characters_checked']}")
    print(f"  受限字符数: {stats['restricted_characters_found']}")
    print(f"  允许字符数: {stats['allowed_characters_found']}")
    print(f"  检测耗时: {stats['detection_time']:.3f}秒")


if __name__ == "__main__":
    main()
