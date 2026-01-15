#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import random

# 导入 logger
from data_collection.utils.logger import setup_logger

class ScrapingConfig:
    """网页爬取配置管理器"""
    
    def __init__(self, config_file: Union[str, Path] = "web_scraping_config.json"):
        self.config_file = Path(config_file)
        self.logger = setup_logger('ScrapingConfig', console_output=False)
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载爬取配置File"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置File: {self.config_file}")
                return config
            else:
                self.logger.info("配置File不exists，使用默认配置")
                return self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"加载配置FileFailed: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "request_settings": {
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 2,
                "request_delay_min": 1,
                "request_delay_max": 3,
                "max_redirects": 5
            },
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
            ],
            "scraping_rules": {
                "max_sites_per_session": 50,
                "max_pages_per_site": 5,
                "include_homepage": True,
                "include_secondary_pages": True,
                "max_page_size_mb": 10,
                "skip_binary_files": True
            },
            "secondary_page_discovery": {
                "max_links_to_check": 20,
                "preferred_link_patterns": [
                    "about", "contact", "help", "support", "news", "blog",
                    "products", "services", "company", "team", "careers"
                ],
                "exclude_patterns": [
                    "login", "register", "download", "pdf", "zip", "exe",
                    "facebook.com", "twitter.com", "instagram.com", "linkedin.com"
                ],
                "link_selection_strategy": "mixed"  # random, priority, mixed
            },
            "content_extraction": {
                "extract_text": True,
                "extract_links": True,
                "extract_images": True,
                "extract_forms": True,
                "extract_meta": True,
                "extract_scripts": False,
                "min_text_length": 10,
                "max_text_length": 10000
            },
            "output_settings": {
                "save_raw_html": True,
                "save_extracted_content": True,
                "output_format": "json",
                "compress_html": False,
                "create_summary_report": True
            },
            "safety_settings": {
                "respect_robots_txt": True,
                "check_robots_txt": False,  # 简化版本暂时关闭
                "avoid_honeypots": True,
                "max_concurrent_requests": 1,
                "blacklisted_domains": [
                    "facebook.com", "twitter.com", "instagram.com"
                ]
            }
        }
    
    def get_request_settings(self) -> Dict[str, Any]:
        """获取请求设置"""
        return self.config.get("request_settings", {})
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = self.config.get("user_agents", [])
        if user_agents:
            return random.choice(user_agents)
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def get_scraping_rules(self) -> Dict[str, Any]:
        """获取爬取规则"""
        return self.config.get("scraping_rules", {})
    
    def get_secondary_page_config(self) -> Dict[str, Any]:
        """获取二级页面发现配置"""
        return self.config.get("secondary_page_discovery", {})
    
    def get_content_extraction_config(self) -> Dict[str, Any]:
        """获取内容提取配置"""
        return self.config.get("content_extraction", {})
    
    def get_output_settings(self) -> Dict[str, Any]:
        """获取输出设置"""
        return self.config.get("output_settings", {})
    
    def get_safety_settings(self) -> Dict[str, Any]:
        """获取安全设置"""
        return self.config.get("safety_settings", {})
    
    def is_domain_blacklisted(self, domain: str) -> bool:
        """Check域名是否在黑名单中"""
        blacklist = self.get_safety_settings().get("blacklisted_domains", [])
        domain_lower = domain.lower()
        
        for blocked_domain in blacklist:
            if blocked_domain.lower() in domain_lower:
                return True
        return False
    
    def should_extract_content_type(self, content_type: str) -> bool:
        """Check是否应该提取某种类型的内容"""
        extraction_config = self.get_content_extraction_config()
        
        type_mapping = {
            "text": "extract_text",
            "links": "extract_links", 
            "images": "extract_images",
            "forms": "extract_forms",
            "meta": "extract_meta",
            "scripts": "extract_scripts"
        }
        
        setting_key = type_mapping.get(content_type)
        if setting_key:
            return extraction_config.get(setting_key, True)
        
        return True
    
    def get_request_delay(self) -> float:
        """获取请求延迟时间"""
        settings = self.get_request_settings()
        min_delay = settings.get("request_delay_min", 1)
        max_delay = settings.get("request_delay_max", 3)
        return random.uniform(min_delay, max_delay)
    
    def should_include_link(self, link_text: str, link_url: str) -> bool:
        """判断是否应该包含某个链接"""
        secondary_config = self.get_secondary_page_config()
        
        # Check排除模式
        exclude_patterns = secondary_config.get("exclude_patterns", [])
        link_text_lower = link_text.lower()
        link_url_lower = link_url.lower()
        
        for pattern in exclude_patterns:
            if pattern.lower() in link_text_lower or pattern.lower() in link_url_lower:
                return False
        
        # Check优先模式
        preferred_patterns = secondary_config.get("preferred_link_patterns", [])
        for pattern in preferred_patterns:
            if pattern.lower() in link_text_lower or pattern.lower() in link_url_lower:
                return True
        
        # 默认策略
        strategy = secondary_config.get("link_selection_strategy", "mixed")
        if strategy == "priority":
            return False  # 只选择优先模式匹配的链接
        
        return True  # mixed或random策略接受其他链接
    
    def save_config(self, output_file: Union[str, Path] = None) -> bool:
        """保存配置到File"""
        try:
            output_file = Path(output_file) if output_file else self.config_file
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置has been保存到: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置Failed: {e}")
            return False
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """更新配置设置"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            self.logger.info(f"更新配置: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置Failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取配置Statistics"""
        return {
            "total_user_agents": len(self.config.get("user_agents", [])),
            "max_sites_per_session": self.get_scraping_rules().get("max_sites_per_session", 0),
            "max_pages_per_site": self.get_scraping_rules().get("max_pages_per_site", 0),
            "blacklisted_domains": len(self.get_safety_settings().get("blacklisted_domains", [])),
            "preferred_link_patterns": len(self.get_secondary_page_config().get("preferred_link_patterns", [])),
            "safety_enabled": self.get_safety_settings().get("respect_robots_txt", False)
        }
    
    def print_config_summary(self):
        """打印配置摘要"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("🔧 网页爬取配置摘要")
        print("="*50)
        print(f"🌐 User-Agent数量: {stats['total_user_agents']}")
        print(f"📊 最大网站数: {stats['max_sites_per_session']}")
        print(f"📄 每站最大页面数: {stats['max_pages_per_site']}")
        print(f"🚫 黑名单域名: {stats['blacklisted_domains']} 个")
        print(f"⭐ 优先链接模式: {stats['preferred_link_patterns']} 个")
        print(f"🛡️  安全模式: {'启用' if stats['safety_enabled'] else '禁用'}")
        print("="*50)
