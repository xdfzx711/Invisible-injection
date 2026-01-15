#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import re
import html
import chardet

# 导入 logger
from data_collection.utils.logger import setup_logger

# 修复相对导入问题
try:
    from .scraping_config import ScrapingConfig
except ImportError:
    from scraping_config import ScrapingConfig

class HTMLExtractor:
    """HTML内容提取器"""
    
    def __init__(self, config: ScrapingConfig, output_dir: Union[str, Path] = "testscan_data"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('HTMLExtractor', console_output=False)
        
        # 创建Output directory - 修改为新的路径
        self.extracted_output_dir = self.output_dir / "parsed_data" / "html_analysis"
        self.extracted_output_dir.mkdir(parents=True, exist_ok=True)

    def _fix_encoding_and_decode_html(self, html_content: str, encoding: str = None) -> str:
        """修复编码并进行HTML实体解码"""
        try:
            # 如果内容是字符串，尝试检测和修复编码
            if isinstance(html_content, str):
                # 尝试将字符串编码为bytes再解码，修复编码问题
                try:
                    # 检测可能的编码问题
                    if encoding and encoding.lower() not in ['utf-8', 'utf8']:
                        # 尝试用原编码编码，再用UTF-8解码
                        bytes_content = html_content.encode('latin-1')
                        detected = chardet.detect(bytes_content)
                        if detected['encoding']:
                            html_content = bytes_content.decode(detected['encoding'])
                except (UnicodeError, LookupError):
                    # 如果编码转换Failed，保持原内容
                    pass

            # HTML实体解码
            html_content = html.unescape(html_content)

            return html_content

        except Exception as e:
            self.logger.warning(f"编码修复Failed: {e}")
            return html_content

    def _decode_html_entities(self, text: str) -> str:
        """HTML实体解码"""
        if not text:
            return text

        try:
            # 使用html.unescape进行HTML实体解码
            decoded_text = html.unescape(text)

            # 额外处理一些常见的实体
            entity_map = {
                '&nbsp;': ' ',
                '&ndash;': '–',
                '&mdash;': '—',
                '&laquo;': '«',
                '&raquo;': '»',
                '&hellip;': '…',
                '&copy;': '©',
                '&reg;': '®',
                '&trade;': '™'
            }

            for entity, char in entity_map.items():
                decoded_text = decoded_text.replace(entity, char)

            return decoded_text

        except Exception as e:
            self.logger.warning(f"HTML实体解码Failed: {e}")
            return text
    
    def extract_from_page_result(self, page_result: Dict[str, Any]) -> Dict[str, Any]:
        """从页面结果中提取内容"""
        
        self.logger.info(f"开始提取HTML内容: {page_result.get('url', 'unknown')}")
        
        try:
            from bs4 import BeautifulSoup
            
            html_content = page_result.get("html_content", "")
            if not html_content:
                return self._create_empty_result(page_result, "HTML内容为空")

            # 修复编码问题和HTML实体解码
            encoding = page_result.get("encoding", "utf-8")
            html_content = self._fix_encoding_and_decode_html(html_content, encoding)

            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取各种内容
            extraction_result = {
                "page_info": {
                    "url": page_result.get("url", ""),
                    "page_type": page_result.get("page_type", ""),
                    "website_name": page_result.get("website_info", {}).get("name", ""),
                    "website_info": page_result.get("website_info", {}),  # 添加完整的网站信息
                    "content_length": page_result.get("content_length", 0),
                    "encoding": page_result.get("encoding", "utf-8"),
                    "scrape_timestamp": page_result.get("scrape_timestamp", 0)
                },
                "extracted_content": {
                    "text_entries": [],
                    "meta_info": {},
                    "links": [],
                    "images": [],
                    "forms": []
                },
                "extraction_stats": {
                    "total_text_entries": 0,
                    "total_characters": 0,
                    "extraction_timestamp": time.time()
                }
            }
            
            # 提取meta信息
            if self.config.should_extract_content_type("meta"):
                extraction_result["extracted_content"]["meta_info"] = self._extract_meta_info(soup)
            
            # 提取文本内容
            if self.config.should_extract_content_type("text"):
                text_entries = self._extract_text_content(soup)
                extraction_result["extracted_content"]["text_entries"] = text_entries
                extraction_result["extraction_stats"]["total_text_entries"] = len(text_entries)
                extraction_result["extraction_stats"]["total_characters"] = sum(
                    len(entry.get("value", "")) for entry in text_entries
                )
            
            # 提取链接
            if self.config.should_extract_content_type("links"):
                extraction_result["extracted_content"]["links"] = self._extract_links(soup)
            
            # 提取图片
            if self.config.should_extract_content_type("images"):
                extraction_result["extracted_content"]["images"] = self._extract_images(soup)
            
            # 提取表单
            if self.config.should_extract_content_type("forms"):
                extraction_result["extracted_content"]["forms"] = self._extract_forms(soup)
            
            # 保存提取结果
            self._save_extraction_result(extraction_result)
            
            self.logger.info(f"HTML内容提取Completed: {extraction_result['extraction_stats']['total_text_entries']} 个文本entries目")
            
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"HTML内容提取Failed: {e}")
            return self._create_empty_result(page_result, f"提取Failed: {e}")
    
    def _extract_meta_info(self, soup) -> Dict[str, Any]:
        """提取meta信息"""
        
        meta_info = {}
        
        try:
            # 页面标题
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # HTML实体解码
                meta_info['title'] = self._decode_html_entities(title_text)

            # meta标签
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content = meta.get('content')

                if name and content:
                    # HTML实体解码
                    content = self._decode_html_entities(content)
                    meta_info[f'meta_{name}'] = content
            
            # 语言信息
            html_tag = soup.find('html')
            if html_tag:
                lang = html_tag.get('lang')
                if lang:
                    meta_info['language'] = lang
            
        except Exception as e:
            self.logger.error(f"提取meta信息Failed: {e}")
        
        return meta_info
    
    def _extract_text_content(self, soup) -> List[Dict[str, Any]]:
        """提取文本内容"""
        
        text_entries = []
        content_config = self.config.get_content_extraction_config()
        min_length = content_config.get("min_text_length", 10)
        max_length = content_config.get("max_text_length", 10000)
        
        try:
            # 定义要提取的HTML元素
            text_elements = [
                # 标题元素
                {'tag': 'h1', 'type': 'heading'},
                {'tag': 'h2', 'type': 'heading'},
                {'tag': 'h3', 'type': 'heading'},
                {'tag': 'h4', 'type': 'heading'},
                {'tag': 'h5', 'type': 'heading'},
                {'tag': 'h6', 'type': 'heading'},
                
                # 段落和文本
                {'tag': 'p', 'type': 'paragraph'},
                {'tag': 'div', 'type': 'div_text'},
                {'tag': 'span', 'type': 'span_text'},
                
                # 列表
                {'tag': 'li', 'type': 'list_item'},
                
                # 链接文本
                {'tag': 'a', 'type': 'link_text'},
                
                # 表格
                {'tag': 'td', 'type': 'table_cell'},
                {'tag': 'th', 'type': 'table_header'},
                
                # 表单元素
                {'tag': 'label', 'type': 'form_label'},
                {'tag': 'button', 'type': 'button_text'},
                
                # 其他
                {'tag': 'strong', 'type': 'strong_text'},
                {'tag': 'em', 'type': 'emphasis_text'},
                {'tag': 'blockquote', 'type': 'quote'}
            ]
            
            for element_def in text_elements:
                tag_name = element_def['tag']
                element_type = element_def['type']
                
                elements = soup.find_all(tag_name)
                
                for i, element in enumerate(elements):
                    text_content = element.get_text(strip=True)
                    # HTML实体解码
                    text_content = self._decode_html_entities(text_content)

                    if text_content and min_length <= len(text_content) <= max_length:
                        
                        # 获取元素属性
                        attributes = {}
                        for attr_name in ['class', 'id', 'title', 'alt', 'placeholder']:
                            attr_value = element.get(attr_name)
                            if attr_value:
                                if isinstance(attr_value, list):
                                    attributes[attr_name] = ' '.join(attr_value)
                                else:
                                    attributes[attr_name] = str(attr_value)
                        
                        # 生成XPath（简化版）
                        xpath = self._generate_simple_xpath(element, tag_name, i)
                        
                        text_entry = {
                            "element_type": element_type,
                            "tag_name": tag_name,
                            "value": text_content,
                            "length": len(text_content),
                            "xpath": xpath,
                            "attributes": attributes,
                            "field_type": "text"  # 简化实现，可以后续增强
                        }
                        
                        text_entries.append(text_entry)
            
            # 去重相似的文本entries目
            text_entries = self._deduplicate_text_entries(text_entries)
            
        except Exception as e:
            self.logger.error(f"提取文本内容Failed: {e}")
        
        return text_entries
    
    def _extract_links(self, soup) -> List[Dict[str, Any]]:
        """提取链接信息"""
        
        links = []
        
        try:
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '').strip()
                link_text = link.get_text(strip=True)
                title = link.get('title', '')

                # HTML实体解码
                link_text = self._decode_html_entities(link_text)
                title = self._decode_html_entities(title)

                if href and link_text:
                    links.append({
                        "url": href,
                        "text": link_text,
                        "title": title,
                        "length": len(link_text)
                    })
        
        except Exception as e:
            self.logger.error(f"提取链接Failed: {e}")
        
        return links
    
    def _extract_images(self, soup) -> List[Dict[str, Any]]:
        """提取图片信息"""
        
        images = []
        
        try:
            img_elements = soup.find_all('img')
            
            for img in img_elements:
                src = img.get('src', '').strip()
                alt = img.get('alt', '').strip()
                title = img.get('title', '').strip()

                # HTML实体解码
                alt = self._decode_html_entities(alt)
                title = self._decode_html_entities(title)

                if src:
                    images.append({
                        "src": src,
                        "alt": alt,
                        "title": title,
                        "alt_length": len(alt) if alt else 0
                    })
        
        except Exception as e:
            self.logger.error(f"提取图片Failed: {e}")
        
        return images
    
    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        """提取表单信息"""
        
        forms = []
        
        try:
            form_elements = soup.find_all('form')
            
            for form in form_elements:
                form_data = {
                    "action": form.get('action', ''),
                    "method": form.get('method', 'get'),
                    "inputs": []
                }
                
                # 提取表单输入字段
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_elem in inputs:
                    placeholder = input_elem.get('placeholder', '')
                    value = input_elem.get('value', '')

                    # HTML实体解码
                    placeholder = self._decode_html_entities(placeholder)
                    value = self._decode_html_entities(value)

                    input_data = {
                        "tag": input_elem.name,
                        "type": input_elem.get('type', ''),
                        "name": input_elem.get('name', ''),
                        "placeholder": placeholder,
                        "value": value
                    }
                    form_data["inputs"].append(input_data)
                
                forms.append(form_data)
        
        except Exception as e:
            self.logger.error(f"提取表单Failed: {e}")
        
        return forms
    
    def _generate_simple_xpath(self, element, tag_name: str, index: int) -> str:
        """生成简化的XPath"""
        try:
            # 简化版XPath，只包含标签名和索引
            return f"//{tag_name}[{index + 1}]"
        except:
            return f"//{tag_name}"
    
    def _deduplicate_text_entries(self, text_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重相似的文本entries目"""
        
        unique_entries = []
        seen_texts = set()
        
        for entry in text_entries:
            text_value = entry.get("value", "").strip()
            
            # 简单去重：相同文本只保留一个
            if text_value and text_value not in seen_texts:
                seen_texts.add(text_value)
                unique_entries.append(entry)
        
        return unique_entries
    
    def _save_extraction_result(self, extraction_result: Dict[str, Any]):
        """保存提取结果"""

        try:
            page_info = extraction_result.get("page_info", {})
            website_name = page_info.get("website_name", "unknown")
            page_type = page_info.get("page_type", "unknown")
            timestamp = int(page_info.get("scrape_timestamp", time.time()))

            # 获取网站排名/编号，用于File命名
            website_info = page_info.get("website_info", {})
            rank = website_info.get("rank", 0)
            source_row = website_info.get("source_row", 0)

            # 使用排名或行号作为编号
            site_number = rank if rank > 0 else source_row

            # 创建基于编号的File名
            # 清理File名，移除非法字符
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', website_name)

            # 格式：编号_网站名_页面类型_时间戳_extracted.json
            filename = f"{site_number:06d}_{safe_name}_{page_type}_{timestamp}_extracted.json"
            file_path = self.extracted_output_dir / filename

            # 保存提取结果
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_result, f, ensure_ascii=False, indent=2)

            # 更新提取结果中的File路径
            extraction_result["saved_extraction_path"] = str(file_path)

            self.logger.debug(f"提取结果has been保存: {file_path}")

        except Exception as e:
            self.logger.error(f"保存提取结果Failed: {e}")
    
    def _create_empty_result(self, page_result: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """创建空的提取结果"""
        
        return {
            "page_info": {
                "url": page_result.get("url", ""),
                "page_type": page_result.get("page_type", ""),
                "website_name": page_result.get("website_info", {}).get("name", ""),
                "error": error_message
            },
            "extracted_content": {
                "text_entries": [],
                "meta_info": {},
                "links": [],
                "images": [],
                "forms": []
            },
            "extraction_stats": {
                "total_text_entries": 0,
                "total_characters": 0,
                "extraction_timestamp": time.time()
            }
        }

    def extract_from_html_file(self, html_file_path: Union[str, Path],
                              output_filename: str = None) -> Dict[str, Any]:
        """直接从HTMLFile提取内容"""

        html_file_path = Path(html_file_path)

        if not html_file_path.exists():
            self.logger.error(f"HTMLFile不exists: {html_file_path}")
            return self._create_empty_result({}, f"HTMLFile不exists: {html_file_path}")

        self.logger.info(f"开始从HTMLFile提取内容: {html_file_path.name}")

        try:
            # 读取HTMLFile
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 如果没有指定输出File名，使用原始File名
            if output_filename is None:
                output_filename = html_file_path.stem

            # 创建页面结果结构
            page_result = {
                "url": f"file://{html_file_path.absolute()}",
                "page_type": "local_file",
                "html_content": html_content,
                "content_length": len(html_content),
                "encoding": "utf-8",
                "scrape_timestamp": int(html_file_path.stat().st_mtime),
                "website_info": {
                    "name": output_filename,
                    "source": "local_file",
                    "file_path": str(html_file_path)
                }
            }

            # 临时保存原始的保存方法
            original_save_method = self._save_extraction_result

            # 创建自定义保存方法
            def custom_save_method(extraction_result):
                try:
                    # 使用指定的File名
                    filename = f"{output_filename}_extracted.json"
                    file_path = self.extracted_output_dir / filename

                    # 保存提取结果
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(extraction_result, f, ensure_ascii=False, indent=2)

                    # 更新提取结果中的File路径
                    extraction_result["saved_extraction_path"] = str(file_path)

                    self.logger.debug(f"提取结果has been保存: {file_path}")

                except Exception as e:
                    self.logger.error(f"保存提取结果Failed: {e}")

            # 临时替换保存方法
            self._save_extraction_result = custom_save_method

            try:
                # 使用现有的提取方法
                extraction_result = self.extract_from_page_result(page_result)

                # 更新页面信息以反映这是从本地File提取的
                if "page_info" in extraction_result:
                    extraction_result["page_info"]["source_type"] = "local_html_file"
                    extraction_result["page_info"]["original_file"] = str(html_file_path)

                return extraction_result

            finally:
                # 恢复原始的保存方法
                self._save_extraction_result = original_save_method

        except Exception as e:
            self.logger.error(f"从HTMLFile提取内容Failed: {e}")
            return self._create_empty_result({}, f"提取Failed: {e}")
