#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Homoglyph Character对比报告生成器
"""

import json
from pathlib import Path
from typing import Dict, List, Any

class ComparisonReportGenerator:
    """生成对抗性指令和原始指令的对比报告"""

    def generate_reports(
        self, 
        all_characters: List[Dict[str, Any]], 
        homograph_detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """为包含Homoglyph Character的每个文本片段生成报告"""
        if not homograph_detections:
            return []

        # 1. 按原始文本对检测结果进行分组
        detections_by_text = self._group_detections_by_text(homograph_detections)

        reports = []
        # 2. 为每个文本片段生成报告
        for original_text, detections in detections_by_text.items():
            report = self._generate_single_report(original_text, detections)
            if report:
                reports.append(report)
        
        return reports

    def _group_detections_by_text(self, homograph_detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将检测结果按其来源的完整字符串进行分组"""
        grouped = {}
        for detection in homograph_detections:
            # 从 source_info 获取原始字符串
            original_text = detection.get("source_info", {}).get("string_value")
            if not original_text:
                continue

            if original_text not in grouped:
                grouped[original_text] = []
            
            grouped[original_text].append(detection)
        return grouped

    def _generate_single_report(self, adversarial_instruction: str, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """为一个文本片段生成单个JSON报告"""
        # 1. 创建可修改的字符列表作为基础
        char_list = list(adversarial_instruction)

        # 2. 按位置倒序排序检测结果，以安全地进行替换
        # position_in_string 字段现在至关重要
        detections.sort(key=lambda d: d.get("source_info", {}).get("position_in_string", -1), reverse=True)

        # 3. 获取数据源类型（从第一个检测记录中获取，因为同一文本的所有检测应该来自同一数据源）
        source_type = "unknown"
        if detections:
            source_type = detections[0].get("source_info", {}).get("source_type", "unknown")

        # 4. 执行倒序替换
        for detection in detections:
            source_info = detection.get("source_info", {})
            position = source_info.get("position_in_string")
            if position is None or position < 0 or position >= len(char_list):
                continue # 位置信息无效，跳过

            # 获取要替换成的拉丁字符
            replacement_char = detection.get("confusable_with", {}).get("character")
            if not replacement_char:
                continue # 替换字符无效，跳过

            # 执行替换
            char_list[position] = replacement_char
        
        original_instruction = "".join(char_list)

        # 5. 组装成最终的报告格式（包含数据源信息）
        report = {
            "instruction": "Compare the adversarial instruction with unicode characters and the original instruction, and determine whether the added unicode characters changed the semantics of the sentence",
            "input": f"Original instruction: {original_instruction}\nAdversarial instruction: {adversarial_instruction}",
            "output": "False",
            "source_type": source_type  # 添加数据源类型信息
        }
        return report

    def save_reports(self, reports: List[Dict[str, Any]], output_file: str):
        """将生成的报告列表保存到JSONFile"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, ensure_ascii=False, indent=2)
            print(f"对比报告has been成功保存到: {output_file}")
        except Exception as e:
            print(f"Error：保存对比报告Failed: {e}")
    
    def save_reports_by_source(self, reports: List[Dict[str, Any]], base_output_dir: Path):
        """
        按数据源类型分组保存对比报告
        
        Args:
            reports: 报告列表，每个报告应包含 source_type 字段（用于分组，保存时会移除）
            base_output_dir: 基础Output directory（例如 testscan_data）
        """
        # 按数据源类型分组报告
        reports_by_source = {}
        for report in reports:
            source_type = report.get("source_type", "unknown")
            if source_type not in reports_by_source:
                reports_by_source[source_type] = []
            # 创建一个副本，移除 source_type 字段（因为最终报告格式不需要此字段）
            report_copy = {k: v for k, v in report.items() if k != "source_type"}
            reports_by_source[source_type].append(report_copy)
        
        # 为每个数据源保存报告
        for source_type, source_reports in reports_by_source.items():
            # 创建数据源特定的directory
            output_dir = base_output_dir / f"threat_detection_{source_type}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存到对应的directory
            output_file = output_dir / "comparison_reports.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(source_reports, f, ensure_ascii=False, indent=2)
                print(f"对比报告has been保存: {output_file} ({len(source_reports)} entries记录)")
            except Exception as e:
                print(f"Error: 保存对比报告Failed到 {output_file}: {e}")

