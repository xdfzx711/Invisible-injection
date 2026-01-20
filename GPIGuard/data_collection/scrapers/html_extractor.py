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


from data_collection.utils.logger import setup_logger


try:
    from .scraping_config import ScrapingConfig
except ImportError:
    from scraping_config import ScrapingConfig

class HTMLExtractor:

    
    def __init__(self, config: ScrapingConfig, output_dir: Union[str, Path] = "testscan_data"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('HTMLExtractor', console_output=False)
        

        self.extracted_output_dir = self.output_dir / "parsed_data" / "html_analysis"
        self.extracted_output_dir.mkdir(parents=True, exist_ok=True)

    def _fix_encoding_and_decode_html(self, html_content: str, encoding: str = None) -> str:

        try:

            if isinstance(html_content, str):
    
                try:
                
                    if encoding and encoding.lower() not in ['utf-8', 'utf8']:
                 
                        bytes_content = html_content.encode('latin-1')
                        detected = chardet.detect(bytes_content)
                        if detected['encoding']:
                            html_content = bytes_content.decode(detected['encoding'])
                except (UnicodeError, LookupError):
                 
                    pass

            html_content = html.unescape(html_content)

            return html_content

        except Exception as e:
            self.logger.warning(f"Encoding fix failed: {e}")
            return html_content

    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities"""
        if not text:
            return text

        try:
            # Use html.unescape to decode HTML entities
            decoded_text = html.unescape(text)

            # Additional handling for common entities
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
            self.logger.warning(f"HTML entity decoding failed: {e}")
            return text
    
    def extract_from_page_result(self, page_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from page result"""
        
        self.logger.info(f"Starting to extract HTML content: {page_result.get('url', 'unknown')}")
        
        try:
            from bs4 import BeautifulSoup
            
            html_content = page_result.get("html_content", "")
            if not html_content:
                return self._create_empty_result(page_result, "HTML content is empty")

            # Fix encoding issues and decode HTML entities
            encoding = page_result.get("encoding", "utf-8")
            html_content = self._fix_encoding_and_decode_html(html_content, encoding)

            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract various types of content
            extraction_result = {
                "page_info": {
                    "url": page_result.get("url", ""),
                    "page_type": page_result.get("page_type", ""),
                    "website_name": page_result.get("website_info", {}).get("name", ""),
                    "website_info": page_result.get("website_info", {}),  # Add complete website information
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
            
            # Extract meta information
            if self.config.should_extract_content_type("meta"):
                extraction_result["extracted_content"]["meta_info"] = self._extract_meta_info(soup)
            
            # Extract text content
            if self.config.should_extract_content_type("text"):
                text_entries = self._extract_text_content(soup)
                extraction_result["extracted_content"]["text_entries"] = text_entries
                extraction_result["extraction_stats"]["total_text_entries"] = len(text_entries)
                extraction_result["extraction_stats"]["total_characters"] = sum(
                    len(entry.get("value", "")) for entry in text_entries
                )
            
            # Extract links
            if self.config.should_extract_content_type("links"):
                extraction_result["extracted_content"]["links"] = self._extract_links(soup)
            
            # Extract images
            if self.config.should_extract_content_type("images"):
                extraction_result["extracted_content"]["images"] = self._extract_images(soup)
            
            # Extract forms
            if self.config.should_extract_content_type("forms"):
                extraction_result["extracted_content"]["forms"] = self._extract_forms(soup)
            
            # Save extraction result
            self._save_extraction_result(extraction_result)
            
            self.logger.info(f"HTML content extraction completed: {extraction_result['extraction_stats']['total_text_entries']} text entries")
            
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"HTML content extraction failed: {e}")
            return self._create_empty_result(page_result, f"Extraction failed: {e}")
    
    def _extract_meta_info(self, soup) -> Dict[str, Any]:
        """Extract meta information"""
        
        meta_info = {}
        
        try:
            # Page title
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
        
                meta_info['title'] = self._decode_html_entities(title_text)

            # Meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content = meta.get('content')

                if name and content:
           
                    content = self._decode_html_entities(content)
                    meta_info[f'meta_{name}'] = content
            
            # Language information
            html_tag = soup.find('html')
            if html_tag:
                lang = html_tag.get('lang')
                if lang:
                    meta_info['language'] = lang
            
        except Exception as e:
            self.logger.error(f"Failed to extract meta information: {e}")
        
        return meta_info
    
    def _extract_text_content(self, soup) -> List[Dict[str, Any]]:
        """Extract text content"""
        
        text_entries = []
        content_config = self.config.get_content_extraction_config()
        min_length = content_config.get("min_text_length", 10)
        max_length = content_config.get("max_text_length", 10000)
        
        try:
            # Define HTML elements to extract
            text_elements = [
                # Heading elements
                {'tag': 'h1', 'type': 'heading'},
                {'tag': 'h2', 'type': 'heading'},
                {'tag': 'h3', 'type': 'heading'},
                {'tag': 'h4', 'type': 'heading'},
                {'tag': 'h5', 'type': 'heading'},
                {'tag': 'h6', 'type': 'heading'},
                
                # Paragraphs and text
                {'tag': 'p', 'type': 'paragraph'},
                {'tag': 'div', 'type': 'div_text'},
                {'tag': 'span', 'type': 'span_text'},
                
                # Lists
                {'tag': 'li', 'type': 'list_item'},
                
                # Link text
                {'tag': 'a', 'type': 'link_text'},
                
                # Table
                {'tag': 'td', 'type': 'table_cell'},
                {'tag': 'th', 'type': 'table_header'},
                
                # Form elements
                {'tag': 'label', 'type': 'form_label'},
                {'tag': 'button', 'type': 'button_text'},
                
                # Other
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
                   
                    text_content = self._decode_html_entities(text_content)

                    if text_content and min_length <= len(text_content) <= max_length:
                        
                  
                        attributes = {}
                        for attr_name in ['class', 'id', 'title', 'alt', 'placeholder']:
                            attr_value = element.get(attr_name)
                            if attr_value:
                                if isinstance(attr_value, list):
                                    attributes[attr_name] = ' '.join(attr_value)
                                else:
                                    attributes[attr_name] = str(attr_value)
                        
                  Generate XPath (simplified version)
                        xpath = self._generate_simple_xpath(element, tag_name, i)
                        
                        text_entry = {
                            "element_type": element_type,
                            "tag_name": tag_name,
                            "value": text_content,
                            "length": len(text_content),
                            "xpath": xpath,
                            "attributes": attributes,
                            "field_type": "text"  # Simplified implementation, can be enhanced later
                        }
                        
                        text_entries.append(text_entry)
            
            # Deduplicate similar text entries
            text_entries = self._deduplicate_text_entries(text_entries)
            
        except Exception as e:
            self.logger.error(f"Failed to extract text content: {e}")
        
        return text_entries
    
    def _extract_links(self, soup) -> List[Dict[str, Any]]:
        """Extract link information"""
        
        links = []
        
        try:
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '').strip()
                link_text = link.get_text(strip=True)
                title = link.get('title', '')

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
            self.logger.error(f"Failed to extract links: {e}")
        
        return links
    
    def _extract_images(self, soup) -> List[Dict[str, Any]]:
        """Extract image information"""
        
        images = []
        
        try:
            img_elements = soup.find_all('img')
            
            for img in img_elements:
                src = img.get('src', '').strip()
                alt = img.get('alt', '').strip()
                title = img.get('title', '').strip()

                # Decode HTML entities
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
            self.logger.error(f"Failed to extract images: {e}")
        
        return images
    
    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        """Extract form information"""
        
        forms = []
        
        try:
            form_elements = soup.find_all('form')
            
            for form in form_elements:
                form_data = {
                    "action": form.get('action', ''),
                    "method": form.get('method', 'get'),
                    "inputs": []
                }
                
                # Extract form input fields
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_elem in inputs:
                    placeholder = input_elem.get('placeholder', '')
                    value = input_elem.get('value', '')

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
            self.logger.error(f"Failed to extract forms: {e}")
        
        return forms
    
    def _generate_simple_xpath(self, element, tag_name: str, index: int) -> str:
        """Generate simplified XPath"""
        try:
            # Simplified XPath, contains only tag name and index
            return f"//{tag_name}[{index + 1}]"
        except:
            return f"//{tag_name}"
    
    def _deduplicate_text_entries(self, text_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate similar text entries"""
        
        unique_entries = []
        seen_texts = set()
        
        for entry in text_entries:
            text_value = entry.get("value", "").strip()
            
            # Simple deduplication: keep only one for duplicate text
            if text_value and text_value not in seen_texts:
                seen_texts.add(text_value)
                unique_entries.append(entry)
        
        return unique_entries
    
    def _save_extraction_result(self, extraction_result: Dict[str, Any]):
        """Save extraction result"""

        try:
            page_info = extraction_result.get("page_info", {})
            website_name = page_info.get("website_name", "unknown")
            page_type = page_info.get("page_type", "unknown")
            timestamp = int(page_info.get("scrape_timestamp", time.time()))

            website_info = page_info.get("website_info", {})
            rank = website_info.get("rank", 0)
            source_row = website_info.get("source_row", 0)

            site_number = rank if rank > 0 else source_row

            # Create filename based on number
            # Clean filename, remove illegal characters
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', website_name)

            # Format: number_website_name_page_type_timestamp_extracted.json
            filename = f"{site_number:06d}_{safe_name}_{page_type}_{timestamp}_extracted.json"
            file_path = self.extracted_output_dir / filename

            # Save extraction result
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_result, f, ensure_ascii=False, indent=2)

            # Update file path in extraction result
            extraction_result["saved_extraction_path"] = str(file_path)

            self.logger.debug(f"Extraction result has been saved: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save extraction result: {e}")
    
    def _create_empty_result(self, page_result: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Create empty extraction result"""
        
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
        """Extract content directly from HTML file"""

        html_file_path = Path(html_file_path)

        if not html_file_path.exists():
            self.logger.error(f"HTML file does not exist: {html_file_path}")
            return self._create_empty_result({}, f"HTML file does not exist: {html_file_path}")

        self.logger.info(f"Starting to extract content from HTML file: {html_file_path.name}")

        try:
            # Read HTML file
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # If no output filename specified, use original filename
            if output_filename is None:
                output_filename = html_file_path.stem

            # Create page result structure
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

            # Temporarily save original save method
            original_save_method = self._save_extraction_result

            # Create custom save method
            def custom_save_method(extraction_result):
                try:
                    # Use specified filename
                    filename = f"{output_filename}_extracted.json"
                    file_path = self.extracted_output_dir / filename

                    # Save extraction result
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(extraction_result, f, ensure_ascii=False, indent=2)

                    # Update file path in extraction result
                    extraction_result["saved_extraction_path"] = str(file_path)

                    self.logger.debug(f"Extraction result has been saved: {file_path}")

                except Exception as e:
                    self.logger.error(f"Failed to save extraction result: {e}")

            # Temporarily replace save method
            self._save_extraction_result = custom_save_method

            try:
                # Use existing extraction method
                extraction_result = self.extract_from_page_result(page_result)

                # Update page info to reflect that it is extracted from local file
                if "page_info" in extraction_result:
                    extraction_result["page_info"]["source_type"] = "local_html_file"
                    extraction_result["page_info"]["original_file"] = str(html_file_path)

                return extraction_result

            finally:
                # Restore original save method
                self._save_extraction_result = original_save_method

        except Exception as e:
            self.logger.error(f"Failed to extract content from HTML file: {e}")
            return self._create_empty_result({}, f"Extraction failed: {e}")
