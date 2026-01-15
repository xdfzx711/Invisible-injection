#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threat Report Converter
Convert formatted_threats.json to standard format and separate BIDI threats
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging


class ThreatReportConverter:
    """Threat Report Converter"""
    
    def __init__(self, logger=None):
        """
        Initialize converter
        
        Args:
            logger: Logger
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def convert_formatted_threats(self, input_file: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Convert formatted_threats.json to standard format and separate BIDI threats
        
        Args:
            input_file: Path to input formatted_threats.json file
            output_dir: Output directory
            
        Returns:
            Conversion statistics
        """
        self.logger.info(f"Starting threat report conversion: {input_file}")
        
        # Read original data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        threats_list = data.get('threats', [])
        
        # Separate BIDI and non-BIDI threats
        bidi_threats, non_bidi_threats = self._separate_bidi_threats(threats_list)
        
        # Convert to standard format
        bidi_standard = self._convert_to_standard_format(bidi_threats, is_bidi=True)
        non_bidi_standard = self._convert_to_standard_format(non_bidi_threats, is_bidi=False)
        
        # Statistics
        stats = {
            'total_threats': len(threats_list),
            'bidi_threats': len(bidi_threats),
            'non_bidi_threats': len(non_bidi_threats),
            'bidi_converted': len(bidi_standard),
            'non_bidi_converted': len(non_bidi_standard),
            'skipped_too_long': 0,
            'conversion_success': True
        }
        
        # Save files
        try:
            # Save BIDI threats
            bidi_output_file = output_dir / "bidi_threats.json"
            with open(bidi_output_file, 'w', encoding='utf-8') as f:
                json.dump(bidi_standard, f, ensure_ascii=False, indent=2)
            
            # Save non-BIDI threats
            suspicious_output_file = output_dir / "Suspicious threat.json"
            with open(suspicious_output_file, 'w', encoding='utf-8') as f:
                json.dump(non_bidi_standard, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Conversion completed:")
            self.logger.info(f"  - BIDI threats: {len(bidi_standard)} entries -> {bidi_output_file}")
            self.logger.info(f"  - Other threats: {len(non_bidi_standard)} entries -> {suspicious_output_file}")
            
            stats['bidi_output_file'] = str(bidi_output_file)
            stats['suspicious_output_file'] = str(suspicious_output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to save conversion results: {e}")
            stats['conversion_success'] = False
            stats['error'] = str(e)
        
        return stats
    
    def _separate_bidi_threats(self, threats_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        分离BIDI threats和non-BIDI threats
        
        Args:
            threats_list: Threat list
            
        Returns:
            (bidi_threats, non_bidi_threats)
        """
        bidi_threats = []
        non_bidi_threats = []
        
        for threat in threats_list:
            if self._is_bidi_threat(threat):
                bidi_threats.append(threat)
            else:
                non_bidi_threats.append(threat)
        
        self.logger.info(f"Threat separation completed: BIDI={len(bidi_threats)}, non-BIDI={len(non_bidi_threats)}")
        
        return bidi_threats, non_bidi_threats
    
    def _is_bidi_threat(self, threat: Dict[str, Any]) -> bool:
        """
        Check是否为BIDI threats
        
        Args:
            threat: Threat data
            
        Returns:
            是否为BIDI threats
        """
        # Method 1: Check unicode_type_id
        if threat.get('unicode_type_id') == 3:
            return True
        
        # Method 2: Check unicode_type_name
        if threat.get('unicode_type_name') == 'bidi':
            return True
        
        # Method 3: Check if threat contains BIDI characters
        threat_chars = threat.get('threat_characters', [])
        bidi_unicode_points = {
            'U+202A', 'U+202B', 'U+202C', 'U+202D', 'U+202E',  # LRE, RLE, PDF, LRO, RLO
            'U+2066', 'U+2067', 'U+2068', 'U+2069'              # LRI, RLI, FSI, PDI
        }
        
        for char_info in threat_chars:
            if char_info.get('unicode_point') in bidi_unicode_points:
                return True
        
        return False
    
    def _convert_to_standard_format(self, threats_list: List[Dict[str, Any]], is_bidi: bool = False) -> List[Dict[str, Any]]:
        """
        转换Threat list为标准格式
        
        Args:
            threats_list: Threat list
            is_bidi: 是否为BIDI threats
            
        Returns:
            标准格式的Threat list
        """
        standard_threats = []
        skipped_count = 0
        
        for threat in threats_list:
            # Get original and adversarial instructions
            original = threat.get('original_instruction', '')
            adversarial = threat.get('adversarial_instruction', '')
            
            # Check instruction length, skip long instructions (refer to convert_to_json.py logic)
            original_len = len(original) if original else 0
            adversarial_len = len(adversarial) if adversarial else 0
            
            if original_len > 3000 or adversarial_len > 3000:
                skipped_count += 1
                continue
            
            # Convert to standard format（参考convert_to_json.py的格式）
            formatted_entry = {
                'instruction': 'Compare the adversarial instruction with unicode characters and the original instruction, and determine whether the added unicode characters changed the semantics of the sentence',
                'input': f"Original instruction: {original}\nAdversarial instruction: {adversarial}"
                # Note: Do not add output field
            }
            
            standard_threats.append(formatted_entry)
        
        if skipped_count > 0:
            threat_type = "BIDI" if is_bidi else "non-BIDI"
            self.logger.info(f"{threat_type}威胁转换: 跳过{skipped_count}entries过长指令")
        
        return standard_threats
    
    def get_conversion_summary(self, stats: Dict[str, Any]) -> str:
        """
        生成转换摘要信息
        
        Args:
            stats: Conversion statistics
            
        Returns:
            摘要字符串
        """
        if not stats.get('conversion_success', False):
            return f"转换Failed: {stats.get('error', '未知Error')}"
        
        summary = f"""
威胁报告转换摘要:
==========================================
总威胁数: {stats['total_threats']}
  - BIDI threats: {stats['bidi_threats']} entries
  - Other threats: {stats['non_bidi_threats']} entries

转换结果:
  - BIDI标准格式: {stats['bidi_converted']} entries
  - 其他标准格式: {stats['non_bidi_converted']} entries

输出File:
  - BIDI threats: {stats.get('bidi_output_file', 'N/A')}
  - Other threats: {stats.get('suspicious_output_file', 'N/A')}
==========================================
        """
        
        return summary.strip()


# 示例用法
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建转换器
    converter = ThreatReportConverter()
    
    # 转换示例
    input_file = Path("testscan_data/threat_detection_reddit/formatted_threats.json")
    output_dir = Path("testscan_data/threat_detection_reddit")
    
    if input_file.exists():
        stats = converter.convert_formatted_threats(input_file, output_dir)
        print(converter.get_conversion_summary(stats))
    else:
        print(f"输入File不exists: {input_file}")
