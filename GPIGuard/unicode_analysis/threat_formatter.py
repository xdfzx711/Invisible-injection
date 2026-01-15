#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unicode威胁报告格式化器
生成新格式的威胁检测报告
"""

from typing import Dict, List, Any, Tuple
import json
from pathlib import Path
from datetime import datetime


class ThreatFormatter:
    """威胁报告格式化器"""
    
    def __init__(self):
        pass
    
    def remove_threat_characters(self, text: str, threat_chars: List[str]) -> str:
        """
        移除威胁字符，生成清理后的版本
        
        Args:
            text: 原始文本
            threat_chars: 威胁字符列表
        
        Returns:
            清理后的文本
        """
        clean_text = text
        for char in threat_chars:
            clean_text = clean_text.replace(char, '')
        return clean_text
    
    def format_detection_entry(self, 
                               unicode_type_id: int, 
                               original_text: str, 
                               adversarial_text: str) -> str:
        """
        格式化单entries检测记录
        
        Args:
            unicode_type_id: Unicode类型ID (0-4)
            original_text: 清理后的原始指令
            adversarial_text: 包含威胁字符的对抗性指令
        
        Returns:
            格式化的字符串
        """
        return (f"Unicode type ID: {unicode_type_id}\n"
                f"Original instruction: {original_text}\n"
                f"Adversarial instruction: {adversarial_text}")
    
    def group_detections_by_string(self, detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        将检测结果按源字符串分组
        
        Args:
            detections: 字符级别的检测列表
        
        Returns:
            按字符串分组的检测字典
        """
        grouped = {}
        
        for detection in detections:
            source_info = detection.get("source_info", {})
            string_value = source_info.get("string_value", "")
            
            if not string_value:
                continue
            
            # 使用字符串内容作为键
            if string_value not in grouped:
                grouped[string_value] = []
            
            grouped[string_value].append(detection)
        
        return grouped
    
    def generate_threat_reports(self, 
                                detections: List[Dict[str, Any]], 
                                classifier) -> List[Dict[str, Any]]:
        """
        生成威胁报告（字符串级别）
        
        Args:
            detections: 字符级别的检测列表
            classifier: Unicode类型分类器
        
        Returns:
            List of formatted threat reports
        """
        # 按字符串分组
        grouped_detections = self.group_detections_by_string(detections)
        
        reports = []
        
        for adversarial_text, char_detections in grouped_detections.items():
            # 提取威胁字符
            threat_chars = [d.get("character", "") for d in char_detections]
            
            # 分类威胁类型
            unicode_type_id = classifier.classify_string_threats(adversarial_text, char_detections)
            
            if unicode_type_id is None:
                continue
            
            # 生成清理版本
            original_text = self.remove_threat_characters(adversarial_text, threat_chars)
            
            # 创建报告entries目
            report = {
                "unicode_type_id": unicode_type_id,
                "unicode_type_name": classifier.get_type_name(unicode_type_id),
                "original_instruction": original_text,
                "adversarial_instruction": adversarial_text,
                "threat_characters": [
                    {
                        "character": d.get("character", ""),
                        "unicode_point": d.get("unicode_point", ""),
                        "name": d.get("name", ""),
                        "position": d.get("position_in_string", 0)
                    }
                    for d in char_detections
                ],
                "source_info": char_detections[0].get("source_info", {}),
                "formatted_output": self.format_detection_entry(
                    unicode_type_id, 
                    original_text, 
                    adversarial_text
                )
            }
            
            reports.append(report)
        
        return reports
    
    def save_formatted_reports(self, 
                              reports: List[Dict[str, Any]], 
                              output_file: Path,
                              include_metadata: bool = True):
        """
        保存格式化报告
        
        Args:
            reports: 威胁报告列表
            output_file: 输出File路径
            include_metadata: 是否包含元数据
        """
        # 按类型ID分组
        reports_by_type = {}
        for report in reports:
            type_id = report["unicode_type_id"]
            if type_id not in reports_by_type:
                reports_by_type[type_id] = []
            reports_by_type[type_id].append(report)
        
        # 构建输出数据
        output_data = {
            "metadata": {
                "total_threats": len(reports),
                "threats_by_type": {
                    str(type_id): len(type_reports) 
                    for type_id, type_reports in reports_by_type.items()
                },
                "generation_time": datetime.now().isoformat(),
                "format_version": "2.0"
            } if include_metadata else {},
            "threats": reports
        }
        
        # 保存JSON格式
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 威胁报告has been保存: {output_file}")
        except Exception as e:
            print(f"❌ 保存报告Failed: {e}")
    
    def save_formatted_text_reports(self, 
                                   reports: List[Dict[str, Any]], 
                                   output_file: Path):
        """
        保存纯文本格式的报告（每entries一行）
        
        Args:
            reports: 威胁报告列表
            output_file: 输出File路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for report in reports:
                    # 写入格式化的输出（替换\n为实际换行）
                    formatted = report["formatted_output"]
                    f.write(formatted + "\n\n")  # 每entries记录之间空一行
            
            print(f"✅ 文本格式报告has been保存: {output_file}")
        except Exception as e:
            print(f"❌ 保存文本报告Failed: {e}")
    
    def generate_summary_statistics(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成统计摘要
        
        Args:
            reports: 威胁报告列表
        
        Returns:
            统计摘要字典
        """
        stats = {
            "total_threats": len(reports),
            "by_type": {},
            "top_threat_sources": []
        }
        
        # 按类型统计
        type_counts = {}
        for report in reports:
            type_id = report["unicode_type_id"]
            type_name = report["unicode_type_name"]
            
            if type_id not in type_counts:
                type_counts[type_id] = {
                    "name": type_name,
                    "count": 0
                }
            type_counts[type_id]["count"] += 1
        
        stats["by_type"] = type_counts
        
        # 统计威胁来源
        source_counts = {}
        for report in reports:
            source_file = report["source_info"].get("file_name", "unknown")
            source_counts[source_file] = source_counts.get(source_file, 0) + 1
        
        # 获取前10个威胁最多的来源
        stats["top_threat_sources"] = sorted(
            source_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return stats


# 测试代码
if __name__ == "__main__":
    formatter = ThreatFormatter()
    
    # 测试清理功能
    adversarial = "Please visit https://goo​gle.com"  # 包含零宽字符
    threat_chars = ["​"]  # U+200B
    original = formatter.remove_threat_characters(adversarial, threat_chars)
    
    print("清理测试:")
    print(f"对抗性文本: {repr(adversarial)}")
    print(f"清理后: {repr(original)}")
    
    # 测试格式化
    formatted = formatter.format_detection_entry(1, original, adversarial)
    print(f"\n格式化输出:\n{formatted}")

