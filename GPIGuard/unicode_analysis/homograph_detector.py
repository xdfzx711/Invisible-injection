#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Homoglyph Character检测器
检测字符列表中的Homoglyph Character（混淆字符）
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import unicodedata

# 导入相关模块
sys.path.append(str(Path(__file__).parent.parent))
from data_collection.utils.logger import setup_logger

# 修复相对导入问题
try:
    from .homograph_config import HomographConfig
except ImportError:
    from homograph_config import HomographConfig


class HomographDetector:
    """Homoglyph Character检测器"""

    def __init__(self, config: HomographConfig, output_dir: Union[str, Path] = "testscan_data/unicode_analysis", data_sources: List[str] = None):
        self.config = config
        self.base_output_dir = Path(output_dir)
        self.data_sources = data_sources or ['general']

        # 为每个数据源创建Output directory
        self.output_dirs = {}
        for source in self.data_sources:
            source_output_dir = self.base_output_dir / f"threat_detection_{source}"
            source_output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dirs[source] = source_output_dir

        # 设置日志
        self.logger = setup_logger('HomographDetector', 'homograph_detector.log')
        
        # 检测统计
        self.detection_stats = {
            "total_characters_checked": 0,
            "homograph_characters_found": 0,
            "detection_time": 0.0
        }
        
        self.logger.info(f"Homoglyph Character检测器has been初始化，数据源: {', '.join(self.data_sources)}")
        self.logger.info(f"可检测 {self.config.get_confusables_count()} 个混淆字符")
    
    def detect_homographs_in_characters(self, all_characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测字符列表中的Homoglyph Character"""
        if not all_characters:
            self.logger.warning("没有字符需要检测")
            return []
        
        self.logger.info(f"开始检测 {len(all_characters)} 个字符的Homoglyph Character")
        start_time = time.time()
        
        # 重置统计
        self.detection_stats = {
            "total_characters_checked": 0,
            "homograph_characters_found": 0,
            "detection_time": 0.0
        }
        
        # 按数据源分组字符
        characters_by_source = self._group_characters_by_source(all_characters)
        
        all_detections = []
        
        # 为每个数据源单独检测和保存
        for source_type, source_characters in characters_by_source.items():
            self.logger.info(f"检测 {source_type} 数据源的 {len(source_characters)} 个字符")
            
            source_detections = self._detect_homographs_for_source(source_type, source_characters)
            
            if source_detections:
                # 保存到对应的数据源directory
                self._save_homograph_detections(source_type, source_detections)
                all_detections.extend(source_detections)
                
                self.logger.info(f"{source_type} 数据源发现 {len(source_detections)} 个Homoglyph Character")
            else:
                self.logger.info(f"{source_type} 数据源未发现Homoglyph Character")
        
        # 更新统计
        end_time = time.time()
        self.detection_stats["detection_time"] = end_time - start_time
        
        self.logger.info(f"Homoglyph Character检测Completed，共发现 {len(all_detections)} 个混淆字符")
        self.logger.info(f"检测耗时: {self.detection_stats['detection_time']:.3f}秒")
        
        return all_detections
    
    def _group_characters_by_source(self, all_characters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按数据源分组字符"""
        characters_by_source = {}
        
        for char_info in all_characters:
            # 从source_info中获取数据源类型
            source_info = char_info.get("source_info", {})
            source_type = source_info.get("source_type", "unknown")
            
            # 如果source_type不在配置的数据源中，尝试从File路径推断
            if source_type == "unknown" or source_type not in self.data_sources:
                source_type = self._infer_source_type(char_info)
            
            if source_type not in characters_by_source:
                characters_by_source[source_type] = []
            
            characters_by_source[source_type].append(char_info)
        
        return characters_by_source
    
    def _infer_source_type(self, char_info: Dict[str, Any]) -> str:
        """从字符信息推断数据源类型"""
        source_info = char_info.get("source_info", {})
        
        # 尝试从File路径推断
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
        
        # 默认返回第一个配置的数据源
        return self.data_sources[0] if self.data_sources else "general"
    
    def _detect_homographs_for_source(self, source_type: str, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为特定数据源检测Homoglyph Character"""
        detections = []
        
        for char_info in characters:
            self.detection_stats["total_characters_checked"] += 1
            
            unicode_point = char_info.get("unicode_point", "")
            character = char_info.get("character", "")

            # 跳过标点、符号等
            if character:
                category = unicodedata.category(character[0])
                if not (category.startswith('L') or category.startswith('N')):
                    continue

                # 新增：跳过标准数字 0-9
                if '0' <= character <= '9':
                    continue
            
            # 只检测在 confusables_map 中的字符（混淆字符）
            if self.config.is_confusable_character(unicode_point):
                confusable_info = self.config.get_confusable_info(unicode_point)
                
                if confusable_info:
                    detection = self._create_homograph_detection(char_info, confusable_info)
                    detections.append(detection)
                    self.detection_stats["homograph_characters_found"] += 1
        
        return detections
    
    def _create_homograph_detection(self, char_info: Dict[str, Any], confusable_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建Homoglyph Character检测记录"""
        return {
            "detection_id": f"homograph_{uuid.uuid4().hex[:8]}",
            "detection_type": "homograph_character",
            "character": char_info["character"],
            "unicode_point": char_info["unicode_point"],

            # 混淆信息
            "confusable_with": confusable_info.get("confusable_with", {}),
            "confusable_type": confusable_info.get("confusable_type", "unknown"),
            "description": confusable_info.get("description", ""),

            # 源信息
            "source_info": {
                **char_info.get("source_info", {}),
                "position_in_string": char_info.get("position_in_string")
            },
            # 去掉 context 字段以简化报告结构

            # 检测元数据
            "detection_time": datetime.now().isoformat(),
            "detector_version": "1.0.0"
        }
    
    def _save_homograph_detections(self, source_type: str, detections: List[Dict[str, Any]]):
        """保存Homoglyph character detection results到对应数据源directory"""
        output_dir = self.output_dirs.get(source_type)
        if not output_dir:
            self.logger.warning(f"未找到数据源 {source_type} 的Output directory")
            return
        
        # 保存详细检测结果
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
            
            self.logger.info(f"Homoglyph character detection resultshas been保存: {detections_file}")
            
        except Exception as e:
            self.logger.error(f"保存Homoglyph character detection resultsFailed: {e}")
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """获取检测Statistics"""
        return self.detection_stats.copy()


def main():
    """Test function"""
    print("=== Homoglyph Character检测器测试 ===\n")
    
    # 创建配置和检测器
    config = HomographConfig()
    detector = HomographDetector(config, "testscan_data/unicode_analysis", ["test"])
    
    # 创建测试字符数据
    test_characters = [
        {
            "character": "а",  # 西里尔字母 a
            "unicode_point": "U+0430",
            "source_info": {"source_type": "test", "file_path": "test.txt"},
            "context": {"string_value": "test", "position": 0}
        },
        {
            "character": "a",  # 拉丁字母 a
            "unicode_point": "U+0061",
            "source_info": {"source_type": "test", "file_path": "test.txt"},
            "context": {"string_value": "test", "position": 1}
        }
    ]
    
    # 执行检测
    detections = detector.detect_homographs_in_characters(test_characters)
    
    # 显示结果
    print(f"检测Completed，发现 {len(detections)} 个Homoglyph Character")
    for detection in detections:
        char = detection.get("character", "")
        unicode_point = detection.get("unicode_point", "")
        confusable_with = detection.get("confusable_with", {})
        target_char = confusable_with.get("character", "?")
        target_point = confusable_with.get("unicode_point", "?")
        
        print(f"  '{char}' ({unicode_point}) 混淆于 '{target_char}' ({target_point})")
    
    # 显示统计
    stats = detector.get_detection_statistics()
    print(f"\nStatistics:")
    print(f"  检测字符总数: {stats['total_characters_checked']}")
    print(f"  发现混淆字符数: {stats['homograph_characters_found']}")
    print(f"  检测耗时: {stats['detection_time']:.3f}秒")


if __name__ == "__main__":
    main()
