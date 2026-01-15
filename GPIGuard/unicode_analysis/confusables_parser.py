#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unicode Confusables 解析器
解析 confusables.txt File并转换为威胁检测配置格式
"""

import re
import json
import logging
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

class ConfusablesParser:
    """Unicode Confusables 解析器"""

    def __init__(self, output_dir: Union[str, Path] = None):
        # 设置绝对输出路径
        if output_dir is None:
            # 获取当前File的绝对路径，然后构建目标directory
            current_file = Path(__file__).resolve()
            testscan_root = current_file.parent.parent  # 从 unicode_analysis 回到 testscan
            output_dir = testscan_root / "testscan_data" / "unicode_analysis"

        self.output_dir = Path(output_dir)
        self.logger = setup_logger('ConfusablesParser', 'confusables_parser.log')

        # 创建Output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Confusables解析器Output directory: {self.output_dir.absolute()}")
    
    def parse_confusables_file(self, confusables_file: Union[str, Path]) -> Dict[str, Any]:
        """解析confusables.txtFile"""
        confusables_file = Path(confusables_file)

        if not confusables_file.exists():
            self.logger.error(f"ConfusablesFile不exists: {confusables_file}")
            return {}

        self.logger.info(f"开始解析confusablesFile: {confusables_file}")

        # 简化的数据结构，不包含危险等级
        confusables_data = {
            "metadata": {
                "source_file": str(confusables_file.absolute()),
                "parsed_time": "",
                "total_entries": 0
            },
            "confusables_map": {}  # 主要的混淆字符映射
        }

        parse_stats = {
            "total_lines": 0,
            "comment_lines": 0,
            "empty_lines": 0,
            "parsed_entries": 0,
            "error_lines": 0,
            "confusable_types": {}
        }
        
        try:
            with open(confusables_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parse_stats["total_lines"] += 1
                    
                    # 跳过空行
                    if not line.strip():
                        parse_stats["empty_lines"] += 1
                        continue
                    
                    # 跳过注释行
                    if line.strip().startswith('#'):
                        parse_stats["comment_lines"] += 1
                        continue
                    
                    # 解析数据行
                    try:
                        entry = self._parse_confusable_line(line, line_num)
                        if entry:
                            unicode_point = entry["unicode_point"]
                            confusables_data["confusables_map"][unicode_point] = entry
                            parse_stats["parsed_entries"] += 1

                            # 统计类型
                            conf_type = entry.get("confusable_type", "unknown")
                            parse_stats["confusable_types"][conf_type] = parse_stats["confusable_types"].get(conf_type, 0) + 1
                    
                    except Exception as e:
                        self.logger.warning(f"解析第{line_num}行Failed: {e}")
                        parse_stats["error_lines"] += 1
        
        except Exception as e:
            self.logger.error(f"读取confusablesFileFailed: {e}")
            return {}

        # 更新元数据
        import datetime
        confusables_data["metadata"]["parsed_time"] = datetime.datetime.now().isoformat()
        confusables_data["metadata"]["total_entries"] = parse_stats["parsed_entries"]

        self.logger.info(f"Confusables解析Completed: {parse_stats['parsed_entries']} 个entries目")
        self._log_parse_stats(parse_stats)

        return confusables_data

    def save_confusables_data(self, confusables_data: Dict[str, Any], filename: str = "unicode_confusables.json") -> Path:
        """保存解析后的confusables数据到指定directory"""
        output_file = self.output_dir / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(confusables_data, f, ensure_ascii=False, indent=2)

            total_entries = confusables_data.get("metadata", {}).get("total_entries", 0)
            self.logger.info(f"Confusables数据has been保存: {output_file.absolute()}")
            self.logger.info(f"包含 {total_entries} 个混淆字符entries目")

            return output_file

        except Exception as e:
            self.logger.error(f"保存confusables数据Failed: {e}")
            raise

    def parse_and_save(self, confusables_file: Union[str, Path], output_filename: str = "unicode_confusables.json") -> Path:
        """解析confusablesFile并保存结果"""
        self.logger.info("开始解析和保存confusables数据")

        # 解析File
        confusables_data = self.parse_confusables_file(confusables_file)

        if not confusables_data or not confusables_data.get("confusables_map"):
            self.logger.error("解析Failed或没有有效数据")
            return None

        # 保存结果
        output_file = self.save_confusables_data(confusables_data, output_filename)

        # 打印摘要
        self.print_parse_summary(confusables_data)

        return output_file

    def _parse_confusable_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """解析单行confusable数据"""
        
        # 移除行尾注释和空白
        line = line.strip()
        if '#' in line:
            data_part = line.split('#')[0].strip()
            comment_part = line.split('#', 1)[1].strip()
        else:
            data_part = line
            comment_part = ""
        
        if not data_part:
            return None
        
        # 解析数据部分：source ; target ; type
        parts = [part.strip() for part in data_part.split(';')]
        if len(parts) < 3:
            self.logger.warning(f"第{line_num}行格式不正确: {line}")
            return None
        
        source_code = parts[0]
        target_code = parts[1]
        conf_type = parts[2]
        
        try:
            # 转换Unicode码点为字符
            source_char = self._unicode_point_to_char(source_code)
            target_char = self._unicode_point_to_char(target_code)
            
            # 从注释中提取字符名称
            source_name, target_name = self._extract_names_from_comment(comment_part)
            
            # 简化的entries目结构，不包含危险等级
            entry = {
                "unicode_point": f"U+{source_code}",
                "character": source_char,
                "name": source_name or f"U+{source_code}",
                "confusable_with": {
                    "character": target_char,
                    "unicode_point": f"U+{target_code}",
                    "name": target_name or f"U+{target_code}"
                },
                "confusable_type": conf_type,
                "description": f"Confusable with {target_char} (type: {conf_type})",
                "source": "confusables.txt"
            }

            return entry
            
        
        except Exception as e:
            self.logger.warning(f"第{line_num}行字符转换Failed: {e}")
            return None
    
    def _unicode_point_to_char(self, unicode_point: str) -> str:
        """将Unicode码点转换为字符"""
        try:
            # 移除可能的前缀和空白
            unicode_point = unicode_point.strip().upper()
            if unicode_point.startswith('U+'):
                unicode_point = unicode_point[2:]
            
            # 处理多个码点的情况（用空格分隔）
            if ' ' in unicode_point:
                code_points = unicode_point.split()
                chars = [chr(int(cp, 16)) for cp in code_points]
                return ''.join(chars)
            else:
                return chr(int(unicode_point, 16))
        
        except ValueError as e:
            self.logger.warning(f"无效的Unicode码点: {unicode_point}")
            return ""
    
    def _extract_names_from_comment(self, comment: str) -> tuple:
        """从注释中提取字符名称"""
        try:
            # 注释格式通常是: ( char → char ) NAME → NAME
            if '→' in comment and ')' in comment:
                # 提取括号后的部分
                if ')' in comment:
                    names_part = comment.split(')', 1)[1].strip()
                    if '→' in names_part:
                        parts = names_part.split('→')
                        source_name = parts[0].strip()
                        target_name = parts[1].strip() if len(parts) > 1 else ""
                        return source_name, target_name
            
            return "", ""
        
        except Exception:
            return "", ""
    
    def _log_parse_stats(self, stats: Dict[str, Any]):
        """记录解析Statistics"""
        self.logger.info("解析统计:")
        self.logger.info(f"  总行数: {stats['total_lines']}")
        self.logger.info(f"  注释行: {stats['comment_lines']}")
        self.logger.info(f"  空行: {stats['empty_lines']}")
        self.logger.info(f"  解析entries目: {stats['parsed_entries']}")
        self.logger.info(f"  Error行: {stats['error_lines']}")
        
        if stats['confusable_types']:
            self.logger.info("  类型分布:")
            for conf_type, count in sorted(stats['confusable_types'].items()):
                self.logger.info(f"    {conf_type}: {count}")
    
    def convert_to_config_format(self, confusables_data: Dict[str, Any]) -> Dict[str, Any]:
        """将confusables数据转换为配置格式"""

        config_characters = {}

        for unicode_point, data in confusables_data.items():
            # 转换为现有配置格式
            config_entry = {
                "char": data["char"],
                "name": data["name"],
                "similar_to": data["similar_to"],
                "description": data["description"],
                "confusable_type": data["confusable_type"],
                "unicode_source": data["unicode_source"]
                # 注意：不添加 risk_level，使用类别默认级别
            }

            config_characters[unicode_point] = config_entry

        return config_characters
    
    def save_confusables_config(self, confusables_data: Dict[str, Any], 
                              output_file: Union[str, Path] = None) -> Path:
        """保存confusables配置数据"""
        
        if output_file is None:
            output_file = self.parser_output_dir / "confusables_config.json"
        else:
            output_file = Path(output_file)
        
        # 转换为配置格式
        config_data = self.convert_to_config_format(confusables_data)
        
        # 创建完整的配置结构
        full_config = {
            "confusables_info": {
                "source": "Unicode confusables.txt",
                "total_characters": len(config_data),
                "description": "Unicode confusable characters for homograph attack detection"
            },
            "characters": config_data
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Confusables配置has been保存: {output_file}")
            self.logger.info(f"包含 {len(config_data)} 个字符")
            
            return output_file
        
        except Exception as e:
            self.logger.error(f"保存confusables配置Failed: {e}")
            raise
    
    def print_parse_summary(self, confusables_data: Dict[str, Any]):
        """打印解析摘要"""

        print("\n" + "="*60)
        print("📋 Unicode Confusables 解析摘要")
        print("="*60)

        metadata = confusables_data.get("metadata", {})
        confusables_map = confusables_data.get("confusables_map", {})

        print(f"📊 总字符数: {len(confusables_map)}")
        print(f"📅 解析时间: {metadata.get('parsed_time', 'Unknown')}")
        print(f"📁 源File: {metadata.get('source_file', 'Unknown')}")

        # 统计类型分布
        type_stats = {}
        for data in confusables_map.values():
            conf_type = data.get("confusable_type", "unknown")
            type_stats[conf_type] = type_stats.get(conf_type, 0) + 1

        print(f"\n📈 类型分布:")
        for conf_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {conf_type}: {count:,} 个字符")

        # 显示一些示例
        print(f"\n📝 字符示例 (前5个):")
        for i, (unicode_point, data) in enumerate(list(confusables_map.items())[:5]):
            char = data["character"]
            name = data["name"]
            confusable_with = data.get("confusable_with", {})
            target_char = confusable_with.get("character", "?")
            target_point = confusable_with.get("unicode_point", "?")

            print(f"   {i+1}. '{char}' ({unicode_point}) - {name}")
            print(f"      混淆于: '{target_char}' ({target_point})")

        print("="*60)


def main():
    """主函数 - 解析confusables.txtFile"""
    print("🔧 Unicode Confusables 解析器")
    print("="*50)

    # 创建解析器实例
    parser = ConfusablesParser()

    # 查找confusables.txtFile
    current_dir = Path(__file__).parent.parent  # 回到testscandirectory
    confusables_file = current_dir / "confusables.txt"

    if not confusables_file.exists():
        print(f"❌ 找不到confusables.txtFile: {confusables_file}")
        print("请确保confusables.txtFile位于testscandirectory下")
        return

    print(f"📁 找到confusablesFile: {confusables_file}")

    try:
        # 解析并保存
        output_file = parser.parse_and_save(confusables_file)

        if output_file:
            print(f"\n✅ 解析Completed！")
            print(f"📄 输出File: {output_file.absolute()}")
        else:
            print(f"\n❌ 解析Failed")

    except Exception as e:
        print(f"\n❌ 解析过程中出错: {e}")


if __name__ == "__main__":
    main()
