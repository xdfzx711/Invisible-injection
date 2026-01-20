#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unicode Threat Report Formatter
Generate new format threat detection reports
"""

from typing import Dict, List, Any, Tuple
import json
from pathlib import Path
from datetime import datetime


class ThreatFormatter:
    """Threat Report Formatter"""
    
    def __init__(self):
        pass
    
    def remove_threat_characters(self, text: str, threat_chars: List[str]) -> str:
        """
        Remove threat characters and generate cleaned version
        
        Args:
            text: Original text
            threat_chars: Threat character list
        
        Returns:
            Cleaned text
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
        Format single entry detection record
        
        Args:
            unicode_type_id: Unicode type ID (0-4)
            original_text: Cleaned original instruction
            adversarial_text: Adversarial instruction containing threat characters
        
        Returns:
            Formatted string
        """
        return (f"Unicode type ID: {unicode_type_id}\n"
                f"Original instruction: {original_text}\n"
                f"Adversarial instruction: {adversarial_text}")
    
    def group_detections_by_string(self, detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group detection results by source string
        
        Args:
            detections: Character-level detection list
        
        Returns:
            Detection dictionary grouped by string
        """
        grouped = {}
        
        for detection in detections:
            source_info = detection.get("source_info", {})
            string_value = source_info.get("string_value", "")
            
            if not string_value:
                continue
            
            # Use string content as key
            if string_value not in grouped:
                grouped[string_value] = []
            
            grouped[string_value].append(detection)
        
        return grouped
    
    def generate_threat_reports(self, 
                                detections: List[Dict[str, Any]], 
                                classifier) -> List[Dict[str, Any]]:
        """
        Generate threat reports (string level)
        
        Args:
            detections: Character-level detection list
            classifier: Unicode type classifier
        
        Returns:
            List of formatted threat reports
        """
        # Group by string
        grouped_detections = self.group_detections_by_string(detections)
        
        reports = []
        
        for adversarial_text, char_detections in grouped_detections.items():
            # Extract threat characters
            threat_chars = [d.get("character", "") for d in char_detections]
            
            # Classify threat type
            unicode_type_id = classifier.classify_string_threats(adversarial_text, char_detections)
            
            if unicode_type_id is None:
                continue
            
            # Generate cleaned version
            original_text = self.remove_threat_characters(adversarial_text, threat_chars)
            
            # Create report entry item
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
        Save formatted report
        
        Args:
            reports: Threat report list
            output_file: Output file path
            include_metadata: Whether to include metadata
        """
        # Group by type ID
        reports_by_type = {}
        for report in reports:
            type_id = report["unicode_type_id"]
            if type_id not in reports_by_type:
                reports_by_type[type_id] = []
            reports_by_type[type_id].append(report)
        
        # Build output data
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
        
        # Save JSON format
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Threat report saved: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
    
    def save_formatted_text_reports(self, 
                                   reports: List[Dict[str, Any]], 
                                   output_file: Path):
        """
        Save plain text format report (one entry per line)
        
        Args:
            reports: Threat report list
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for report in reports:
                    # Write formatted output (replace \n with actual line breaks)
                    formatted = report["formatted_output"]
                    f.write(formatted + "\n\n")  # Empty line between each entry record
            
            print(f"✅ Text format report saved: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save text report: {e}")
    
    def generate_summary_statistics(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistical summary
        
        Args:
            reports: Threat report list
        
        Returns:
            Statistical summary dictionary
        """
        stats = {
            "total_threats": len(reports),
            "by_type": {},
            "top_threat_sources": []
        }
        
        # Statistics by type
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
        
        # Statistics on threat sources
        source_counts = {}
        for report in reports:
            source_file = report["source_info"].get("file_name", "unknown")
            source_counts[source_file] = source_counts.get(source_file, 0) + 1
        
        # Get top 10 sources with most threats
        stats["top_threat_sources"] = sorted(
            source_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return stats


# Test code
if __name__ == "__main__":
    formatter = ThreatFormatter()
    
    # Test cleanup function
    adversarial = "Please visit https://goo​gle.com"  # Contains zero-width character
    threat_chars = ["​"]  # U+200B
    original = formatter.remove_threat_characters(adversarial, threat_chars)
    
    print("Cleanup test:")
    print(f"Adversarial text: {repr(adversarial)}")
    print(f"After cleanup: {repr(original)}")
    
    # Test formatting
    formatted = formatter.format_detection_entry(1, original, adversarial)
    print(f"\nFormatted output:\n{formatted}")

