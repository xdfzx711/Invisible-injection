#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unicode Threat Analysis Main Program
Extract characters from parsed structured data and detect specified Unicode threat characters
"""

import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os

# Add project root directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import project tools
from data_collection.utils.logger import setup_logger

# Fix relative import issues
try:
    from .character_extractor import CharacterExtractor
    from .identifier_status_config import IdentifierStatusConfig
    from .identifier_status_detector import IdentifierStatusDetector
    from .homograph_config import HomographConfig
    from .homograph_detector import HomographDetector
    from .unicode_type_classifier import UnicodeTypeClassifier
    from .threat_formatter import ThreatFormatter
    from .comparison_report_generator import ComparisonReportGenerator
    from .threat_report_converter import ThreatReportConverter
except ImportError:
    # If relative import fails, use absolute import
    from character_extractor import CharacterExtractor
    from identifier_status_config import IdentifierStatusConfig
    from identifier_status_detector import IdentifierStatusDetector
    from homograph_config import HomographConfig
    from homograph_detector import HomographDetector
    from unicode_type_classifier import UnicodeTypeClassifier
    from threat_formatter import ThreatFormatter
    from comparison_report_generator import ComparisonReportGenerator
    from threat_report_converter import ThreatReportConverter

class UnicodeAnalysisManager:
    """Unicode Analysis Manager - Simplified version based on identifier status"""

    def __init__(self, output_dir: Union[str, Path] = None,
                 lookup_file: Union[str, Path] = None,
                 data_sources: List[str] = None,
                 force_extract: bool = False,
                 sample_size: int = None,
                 enable_homograph: bool = True):

        # Set default paths (relative to testscan directory)
        if output_dir is None:
            # 从unicode_analysisdirectory向上找到testscandirectory
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            output_dir = testscan_dir / "testscan_data"

        if lookup_file is None:
            # Lookup table file is in testscan_data/unicode_analysis directory
            current_dir = Path(__file__).parent
            testscan_dir = current_dir.parent
            lookup_file = testscan_dir / "testscan_data" / "unicode_analysis" / "identifier_status_lookup.json"

        self.output_dir = Path(output_dir)
        self.force_extract = force_extract
        self.logger = setup_logger('UnicodeAnalysisManager', 'unicode_analysis.log')

        # Set data sources to process
        self.data_sources = data_sources or ['json', 'csv', 'xml', 'html', 'reddit', 'twitter', 'github', 'godofprompt']
        self.logger.info(f"Enabled data sources: {', '.join(self.data_sources)}")
        if force_extract:
            self.logger.info("强制重新提取字符模式has been启用")

        # Initialize configuration
        self.config = IdentifierStatusConfig(lookup_file)

        # Create main output directory (must be defined before use)
        self.analysis_output_dir = self.output_dir / "unicode_analysis"
        self.analysis_output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.character_extractor = CharacterExtractor(output_dir, self.data_sources)
        self.restriction_detector = IdentifierStatusDetector(self.config, output_dir, self.data_sources)

        # Initialize homoglyph character detector (optional)
        self.enable_homograph = enable_homograph
        self.homograph_detector = None
        confusables_file = self.analysis_output_dir / "unicode_confusables.json"
        
        if enable_homograph:
            try:
                # Find confusables data file
                if confusables_file.exists():
                    homograph_config = HomographConfig(confusables_file)
                    self.homograph_detector = HomographDetector(homograph_config, output_dir, self.data_sources)
                    self.logger.info("Homoglyph Character检测器has been启用")
                else:
                    self.logger.warning(f"Confusables data file not found: {confusables_file}")
                    self.logger.warning("Homoglyph detection will be skipped")
                    self.enable_homograph = False
            except Exception as e:
                self.logger.error(f"Failed to initialize homoglyph detector: {e}")
                self.enable_homograph = False
        else:
            self.logger.info("Homoglyph detection is disabled")
        
        # 初始化新格式化组件
        self.logger.info("Initializing threat formatting component...")
        self.unicode_classifier = UnicodeTypeClassifier(confusables_file if confusables_file.exists() else None)
        self.threat_formatter = ThreatFormatter()
        self.logger.info("Threat formatting component initialized")

        # Initializing comparison report generator
        self.comparison_report_generator = ComparisonReportGenerator()
        self.logger.info("Comparison report generator initialized")
        
        # Initializing threat report converter
        self.threat_converter = ThreatReportConverter(logger=self.logger)
        self.logger.info("Threat report converter initialized")
    
    def analyze_unicode_restrictions(self, parsed_data_dir: Union[str, Path] = None) -> Dict[str, Any]:
        """Perform Unicode identifier status analysis"""
        self.logger.info("Starting Unicode identifier status analysis...")

        if parsed_data_dir is None:
            # Use unified parsed_data directory, let character_extractor find subdirectories
            parsed_data_dir = self.output_dir / "parsed_data"
            self.logger.info(f"Using parsed data directory: {parsed_data_dir}")

        parsed_data_dir = Path(parsed_data_dir)

        if not parsed_data_dir.exists():
            self.logger.error(f"Parsed data directory does not exist: {parsed_data_dir}")
            return {"error": "Parsed data directory does not exist"}
        
        start_time = time.time()
        
        try:
            # 第一步：智能字符提取（自动Checkhas been有File）
            self.logger.info("Step 1: Intelligent character extraction...")
            all_characters = self.character_extractor.extract_from_parsed_data_smart(
                parsed_data_dir,
                force_extract=self.force_extract
            )

            if not all_characters:
                self.logger.warning("No characters extracted")

                # Provide detailed diagnostic information
                diagnostic_info = self._diagnose_extraction_failure(parsed_data_dir)
                error_message = f"No characters extracted。{diagnostic_info}"

                self.logger.error(error_message)
                return {"error": error_message}

            # 第二步：检测受限字符
            self.logger.info("Step 2: Detect restricted characters...")
            restriction_detections = self.restriction_detector.detect_restrictions_in_characters(all_characters)

            # 第三步：检测Homoglyph Character（可选）
            homograph_detections = []
            if self.enable_homograph and self.homograph_detector:
                self.logger.info("Step 3: Detect homoglyph characters...")
                homograph_detections = self.homograph_detector.detect_homographs_in_characters(all_characters)
            else:
                self.logger.info("Step 3: Skip homoglyph detection")

            # 第四步：Generate new format threat reports
            self.logger.info("Step 4: Generate new format threat reports...")
            formatted_reports = self._generate_formatted_reports(
                restriction_detections, homograph_detections
            )

            # 新增步骤：生成对比报告
            if homograph_detections:
                self.logger.info("Step 4.5: Generate homoglyph comparison reports...")
                comparison_reports = self.comparison_report_generator.generate_reports(
                    all_characters, homograph_detections
                )
                if comparison_reports:
                    # 按数据源类型分组保存对比报告
                    self.comparison_report_generator.save_reports_by_source(
                        comparison_reports, self.output_dir
                    )
                    self.logger.info(f"Comparison reports saved by data source type to {self.output_dir}/threat_detection_*/ directory")

            # 第五步：Generate analysis results
            end_time = time.time()
            analysis_result = self._generate_analysis_result(
                all_characters, restriction_detections, homograph_detections, start_time, end_time
            )
            
            # 添加新格式报告信息到分析结果
            analysis_result["formatted_reports"] = {
                "total_threats": len(formatted_reports),
                "reports_generated": True
            }

            self.logger.info("Unicode identifier status analysis completed")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Unicode identifier status analysis failed: {e}")
            return {"error": f"分析Failed: {e}"}
    
    def _generate_formatted_reports(self, 
                                    restriction_detections: List[Dict[str, Any]],
                                    homograph_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate new format threat reports
        
        Args:
            restriction_detections: Restricted character detection results
            homograph_detections: Homoglyph character detection results
        
        Returns:
            List of formatted threat reports
        """
        self.logger.info("开始生成新格式威胁报告...")
        
        # Merge all detection results
        all_detections = []
        
        # Add restricted character detection (mainly zero_width, bidi, etc.)
        all_detections.extend(restriction_detections)
        
        # Add homoglyph character detection (confusables)
        all_detections.extend(homograph_detections)
        
        if not all_detections:
            self.logger.info("No threat characters detected")
            return []
        
        self.logger.info(f"Total detected {len(all_detections)} threat characters")
        
        # Use formatter to generate reports
        formatted_reports = self.threat_formatter.generate_threat_reports(
            all_detections,
            self.unicode_classifier
        )
        
        self.logger.info(f"Generated {len(formatted_reports)} threat reports")
        
        # 按数据源保存报告
        self._save_formatted_reports_by_source(formatted_reports)
        
        return formatted_reports
    
    def _save_formatted_reports_by_source(self, reports: List[Dict[str, Any]]):
        """Save formatted reports by data source"""
        # 按数据源分组
        reports_by_source = {}
        for report in reports:
            source_type = report["source_info"].get("source_type", "unknown")
            if source_type not in reports_by_source:
                reports_by_source[source_type] = []
            reports_by_source[source_type].append(report)
        
        # 为每个数据源保存报告
        for source_type, source_reports in reports_by_source.items():
            output_dir = self.output_dir / f"threat_detection_{source_type}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存JSON格式
            json_file = output_dir / "formatted_threats.json"
            self.threat_formatter.save_formatted_reports(
                source_reports, 
                json_file,
                include_metadata=True
            )
            
            # 保存统计摘要
            stats = self.threat_formatter.generate_summary_statistics(source_reports)
            stats_file = output_dir / "threat_summary_by_type.json"
            
            import json
            try:
                with open(stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
                self.logger.info(f"统计摘要has been保存: {stats_file}")
            except Exception as e:
                self.logger.error(f"保存统计摘要Failed: {e}")
            
            # Convert to standard format并分离BIDI threats
            self.logger.info(f"开始转换{source_type}威胁报告为标准格式...")
            try:
                conversion_stats = self.threat_converter.convert_formatted_threats(json_file, output_dir)
                if conversion_stats.get('conversion_success', False):
                    self.logger.info(f"{source_type}威胁报告Conversion completed:")
                    self.logger.info(f"  - BIDI threats: {conversion_stats['bidi_converted']} entries")
                    self.logger.info(f"  - Other threats: {conversion_stats['non_bidi_converted']} entries")
                else:
                    self.logger.error(f"{source_type}威胁报告转换Failed: {conversion_stats.get('error', '未知Error')}")
            except Exception as e:
                self.logger.error(f"转换{source_type}威胁报告时发生异常: {e}")
    
    def _generate_analysis_result(self, all_characters: List[Dict[str, Any]],
                                restriction_detections: List[Dict[str, Any]],
                                homograph_detections: List[Dict[str, Any]],
                                start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate analysis results"""
        
        # 基本统计
        char_summary = self.character_extractor.get_character_summary(all_characters)
        
        # 受限字符统计
        restriction_stats = self._calculate_restriction_stats(restriction_detections)

        # Homoglyph Character统计
        homograph_stats = self._calculate_homograph_stats(homograph_detections)

        # File统计
        file_stats = self._calculate_file_stats(all_characters, restriction_detections, homograph_detections)

        # 检测器统计
        detector_stats = self.restriction_detector.get_detection_statistics()
        homograph_detector_stats = self.homograph_detector.get_detection_statistics() if self.homograph_detector else {}

        analysis_result = {
            "analysis_info": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": end_time - start_time,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
                "output_directory": str(self.restriction_detector.output_dir.relative_to(self.output_dir.parent)),
                "analysis_type": "identifier_status"
            },
            "character_extraction": {
                "total_characters": char_summary["total_characters"],
                "unique_characters": char_summary["unique_characters"],
                "source_types": char_summary["source_types"]
            },
            "restriction_detection": {
                "total_restrictions": len(restriction_detections),
                "restriction_rate": len(restriction_detections) / char_summary["total_characters"] if char_summary["total_characters"] > 0 else 0,
                "allowed_characters": detector_stats["allowed_characters_found"],
                "restricted_characters": detector_stats["restricted_characters_found"],
                "detection_types": restriction_stats["detection_types"],
                "top_restricted_chars": restriction_stats["top_restricted_chars"]
            },
            "homograph_detection": {
                "enabled": self.enable_homograph,
                "total_homographs": len(homograph_detections),
                "homograph_rate": len(homograph_detections) / char_summary["total_characters"] if char_summary["total_characters"] > 0 else 0,
                "confusable_types": homograph_stats["confusable_types"],
                "top_confusable_chars": homograph_stats["top_confusable_chars"],
                "detection_time": homograph_detector_stats.get("detection_time", 0)
            },
            "file_analysis": file_stats,
            "config_info": {
                "total_allowed_characters": len(self.config.allowed_characters),
                "detection_settings": self.config.get_detection_settings(),
                "config_status": self.config.get_statistics()["config_status"]
            }
        }
        
        return analysis_result

    def _calculate_homograph_stats(self, homograph_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算Homoglyph CharacterStatistics"""

        confusable_types = {}
        confusable_chars = {}

        for detection in homograph_detections:
            # 混淆类型统计
            confusable_type = detection.get("confusable_type", "unknown")
            confusable_types[confusable_type] = confusable_types.get(confusable_type, 0) + 1

            # 混淆字符统计
            character = detection.get("character", "")
            unicode_point = detection.get("unicode_point", "")
            char_key = f"{character} ({unicode_point})"
            confusable_chars[char_key] = confusable_chars.get(char_key, 0) + 1

        # 获取前10个最常见的混淆字符
        top_confusable_chars = sorted(confusable_chars.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "confusable_types": confusable_types,
            "top_confusable_chars": top_confusable_chars,
            "unique_confusable_chars": len(confusable_chars)
        }

    def _calculate_restriction_stats(self, restriction_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算受限字符Statistics"""

        detection_types = {}
        restricted_chars = {}
        char_counts = {}
        
        for detection in restriction_detections:
            # 检测类型统计
            detection_type = detection.get("detection_info", {}).get("detection_type", "unknown")
            detection_types[detection_type] = detection_types.get(detection_type, 0) + 1

            # 受限字符统计
            char_key = detection["unicode_point"]
            if char_key not in char_counts:
                char_counts[char_key] = {
                    "character": detection["character"],
                    "unicode_point": detection["unicode_point"],
                    "name": detection.get("name", "UNKNOWN"),
                    "status": detection.get("status", "Restricted"),
                    "category": detection.get("category", "Unknown"),
                    "count": 0
                }
            char_counts[char_key]["count"] += 1

        # 获取最常见的受限字符
        top_restricted_chars = sorted(char_counts.values(), key=lambda x: x["count"], reverse=True)[:10]

        return {
            "detection_types": detection_types,
            "top_restricted_chars": top_restricted_chars
        }
    
    def _calculate_file_stats(self, all_characters: List[Dict[str, Any]],
                            restriction_detections: List[Dict[str, Any]],
                            homograph_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算FileStatistics"""
        
        # 所有File统计
        all_files = {}
        for char in all_characters:
            file_path = char["source_info"]["file_path"]
            if file_path not in all_files:
                all_files[file_path] = {
                    "file_path": file_path,
                    "file_name": char["source_info"]["file_name"],
                    "source_type": char["source_info"]["source_type"],
                    "total_characters": 0,
                    "restrictions_found": 0,
                    "homographs_found": 0
                }
            all_files[file_path]["total_characters"] += 1

        # 受限字符File统计
        for detection in restriction_detections:
            file_path = detection["source_info"]["file_path"]
            if file_path in all_files:
                all_files[file_path]["restrictions_found"] += 1

        # Homoglyph CharacterFile统计
        for detection in homograph_detections:
            file_path = detection["source_info"]["file_path"]
            if file_path in all_files:
                all_files[file_path]["homographs_found"] += 1

        # 计算比率
        for file_info in all_files.values():
            file_info["restriction_rate"] = file_info["restrictions_found"] / file_info["total_characters"] if file_info["total_characters"] > 0 else 0
            file_info["homograph_rate"] = file_info["homographs_found"] / file_info["total_characters"] if file_info["total_characters"] > 0 else 0

        # 按受限字符数量排序
        files_by_restrictions = sorted(all_files.values(), key=lambda x: x["restrictions_found"], reverse=True)

        return {
            "total_files": len(all_files),
            "files_with_restrictions": len([f for f in all_files.values() if f["restrictions_found"] > 0]),
            "files_with_homographs": len([f for f in all_files.values() if f["homographs_found"] > 0]),
            "files_by_restriction_count": files_by_restrictions[:10],  # 前10个受限字符最多的File
            "source_type_distribution": self._get_source_type_distribution(all_files.values())
        }
    
    def _get_source_type_distribution(self, file_infos) -> Dict[str, Dict[str, int]]:
        """获取按源类型的分布统计"""
        distribution = {}
        
        for file_info in file_infos:
            source_type = file_info["source_type"]
            if source_type not in distribution:
                distribution[source_type] = {
                    "total_files": 0,
                    "files_with_restrictions": 0,
                    "total_characters": 0,
                    "total_restrictions": 0
                }

            distribution[source_type]["total_files"] += 1
            distribution[source_type]["total_characters"] += file_info["total_characters"]
            distribution[source_type]["total_restrictions"] += file_info["restrictions_found"]

            if file_info["restrictions_found"] > 0:
                distribution[source_type]["files_with_restrictions"] += 1
        
        return distribution

    def _diagnose_extraction_failure(self, parsed_data_dir: Path) -> str:
        """诊断字符提取Failed的原因"""
        diagnostic_messages = []

        # CheckParsed data directory
        if not parsed_data_dir.exists():
            diagnostic_messages.append(f"Parsed data directory does not exist: {parsed_data_dir}")
            return " ".join(diagnostic_messages)

        # Check各数据源directory
        source_handlers = {
            'json': 'json_analysis',
            'csv': 'csv_analysis',
            'xml': 'xml_analysis',
            'html': 'html_analysis',
            'reddit': 'reddit_analysis',
            'twitter': 'twitter_analysis',
            'github': 'github_analysis'
        }

        missing_dirs = []
        empty_dirs = []
        existing_dirs = []

        for source_type in self.data_sources:
            if source_type in source_handlers:
                dir_name = source_handlers[source_type]
            else:
                # 动态数据源directory推断
                dir_name = f"{source_type}_analysis"
                
            source_dir = parsed_data_dir / dir_name

            if not source_dir.exists():
                missing_dirs.append(f"{source_type}({dir_name})")
            elif not any(source_dir.iterdir()):
                empty_dirs.append(f"{source_type}({dir_name})")
            else:
                existing_dirs.append(f"{source_type}({dir_name})")

        # Check字符提取File
        char_output_dir = self.output_dir / "unicode_analysis" / "character_extraction"
        extraction_file_status = []
        large_files = []

        for source_type in self.data_sources:
            extraction_file = char_output_dir / f"character_extraction_{source_type}.json"
            if extraction_file.exists():
                try:
                    size = extraction_file.stat().st_size
                    size_gb = size / (1024 * 1024 * 1024)

                    if size == 0:
                        extraction_file_status.append(f"{source_type}(File为空)")
                    elif size_gb > 1.0:
                        extraction_file_status.append(f"{source_type}(Fileexists,{size_gb:.2f}GB)")
                        if size_gb > 8.0:
                            large_files.append(f"{source_type}({size_gb:.2f}GB)")
                    else:
                        size_mb = size / (1024 * 1024)
                        extraction_file_status.append(f"{source_type}(Fileexists,{size_mb:.1f}MB)")
                except Exception as e:
                    extraction_file_status.append(f"{source_type}(FileError:{e})")
            else:
                extraction_file_status.append(f"{source_type}(File不exists)")

        # 构建诊断消息
        if missing_dirs:
            diagnostic_messages.append(f"缺失数据源directory: {', '.join(missing_dirs)}")

        if empty_dirs:
            diagnostic_messages.append(f"空数据源directory: {', '.join(empty_dirs)}")

        if existing_dirs:
            diagnostic_messages.append(f"exists数据源directory: {', '.join(existing_dirs)}")

        diagnostic_messages.append(f"字符提取File状态: {', '.join(extraction_file_status)}")

        # 提供建议
        suggestions = []
        if missing_dirs or empty_dirs:
            suggestions.append("请先运行数据解析步骤生成解析数据")

        if not existing_dirs:
            suggestions.append("请Check数据源配置和Parsed data directory")

        if large_files:
            suggestions.append(f"检测到超大File({', '.join(large_files)})可能导致内存不足")
            suggestions.append("建议: 1) 增加系统内存 2) 使用 --force-extract 重新生成File 3) 分批处理数据")
        else:
            suggestions.append("可以使用 --force-extract 参数强制重新提取字符")

        if suggestions:
            diagnostic_messages.append(f"建议: {'; '.join(suggestions)}")

        return " ".join(diagnostic_messages)

    # 注释：删除_save_analysis_result方法，不再生成unicode_analysis_result.json
    # def _save_analysis_result(self, analysis_result: Dict[str, Any]):
    #     """保存分析结果"""
    #
    #     import json
    #
    #     result_file = self.analysis_output_dir / "unicode_analysis_result.json"
    #     try:
    #         with open(result_file, 'w', encoding='utf-8') as f:
    #             json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    #         self.logger.info(f"分析结果has been保存: {result_file}")
    #     except Exception as e:
    #         self.logger.error(f"保存分析结果Failed: {e}")

    def print_analysis_summary(self, analysis_result: Dict[str, Any]):
        """打印分析摘要"""

        print("\n" + "="*70)
        print("🔍 Unicode identifier status analysis completed摘要")
        print("="*70)

        # 基本信息
        char_info = analysis_result["character_extraction"]
        restriction_info = analysis_result["restriction_detection"]
        file_info = analysis_result["file_analysis"]

        print(f"⏱️  分析耗时: {analysis_result['analysis_info']['duration_seconds']:.2f} 秒")
        print(f"📊 字符分析: {char_info['total_characters']} 个字符 ({char_info['unique_characters']} 个唯一字符)")
        print(f"📁 File分析: {file_info['total_files']} 个File")

        # Restricted character detection results
        print(f"\n✅ 标识符状态检测:")
        print(f"   ✅ 允许字符: {restriction_info['allowed_characters']} 个")
        print(f"   ❌ 受限字符: {restriction_info['restricted_characters']} 个")
        print(f"   📈 受限率: {restriction_info['restriction_rate']:.4f} ({restriction_info['restriction_rate']*100:.2f}%)")
        print(f"   📁 涉及File: {file_info['files_with_restrictions']}/{file_info['total_files']} 个")

        if restriction_info["total_restrictions"] > 0:
            print(f"\n📊 检测类型分布:")
            for detection_type, count in restriction_info["detection_types"].items():
                print(f"   • {detection_type}: {count} 个")

            if restriction_info["top_restricted_chars"]:
                print(f"\n🔝 最常见受限字符:")
                for i, restricted_char in enumerate(restriction_info["top_restricted_chars"][:5]):
                    print(f"   {i+1}. '{restricted_char['character']}' ({restricted_char['unicode_point']}) - {restricted_char['count']} 次")

        else:
            print(f"\n✅ 标识符状态检测: 所有字符均为允许状态")
        
        # 新格式报告信息
        if "formatted_reports" in analysis_result and analysis_result["formatted_reports"]["reports_generated"]:
            print(f"\n📝 新格式威胁报告:")
            print(f"   📄 威胁报告数: {analysis_result['formatted_reports']['total_threats']} entries")
            print(f"   ✅ has been生成新格式报告File:")
            print(f"      • formatted_threats.json (JSON格式)")
            print(f"      • threat_summary_by_type.json (按类型统计)")
        
        print(f"\n📂 Output directory: {self.analysis_output_dir}")
        print("="*70)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Unicode标识符状态分析工具 - 从指定数据源提取字符并检测受限字符",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python analysis_main.py                    # 分析所有数据源
  python analysis_main.py --csv              # 只分析CSV数据
  python analysis_main.py --reddit           # 只分析Reddit数据
  python analysis_main.py --godofprompt      # 只分析GodOfPrompt数据
  python analysis_main.py --csv --html       # 分析CSV和HTML数据
  python analysis_main.py --json --xml --reddit  # 分析JSON、XML和Reddit数据
  python analysis_main.py --github --godofprompt  # 分析GitHub和GodOfPrompt数据
        """
    )

    # 数据源选择参数
    parser.add_argument('--json', action='store_true',
                       help='分析JSON数据源')
    parser.add_argument('--csv', action='store_true',
                       help='分析CSV数据源')
    parser.add_argument('--xml', action='store_true',
                       help='分析XML数据源')
    parser.add_argument('--html', action='store_true',
                       help='分析HTML数据源')
    parser.add_argument('--reddit', action='store_true',
                       help='分析Reddit数据源')
    parser.add_argument('--twitter', action='store_true',
                       help='分析Twitter数据源')
    parser.add_argument('--github', action='store_true',
                       help='分析GitHub数据源')
    parser.add_argument('--godofprompt', action='store_true',
                       help='分析GodOfPrompt数据源')

    # 其他参数
    parser.add_argument('--output-dir', type=str,
                       help='Output directory路径 (默认: testscan_data)')
    parser.add_argument('--lookup-file', type=str,
                       help='标识符状态查找表File路径 (默认: identifier_status_lookup.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    parser.add_argument('--force-extract', action='store_true',
                       help='强制重新提取字符，即使has been有提取结果')

    return parser.parse_known_args()

def main():
    """主函数"""
    # 解析命令行参数
    args, unknown_args = parse_arguments()

    # 确定要处理的数据源
    data_sources = []
    if args.json:
        data_sources.append('json')
    if args.csv:
        data_sources.append('csv')
    if args.xml:
        data_sources.append('xml')
    if args.html:
        data_sources.append('html')
    if args.reddit:
        data_sources.append('reddit')
    if args.twitter:
        data_sources.append('twitter')
    if args.github:
        data_sources.append('github')
    if args.godofprompt:
        data_sources.append('godofprompt')

    # 处理动态参数 (例如 --reddit_top)
    for arg in unknown_args:
        if arg.startswith('--'):
            source_name = arg[2:]
            if source_name and source_name not in data_sources:
                data_sources.append(source_name)

    # 如果没有指定任何数据源，则使用所有数据源
    if not data_sources:
        data_sources = ['json', 'csv', 'xml', 'html', 'reddit', 'twitter', 'github', 'godofprompt']

    print("🔍 Unicode标识符状态分析工具")
    print("="*50)
    print(f"📊 分析数据源: {', '.join(data_sources)}")
    print("="*50)

    # 初始化分析管理器
    analysis_manager = UnicodeAnalysisManager(
        output_dir=args.output_dir,
        lookup_file=args.lookup_file,
        data_sources=data_sources,
        force_extract=args.force_extract
    )

    # 显示配置摘要
    config_stats = analysis_manager.config.get_statistics()
    print(f"📋 配置信息:")
    print(f"   ✅ 允许字符数: {config_stats['total_allowed_characters']:,}")
    print(f"   📁 查找表File: {config_stats['lookup_file']}")
    print(f"   🔧 配置状态: {config_stats['config_status']}")

    # 执行分析
    result = analysis_manager.analyze_unicode_restrictions()

    if "error" in result:
        print(f"\n❌ 分析Failed: {result['error']}")
        return

    # 显示分析摘要
    analysis_manager.print_analysis_summary(result)

    # 显示检测详情
    if result["restriction_detection"]["total_restrictions"] > 0:
        base_output_dir = result["analysis_info"]["output_directory"]
        print(f"\n💡 建议查看详细检测结果:")

        # 显示各数据源的检测结果
        for source in data_sources:
            source_dir = f"{base_output_dir}/threat_detection_{source}"
            print(f"   📁 {source.upper()} 数据源:")
            print(f"      📋 检测汇总: {source_dir}/identifier_status_detection_summary.json")
            print(f"      🔍 受限字符: {source_dir}/identifier_status_detections_identifier_status.json")

        print(f"   📊 总体汇总: {base_output_dir}/identifier_status_detection_overall_summary.json")

    print(f"\n✅ Unicode identifier status analysis completed！")

if __name__ == "__main__":
    main()
