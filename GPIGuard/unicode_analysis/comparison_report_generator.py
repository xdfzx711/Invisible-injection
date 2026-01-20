#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Homoglyph Character Comparison Report Generator
"""

import json
from pathlib import Path
from typing import Dict, List, Any

class ComparisonReportGenerator:
    """Generate comparison reports between adversarial instructions and original instructions"""

    def generate_reports(
        self, 
        all_characters: List[Dict[str, Any]], 
        homograph_detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate reports for each text segment containing Homoglyph Characters"""
        if not homograph_detections:
            return []

        # 1. Group detection results by their source text
        detections_by_text = self._group_detections_by_text(homograph_detections)

        reports = []
        # 2. Generate reports for each text segment
        for original_text, detections in detections_by_text.items():
            report = self._generate_single_report(original_text, detections)
            if report:
                reports.append(report)
        
        return reports

    def _group_detections_by_text(self, homograph_detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group detection results by their source complete string"""
        grouped = {}
        for detection in homograph_detections:
            # Get the original string from source_info
            original_text = detection.get("source_info", {}).get("string_value")
            if not original_text:
                continue

            if original_text not in grouped:
                grouped[original_text] = []
            
            grouped[original_text].append(detection)
        return grouped

    def _generate_single_report(self, adversarial_instruction: str, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a single JSON report for a text segment"""
        # 1. Create a modifiable character list as the base
        char_list = list(adversarial_instruction)

        # 2. Sort detection results in reverse order by position for safe replacement
        # The position_in_string field is now critical
        detections.sort(key=lambda d: d.get("source_info", {}).get("position_in_string", -1), reverse=True)

        # 3. Get the data source type (from the first detection record, since all detections from the same text should come from the same data source)
        source_type = "unknown"
        if detections:
            source_type = detections[0].get("source_info", {}).get("source_type", "unknown")

        # 4. Perform reverse replacement
        for detection in detections:
            source_info = detection.get("source_info", {})
            position = source_info.get("position_in_string")
            if position is None or position < 0 or position >= len(char_list):
                continue # Invalid position, skip

            # Get the Latin character to replace with
            replacement_char = detection.get("confusable_with", {}).get("character")
            if not replacement_char:
                continue # Invalid replacement character, skip

            # Perform replacement
            char_list[position] = replacement_char
        
        original_instruction = "".join(char_list)

        # 5. Assemble into final report format (includes data source information)
        report = {
            "instruction": "Compare the adversarial instruction with unicode characters and the original instruction, and determine whether the added unicode characters changed the semantics of the sentence",
            "input": f"Original instruction: {original_instruction}\nAdversarial instruction: {adversarial_instruction}",
            "output": "False",
            "source_type": source_type  # Add data source type information
        }
        return report

    def save_reports(self, reports: List[Dict[str, Any]], output_file: str):
        """Save the generated report list to a JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, ensure_ascii=False, indent=2)
            print(f"Comparison reports have been successfully saved to: {output_file}")
        except Exception as e:
            print(f"Error: Failed to save comparison reports: {e}")
    
    def save_reports_by_source(self, reports: List[Dict[str, Any]], base_output_dir: Path):
        """
        Save comparison reports grouped by data source type
        
        Args:
            reports: List of reports, each report should contain a source_type field (for grouping, will be removed when saving)
            base_output_dir: Base output directory (e.g., testscan_data)
        """
        # Group reports by data source type
        reports_by_source = {}
        for report in reports:
            source_type = report.get("source_type", "unknown")
            if source_type not in reports_by_source:
                reports_by_source[source_type] = []
            # Create a copy and remove the source_type field (as the final report format does not need this field)
            report_copy = {k: v for k, v in report.items() if k != "source_type"}
            reports_by_source[source_type].append(report_copy)
        
        # Save reports for each data source
        for source_type, source_reports in reports_by_source.items():
            # Create data source specific directory
            output_dir = base_output_dir / f"threat_detection_{source_type}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to corresponding directory
            output_file = output_dir / "comparison_reports.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(source_reports, f, ensure_ascii=False, indent=2)
                print(f"Comparison reports have been saved: {output_file} ({len(source_reports)} entries)")
            except Exception as e:
                print(f"Error: Failed to save comparison reports to {output_file}: {e}")

