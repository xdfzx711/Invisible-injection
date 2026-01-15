#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union
import sys
import os

# 添加父directory到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_collection.utils.logger import setup_logger

class CharacterExtractor:
    """字符提取器 - 从解析结果中逐字符提取"""
    
    def __init__(self, output_dir: Union[str, Path] = "testscan", data_sources: List[str] = None):
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('CharacterExtractor', 'character_extraction.log')

        # 设置要处理的数据源
        self.data_sources = data_sources or ['json', 'csv', 'xml', 'html', 'reddit', 'twitter', 'github', 'godofprompt']
        self.logger.info(f"字符提取器启用的数据源: {', '.join(self.data_sources)}")

        # 创建Output directory
        self.char_output_dir = self.output_dir / "unicode_analysis" / "character_extraction"
        self.char_output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_from_parsed_data(self, parsed_data_dir: Union[str, Path]) -> List[Dict[str, Any]]:
        """从Parsed data directory中提取所有字符"""
        parsed_data_dir = Path(parsed_data_dir)
        self.logger.info(f"开始从解析数据中提取字符: {parsed_data_dir}")

        all_characters = []
        source_characters = {}  # 按数据源分组的字符
        char_id_counter = 0

        # 处理各种数据源
        source_handlers = {
            'json': ('json_analysis', self._extract_from_json_results),
            'csv': ('csv_analysis', self._extract_from_csv_results),
            'xml': ('xml_analysis', self._extract_from_xml_results),
            'html': ('html_analysis', self._extract_from_html_results),
            'reddit': ('reddit_analysis', self._extract_from_reddit_results),
            'twitter': ('twitter_analysis', self._extract_from_twitter_results),
            'github': ('github_analysis', self._extract_from_github_results),
            'godofprompt': ('godofprompt_analysis', self._extract_from_godofprompt_results)
        }

        for source_type in self.data_sources:
            handler = None
            dir_name = None
            
            if source_type in source_handlers:
                dir_name, handler = source_handlers[source_type]
            else:
                # 尝试处理动态数据源
                dir_name = f"{source_type}_analysis"
                
                # 根据名称推断处理程序
                if 'reddit' in source_type:
                    handler = self._extract_from_reddit_results
                elif 'twitter' in source_type:
                    handler = self._extract_from_twitter_results
                elif 'github' in source_type:
                    handler = self._extract_from_github_results
                elif 'godofprompt' in source_type:
                    handler = self._extract_from_godofprompt_results
                elif 'html' in source_type:
                    handler = self._extract_from_html_results
                elif 'xml' in source_type:
                    handler = self._extract_from_xml_results
                elif 'csv' in source_type:
                    handler = self._extract_from_csv_results
                elif 'json' in source_type:
                    handler = self._extract_from_json_results
            
            if dir_name and handler:
                source_dir = parsed_data_dir / dir_name

                if source_dir.exists():
                    self.logger.info(f"处理 {source_type.upper()} 数据源...")
                    source_chars = []
                    char_id_counter = handler(source_dir, source_chars, char_id_counter)

                    # 修正提取出的字符的 source_type，确保与当前处理的 source_type 一致
                    # 这对于动态数据源（如 reddit_top）尤为重要
                    for char in source_chars:
                        if "source_info" in char:
                            char["source_info"]["source_type"] = source_type
                        
                        # 更新 char_id 前缀以匹配 source_type
                        if "char_id" in char:
                            parts = char["char_id"].rsplit('_', 1)
                            if len(parts) == 2 and parts[1].isdigit():
                                char["char_id"] = f"{source_type}_{parts[1]}"

                    if source_chars:
                        source_characters[source_type] = source_chars
                        all_characters.extend(source_chars)
                        self.logger.info(f"{source_type.upper()} 数据源提取了 {len(source_chars)} 个字符")
                else:
                    self.logger.info(f"{source_type.upper()} 数据directory不exists: {source_dir}")
            else:
                self.logger.warning(f"无法识别的数据源类型或未找到处理程序: {source_type}")

        self.logger.info(f"字符提取Completed，共提取 {len(all_characters)} 个字符")

        # 按数据源分别保存提取结果
        self._save_extracted_characters_by_source(source_characters, all_characters)

        return all_characters

    def extract_from_parsed_data_smart(self, parsed_data_dir: Union[str, Path], force_extract: bool = False) -> List[Dict[str, Any]]:
        """智能字符提取 - 跳过has beenexists的提取结果"""

        if force_extract:
            self.logger.info("强制重新提取字符")
            return self.extract_from_parsed_data(parsed_data_dir)

        # Check现有提取File
        existing_sources, missing_sources = self._check_existing_extractions()

        if not missing_sources:
            # 所有数据源都has been提取，直接加载现有数据
            self.logger.info("所有数据源的字符has been提取，跳过提取步骤")
            loaded_characters = self._load_existing_extractions(existing_sources)

            if not loaded_characters:
                self.logger.warning(f"虽然检测到提取Fileexists，但加载的字符数为0。数据源: {existing_sources}")
                self.logger.warning("这可能是由于File损坏、格式Error或确实没有可提取的字符")

            return loaded_characters

        if existing_sources:
            # 部分数据源has been提取，只提取缺失的
            self.logger.info(f"发现has been提取的数据源: {existing_sources}")
            self.logger.info(f"需要提取的数据源: {missing_sources}")

            # 临时修改数据源列表，只处理缺失的
            original_sources = self.data_sources
            self.data_sources = missing_sources

            try:
                # 提取缺失的数据源
                new_characters = self.extract_from_parsed_data(parsed_data_dir)

                # 加载现有数据并合并
                existing_characters = self._load_existing_extractions(existing_sources)

                # 合并所有字符
                all_characters = existing_characters + new_characters
                self.logger.info(f"合并Completed，总字符数: {len(all_characters)}")

                if not all_characters:
                    self.logger.warning(f"合并后字符数为0。现有字符: {len(existing_characters)}, 新提取字符: {len(new_characters)}")

                return all_characters
            finally:
                # 恢复原始数据源列表
                self.data_sources = original_sources
        else:
            # 没有现有提取，正常提取
            self.logger.info("开始提取所有数据源的字符")
            extracted_characters = self.extract_from_parsed_data(parsed_data_dir)

            if not extracted_characters:
                self.logger.warning(f"从解析数据中提取的字符数为0。数据源: {self.data_sources}")
                self.logger.warning(f"Parsed data directory: {parsed_data_dir}")

            return extracted_characters

    def _check_existing_extractions(self) -> tuple[List[str], List[str]]:
        """Check现有的字符提取File（简化版Check）"""
        existing_sources = []
        missing_sources = []

        for source in self.data_sources:
            extraction_file = self.char_output_dir / f"character_extraction_{source}.json"

            # 简化Check：只Checkexists性和大小 > 0
            if extraction_file.exists() and extraction_file.stat().st_size > 0:
                existing_sources.append(source)
                self.logger.debug(f"发现有效的提取File: {extraction_file.name}")
            else:
                missing_sources.append(source)
                self.logger.debug(f"缺失或无效的提取File: {extraction_file.name}")

        return existing_sources, missing_sources

    def _load_existing_extractions(self, source_list: List[str]) -> List[Dict[str, Any]]:
        """加载现有的字符提取数据"""
        all_characters = []

        for source in source_list:
            extraction_file = self.char_output_dir / f"character_extraction_{source}.json"

            try:
                if not extraction_file.exists():
                    self.logger.error(f"加载 {source} 提取FileFailed: File不exists - {extraction_file}")
                    continue

                file_size = extraction_file.stat().st_size
                if file_size == 0:
                    self.logger.error(f"加载 {source} 提取FileFailed: File为空 - {extraction_file}")
                    continue

                # CheckFile大小，如果超过1GB则Warning并提供建议
                file_size_gb = file_size / (1024 * 1024 * 1024)
                if file_size_gb > 1.0:
                    self.logger.warning(f"检测到大File: {source} 提取File大小为 {file_size_gb:.2f}GB")
                    self.logger.warning(f"加载大File可能导致内存不足，建议使用 --force-extract 重新生成较小的File")

                    # 如果File超过8GB，直接跳过加载
                    if file_size_gb > 8.0:
                        self.logger.error(f"File过大({file_size_gb:.2f}GB)，跳过加载以避免内存不足")
                        self.logger.error(f"请使用 --force-extract 参数重新生成提取File")
                        continue

                self.logger.info(f"正在加载 {source} 提取File ({file_size_gb:.2f}GB)...")

                # 对于大File，尝试分块加载
                if file_size_gb > 2.0:
                    self.logger.info(f"File较大({file_size_gb:.2f}GB)，尝试分块加载...")
                    characters = self._load_large_file_chunked(extraction_file, source)
                    if characters:
                        all_characters.extend(characters)
                        self.logger.info(f"分块加载 {source.upper()} 字符: {len(characters)} 个")
                        continue
                    else:
                        self.logger.warning(f"分块加载Failed，尝试常规加载...")

                with open(extraction_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    self.logger.error(f"加载 {source} 提取FileFailed: File格式Error，不是有效的JSON对象 - {extraction_file}")
                    continue

                # CheckFile格式
                extraction_info = data.get('extraction_info', {})
                file_format = extraction_info.get('format', 'standard')

                if file_format == 'compressed':
                    # 处理压缩格式
                    characters = self._load_compressed_characters(data, source)
                else:
                    # 处理标准格式
                    characters = data.get('characters', [])
                    if not isinstance(characters, list):
                        self.logger.error(f"加载 {source} 提取FileFailed: 'characters'字段不是列表格式 - {extraction_file}")
                        continue

                all_characters.extend(characters)
                self.logger.info(f"加载 {source.upper()} 字符: {len(characters)} 个 (格式: {file_format})")

            except MemoryError as e:
                file_size_gb = extraction_file.stat().st_size / (1024 * 1024 * 1024)
                self.logger.error(f"加载 {source} 提取FileFailed: 内存不足 - File大小 {file_size_gb:.2f}GB")
                self.logger.error(f"解决方案: 1) 增加系统内存 2) 使用 --force-extract 重新生成File 3) 分批处理数据")
            except json.JSONDecodeError as e:
                self.logger.error(f"加载 {source} 提取FileFailed: JSON解析Error - {extraction_file}, Error: {e}")
            except PermissionError as e:
                self.logger.error(f"加载 {source} 提取FileFailed: 权限Error - {extraction_file}, Error: {e}")
            except FileNotFoundError as e:
                self.logger.error(f"加载 {source} 提取FileFailed: File未找到 - {extraction_file}, Error: {e}")
            except Exception as e:
                self.logger.error(f"加载 {source} 提取FileFailed: 未知Error - {extraction_file}, Error类型: {type(e).__name__}, Error: {e}")

        # 记录加载汇总信息
        self.logger.info(f"字符加载Completed，共加载 {len(all_characters)} 个字符，来源: {source_list}")

        if not all_characters and source_list:
            self.logger.warning(f"虽然尝试加载 {len(source_list)} 个数据源，但没有成功加载任何字符")

        return all_characters

    def _load_large_file_chunked(self, extraction_file: Path, source: str) -> List[Dict[str, Any]]:
        """分块加载大File以避免内存不足"""
        self.logger.info(f"尝试分块加载大File: {extraction_file}")

        try:
            # 尝试使用ijson进行流式解析
            import ijson

            characters = []
            with open(extraction_file, 'rb') as f:
                # 解析characters数组中的每个对象
                parser = ijson.items(f, 'characters.item')

                chunk_size = 10000  # 每次处理10000个字符
                chunk = []

                for char_obj in parser:
                    chunk.append(char_obj)

                    if len(chunk) >= chunk_size:
                        characters.extend(chunk)
                        self.logger.info(f"has been加载 {len(characters)} 个字符...")
                        chunk = []

                # 处理最后一批
                if chunk:
                    characters.extend(chunk)

                self.logger.info(f"分块加载Completed，共加载 {len(characters)} 个字符")
                return characters

        except ImportError:
            self.logger.error("分块加载需要ijson库，请安装: pip install ijson")
            return []
        except Exception as e:
            self.logger.error(f"分块加载Failed: {e}")
            return []

    def _extract_from_json_results(self, json_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从JSON解析结果中提取字符"""
        self.logger.info(f"处理JSON解析结果: {json_dir}")
        
        for json_file in json_dir.glob("*_parsed.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'json', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"处理JSONFileFailed {json_file}: {e}")
        
        return char_id_counter

    def _extract_from_github_results(self, github_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从GitHub解析结果中提取字符"""
        self.logger.info(f"处理GitHub解析结果: {github_dir}")

        for gh_file in github_dir.glob("*_parsed.json"):
            try:
                with open(gh_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result.get('file_info', {})
                text_entries = parsed_result.get('text_entries', [])

                owner = file_info.get('owner', '')
                repo = file_info.get('repo', '')
                repository_url = file_info.get('repository_url', '')

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if not string_value:
                        continue
                    # 针对 GitHub 的通用文本入口
                    source_info = {
                        "source_type": "github",
                        "content_type": entry.get('field_type', 'github_content'),
                        "owner": owner,
                        "repo": repo,
                        "repository_url": repository_url,
                        "file_name": gh_file.name,
                        "file_path": str(gh_file.relative_to(self.output_dir.parent))
                    }
                    char_id_counter = self._extract_characters_from_text(
                        text=string_value,
                        source_info=source_info,
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            except Exception as e:
                self.logger.error(f"处理GitHubFileFailed {gh_file}: {e}")

        return char_id_counter
    
    def _extract_from_godofprompt_results(self, godofprompt_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从GodOfPrompt解析结果中提取字符"""
        self.logger.info(f"处理GodOfPrompt解析结果: {godofprompt_dir}")

        for gp_file in godofprompt_dir.glob("*_parsed.json"):
            try:
                with open(gp_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result.get('file_info', {})
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if not string_value:
                        continue
                    
                    # 获取 slug 和 category 作为上下文信息
                    slug = entry.get('slug', '')
                    category = entry.get('category', '')
                    
                    # 针对 GodOfPrompt 的文本入口
                    source_info = {
                        "source_type": "godofprompt",
                        "content_type": "prompt",
                        "slug": slug,
                        "category": category,
                        "file_name": gp_file.name,
                        "file_path": str(gp_file.relative_to(self.output_dir.parent))
                    }
                    char_id_counter = self._extract_characters_from_text(
                        text=string_value,
                        source_info=source_info,
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            except Exception as e:
                self.logger.error(f"处理GodOfPromptFileFailed {gp_file}: {e}")

        return char_id_counter
    
    def _extract_from_csv_results(self, csv_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从CSV解析结果中提取字符"""
        self.logger.info(f"处理CSV解析结果: {csv_dir}")
        
        for csv_file in csv_dir.glob("*_parsed.json"):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'csv', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"处理CSVFileFailed {csv_file}: {e}")
        
        return char_id_counter
    
    def _extract_from_xml_results(self, xml_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从XML解析结果中提取字符"""
        self.logger.info(f"处理XML解析结果: {xml_dir}")
        
        for xml_file in xml_dir.glob("*_parsed.json"):
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)
                
                if 'error' in parsed_result.get('parsing_info', {}):
                    continue
                
                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])
                
                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'xml', all_characters, char_id_counter
                        )
                        
            except Exception as e:
                self.logger.error(f"处理XMLFileFailed {xml_file}: {e}")
        
        return char_id_counter

    def _extract_from_html_results(self, html_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从HTML解析结果中提取字符"""
        self.logger.info(f"处理HTML解析结果: {html_dir}")

        for html_file in html_dir.glob("*_extracted.json"):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                # Check是否有Error
                page_info = parsed_result.get('page_info', {})
                if 'error' in page_info:
                    continue

                # 获取File信息
                file_info = {
                    'file_name': html_file.name,
                    'relative_path': str(html_file.relative_to(html_dir.parent.parent)),
                    'url': page_info.get('url', ''),
                    'website_name': page_info.get('website_name', ''),
                    'page_type': page_info.get('page_type', '')
                }

                # 提取文本entries目
                extracted_content = parsed_result.get('extracted_content', {})
                text_entries = extracted_content.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'html', all_characters, char_id_counter
                        )

                # 也从meta信息中提取字符
                meta_info = extracted_content.get('meta_info', {})
                for meta_key, meta_value in meta_info.items():
                    if isinstance(meta_value, str) and meta_value:
                        # 创建metaentries目
                        meta_entry = {
                            'element_type': 'meta',
                            'tag_name': 'meta',
                            'meta_key': meta_key,
                            'field_type': 'meta'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            meta_value, meta_entry, file_info, 'html', all_characters, char_id_counter
                        )

                # 从链接文本中提取字符
                links = extracted_content.get('links', [])
                for link in links:
                    link_text = link.get('text', '')
                    if link_text:
                        link_entry = {
                            'element_type': 'link_text',
                            'tag_name': 'a',
                            'url': link.get('url', ''),
                            'field_type': 'link'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            link_text, link_entry, file_info, 'html', all_characters, char_id_counter
                        )

                # 从图片alt文本中提取字符
                images = extracted_content.get('images', [])
                for image in images:
                    alt_text = image.get('alt', '')
                    if alt_text:
                        img_entry = {
                            'element_type': 'image_alt',
                            'tag_name': 'img',
                            'src': image.get('src', ''),
                            'field_type': 'alt_text'
                        }
                        char_id_counter = self._extract_characters_from_string(
                            alt_text, img_entry, file_info, 'html', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理HTMLFileFailed {html_file}: {e}")

        return char_id_counter

    def _detect_normalization_changes(self, original: str, nfc: str, nfkc: str) -> List[Dict[str, Any]]:
        """检测Unicode规范化变化"""
        changes = []

        # NFC变化检测
        if original != nfc:
            changes.append({
                "type": "nfc_change",
                "original": original,
                "normalized": nfc,
                "risk_level": "medium",
                "description": "字符串在NFC规范化后发生变化",
                "character_count_change": len(nfc) - len(original)
            })

        # NFKC变化检测
        if original != nfkc:
            risk_level = "high" if nfc != nfkc else "medium"
            changes.append({
                "type": "nfkc_change",
                "original": original,
                "normalized": nfkc,
                "risk_level": risk_level,
                "description": "字符串在NFKC规范化后发生变化",
                "character_count_change": len(nfkc) - len(original)
            })

        # 长度显著变化检测（可能的安全风险）
        if len(original) != len(nfkc) and abs(len(original) - len(nfkc)) > 1:
            changes.append({
                "type": "significant_length_change",
                "original_length": len(original),
                "normalized_length": len(nfkc),
                "length_difference": len(nfkc) - len(original),
                "risk_level": "high",
                "description": "规范化导致字符串长度显著变化"
            })

        return changes

    def _assess_normalization_risk(self, changes: List[Dict[str, Any]]) -> str:
        """评估规范化变化的风险级别"""
        if not changes:
            return "none"

        risk_levels = [change["risk_level"] for change in changes]

        if "high" in risk_levels:
            return "high"
        elif "medium" in risk_levels:
            return "medium"
        else:
            return "low"

    def _find_original_position(self, char: str, normalized_pos: int, original: str, normalized: str) -> int:
        """尝试找到字符在原始字符串中的位置"""
        # 简单的启发式方法：如果字符串长度相同，位置应该对应
        if len(original) == len(normalized):
            return normalized_pos

        # 如果长度不同，尝试通过字符匹配找到大致位置
        # 这是一个简化的实现，复杂情况可能需要更精确的算法
        if normalized_pos < len(original):
            return normalized_pos
        else:
            return len(original) - 1

    def _extract_characters_from_string(self, string_value: str, entry: Dict, file_info: Dict,
                                      source_type: str, all_characters: List, char_id_counter: int) -> int:
        """从单个字符串中提取所有字符"""

        # 1. 进行Unicode规范化
        original_string = string_value
        nfc_normalized = unicodedata.normalize('NFC', string_value)
        nfkc_normalized = unicodedata.normalize('NFKC', string_value)

        # 2. 检测规范化变化
        normalization_changes = self._detect_normalization_changes(
            original_string, nfc_normalized, nfkc_normalized
        )

        # 3. 评估风险级别
        normalization_risk = self._assess_normalization_risk(normalization_changes)

        # 4. 使用NFKC规范化后的字符串进行字符提取（更严格的规范化）
        final_string = nfkc_normalized

        # 5. 记录字符串级别的规范化信息
        string_normalization_info = {
            "original_string": original_string,
            "nfc_normalized": nfc_normalized,
            "nfkc_normalized": nfkc_normalized,
            "final_string_used": final_string,
            "has_normalization_changes": len(normalization_changes) > 0,
            "normalization_changes": normalization_changes,
            "normalization_risk_level": normalization_risk,
            "original_length": len(original_string),
            "final_length": len(final_string)
        }

        for position, char in enumerate(final_string):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "position_in_original": self._find_original_position(char, position, original_string, final_string),
                "source_info": {
                    "string_value": final_string,  # 使用规范化后的字符串
                    "string_length": len(final_string),
                    "file_path": file_info.get('relative_path', ''),
                    "file_name": file_info.get('file_name', ''),
                    "source_type": source_type,
                    "field_type": entry.get('field_type', 'unknown')
                },
                "normalization_info": string_normalization_info
            }
            
            # 添加特定于源类型的位置信息
            if source_type == 'json':
                char_info["source_info"]["json_path"] = entry.get('json_path', '')
            elif source_type == 'csv':
                char_info["source_info"]["csv_row"] = entry.get('row', 0)
                char_info["source_info"]["csv_column"] = entry.get('column_name', '')
            elif source_type == 'xml':
                char_info["source_info"]["xml_path"] = entry.get('xml_path', '')
                char_info["source_info"]["element_type"] = entry.get('element_type', '')
            elif source_type == 'html':
                char_info["source_info"]["html_element_type"] = entry.get('element_type', '')
                char_info["source_info"]["html_tag_name"] = entry.get('tag_name', '')
                char_info["source_info"]["xpath"] = entry.get('xpath', '')
                char_info["source_info"]["attributes"] = entry.get('attributes', {})
                char_info["source_info"]["url"] = file_info.get('url', '')
                char_info["source_info"]["website_name"] = file_info.get('website_name', '')
                char_info["source_info"]["page_type"] = file_info.get('page_type', '')

                # 添加特定元素类型的额外信息
                if entry.get('element_type') == 'link_text':
                    char_info["source_info"]["link_url"] = entry.get('url', '')
                elif entry.get('element_type') == 'image_alt':
                    char_info["source_info"]["image_src"] = entry.get('src', '')
                elif entry.get('element_type') == 'meta':
                    char_info["source_info"]["meta_key"] = entry.get('meta_key', '')
            elif source_type == 'twitter':
                # 添加Twitter特定的上下文信息
                context = entry.get('context', {})
                char_info["source_info"]["content_type"] = entry.get('field_type', 'unknown')
                char_info["source_info"]["tweet_id"] = context.get('tweet_id', '')
                char_info["source_info"]["author"] = context.get('author', '')
                char_info["source_info"]["created_at"] = context.get('created_at', '')
                char_info["source_info"]["lang"] = context.get('lang', '')
                char_info["source_info"]["query"] = context.get('query', '')

                # 添加上下文预览（字符前后的文本）
                context_length = 20
                start_pos = max(0, position - context_length)
                end_pos = min(len(string_value), position + context_length + 1)
                char_info["source_info"]["context_before"] = string_value[start_pos:position]
                char_info["source_info"]["context_after"] = string_value[position + 1:end_pos]
            elif source_type == 'reddit':
                # 添加Reddit特定的上下文信息
                context = entry.get('context', {})
                char_info["source_info"]["content_type"] = entry.get('field_type', 'unknown')
                char_info["source_info"]["subreddit"] = context.get('subreddit', '')
                char_info["source_info"]["post_id"] = context.get('post_id', '')
                char_info["source_info"]["comment_id"] = context.get('comment_id', '')
                char_info["source_info"]["submission_id"] = context.get('submission_id', '')

                # 添加上下文预览
                context_length = 20
                start_pos = max(0, position - context_length)
                end_pos = min(len(string_value), position + context_length + 1)
                char_info["source_info"]["context_before"] = string_value[start_pos:position]
                char_info["source_info"]["context_after"] = string_value[position + 1:end_pos]

            all_characters.append(char_info)
            char_id_counter += 1
        
        return char_id_counter

    def _save_extracted_characters_by_source(self, source_characters: Dict[str, List[Dict[str, Any]]], all_characters: List[Dict[str, Any]]):
        """按数据源分别保存提取的字符数据"""

        # 为每个数据源保存单独的File
        for source_type, characters in source_characters.items():
            output_file = self.char_output_dir / f"character_extraction_{source_type}.json"

            # 创建数据源特定的结果
            source_result = {
                "extraction_info": {
                    "source_type": source_type,
                    "total_characters": len(characters),
                    "unique_characters": len(set(char["character"] for char in characters)),
                    "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "characters": characters
            }

            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(source_result, f, ensure_ascii=False, indent=2)
                self.logger.info(f"{source_type.upper()} 字符提取结果has been保存: {output_file} ({len(characters)} 个字符)")
            except Exception as e:
                self.logger.error(f"保存 {source_type} 字符提取结果Failed: {e}")

    # 删除了统计生成方法，简化输出

    def get_character_summary(self, all_characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取Character extraction summary信息"""
        if not all_characters:
            return {"total_characters": 0, "unique_characters": 0}
        
        return {
            "total_characters": len(all_characters),
            "unique_characters": len(set(char["character"] for char in all_characters)),
            "source_types": list(set(char["source_info"]["source_type"] for char in all_characters)),
            "sample_characters": all_characters[:10]  # 前10个字符作为样本
        }

    def _extract_from_json_results(self, json_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从JSON解析结果中提取字符"""
        self.logger.info(f"处理JSON解析结果: {json_dir}")

        for json_file in json_dir.glob("*_parsed.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'json', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理JSONFileFailed {json_file}: {e}")

        return char_id_counter

    def _extract_from_csv_results(self, csv_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从CSV解析结果中提取字符"""
        self.logger.info(f"处理CSV解析结果: {csv_dir}")

        for csv_file in csv_dir.glob("*_parsed.json"):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'csv', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理CSVFileFailed {csv_file}: {e}")

        return char_id_counter

    def _extract_from_xml_results(self, xml_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从XML解析结果中提取字符"""
        self.logger.info(f"处理XML解析结果: {xml_dir}")

        for xml_file in xml_dir.glob("*_parsed.json"):
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    parsed_result = json.load(f)

                if 'error' in parsed_result.get('parsing_info', {}):
                    continue

                file_info = parsed_result['file_info']
                text_entries = parsed_result.get('text_entries', [])

                for entry in text_entries:
                    string_value = entry.get('value', '')
                    if string_value:
                        char_id_counter = self._extract_characters_from_string(
                            string_value, entry, file_info, 'xml', all_characters, char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理XMLFileFailed {xml_file}: {e}")

        return char_id_counter



    def _extract_from_reddit_results(self, reddit_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从Reddit解析结果中提取字符"""
        self.logger.info(f"处理Reddit解析结果: {reddit_dir}")

        # 处理帖子File
        for posts_file in reddit_dir.glob("*_posts_parsed.json"):
            char_id_counter = self._extract_from_reddit_posts(posts_file, all_characters, char_id_counter)

        # 处理评论File
        for comments_file in reddit_dir.glob("*_comments_parsed.json"):
            char_id_counter = self._extract_from_reddit_comments(comments_file, all_characters, char_id_counter)

        return char_id_counter

    def _extract_from_twitter_results(self, twitter_dir: Path, all_characters: List, char_id_counter: int) -> int:
        """从Twitter解析结果中提取字符"""
        self.logger.info(f"处理Twitter解析结果: {twitter_dir}")

        for twitter_file in twitter_dir.glob("*.json"):
            try:
                with open(twitter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'error' in data.get('parsing_info', {}):
                    continue

                # Twitter数据格式: {"parsing_info": {...}, "tweets": [...]}
                tweets = data.get('tweets', [])
                if not tweets:
                    continue

                parsing_info = data.get('parsing_info', {})
                query = parsing_info.get('query', 'unknown')

                for tweet in tweets:
                    text_content = tweet.get('text_content', '')
                    if text_content:
                        char_id_counter = self._extract_characters_from_text(
                            text=text_content,
                            source_info={
                                "source_type": "twitter",
                                "content_type": "tweet",
                                "query": query,
                                "tweet_id": tweet.get('id', ''),
                                "author": tweet.get('author_username', ''),
                                "file_name": twitter_file.name,
                                "file_path": str(twitter_file.relative_to(self.output_dir.parent))
                            },
                            all_characters=all_characters,
                            char_id_counter=char_id_counter
                        )

            except Exception as e:
                self.logger.error(f"处理TwitterFileFailed {twitter_file}: {e}")

        return char_id_counter

    def _extract_from_reddit_posts(self, posts_file: Path, all_characters: List, char_id_counter: int) -> int:
        """从Reddit帖子中提取字符"""
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data or 'posts' not in data:
                return char_id_counter

            subreddit = data.get('parsing_info', {}).get('subreddit', 'unknown')

            for post in data['posts']:
                # 提取标题字符
                if post.get('title'):
                    char_id_counter = self._extract_characters_from_text(
                        text=post['title'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "post_title",
                            "subreddit": subreddit,
                            "post_id": post.get('id', ''),
                            "file_name": posts_file.name,
                            "file_path": str(posts_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

                # 提取正文字符
                if post.get('selftext'):
                    char_id_counter = self._extract_characters_from_text(
                        text=post['selftext'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "post_content",
                            "subreddit": subreddit,
                            "post_id": post.get('id', ''),
                            "file_name": posts_file.name,
                            "file_path": str(posts_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            return char_id_counter

        except Exception as e:
            self.logger.error(f"处理Reddit帖子FileFailed {posts_file}: {e}")
            return char_id_counter

    def _extract_from_reddit_comments(self, comments_file: Path, all_characters: List, char_id_counter: int) -> int:
        """从Reddit评论中提取字符"""
        try:
            with open(comments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data or 'comments' not in data:
                return char_id_counter

            subreddit = data.get('parsing_info', {}).get('subreddit', 'unknown')

            for comment in data['comments']:
                if comment.get('body'):
                    char_id_counter = self._extract_characters_from_text(
                        text=comment['body'],
                        source_info={
                            "source_type": "reddit",
                            "content_type": "comment",
                            "subreddit": subreddit,
                            "comment_id": comment.get('id', ''),
                            "submission_id": comment.get('submission_id', ''),
                            "file_name": comments_file.name,
                            "file_path": str(comments_file.relative_to(self.output_dir.parent))
                        },
                        all_characters=all_characters,
                        char_id_counter=char_id_counter
                    )

            return char_id_counter

        except Exception as e:
            self.logger.error(f"处理Reddit评论FileFailed {comments_file}: {e}")
            return char_id_counter

    def _extract_characters_from_text(self, text: str, source_info: Dict, all_characters: List, char_id_counter: int) -> int:
        """从文本中提取字符（通用方法，支持多种数据源）"""
        source_type = source_info.get("source_type", "unknown")
        content_type = source_info.get("content_type", f"{source_type}_content")
        
        for position, char in enumerate(text):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "source_info": {
                    **source_info,
                    "string_value": text,
                    "string_length": len(text),
                    "field_type": content_type
                }
            }

            all_characters.append(char_info)
            char_id_counter += 1

        return char_id_counter

    def _extract_characters_from_string(self, string_value: str, entry: Dict, file_info: Dict, source_type: str, all_characters: List, char_id_counter: int) -> int:
        """从字符串中提取字符（通用方法）"""
        for position, char in enumerate(string_value):
            char_info = {
                "char_id": f"{source_type}_{char_id_counter:06d}",
                "character": char,
                "unicode_point": f"U+{ord(char):04X}",
                "position_in_string": position,
                "source_info": {
                    "source_type": source_type,
                    "field_type": entry.get('field_type', 'text'),
                    "string_value": string_value,
                    "string_length": len(string_value),
                    "file_name": file_info.get('file_name', ''),
                    "file_path": file_info.get('file_path', ''),
                    "context": entry.get('context', {})
                }
            }

            all_characters.append(char_info)
            char_id_counter += 1

        return char_id_counter
