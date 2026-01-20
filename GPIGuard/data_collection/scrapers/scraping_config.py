#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import random

# Import logger
from data_collection.utils.logger import setup_logger

class ScrapingConfig:
    """Web scraping configuration manager"""
    
    def __init__(self, config_file: Union[str, Path] = "web_scraping_config.json"):
        self.config_file = Path(config_file)
        self.logger = setup_logger('ScrapingConfig', console_output=False)
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scraping configuration file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Successfully loaded config file: {self.config_file}")
                return config
            else:
                self.logger.info("Config file does not exist, using default configuration")
                return self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
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
                "check_robots_txt": False,  # Simplified version temporarily disabled
                "avoid_honeypots": True,
                "max_concurrent_requests": 1,
                "blacklisted_domains": [
                    "facebook.com", "twitter.com", "instagram.com"
                ]
            }
        }
    
    def get_request_settings(self) -> Dict[str, Any]:
        """Get request settings"""
        return self.config.get("request_settings", {})
    
    def get_random_user_agent(self) -> str:
        """Get random User-Agent"""
        user_agents = self.config.get("user_agents", [])
        if user_agents:
            return random.choice(user_agents)
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def get_scraping_rules(self) -> Dict[str, Any]:
        """Get scraping rules"""
        return self.config.get("scraping_rules", {})
    
    def get_secondary_page_config(self) -> Dict[str, Any]:
        """Get secondary page discovery configuration"""
        return self.config.get("secondary_page_discovery", {})
    
    def get_content_extraction_config(self) -> Dict[str, Any]:
        """Get content extraction configuration"""
        return self.config.get("content_extraction", {})
    
    def get_output_settings(self) -> Dict[str, Any]:
        """Get output settings"""
        return self.config.get("output_settings", {})
    
    def get_safety_settings(self) -> Dict[str, Any]:
        """Get safety settings"""
        return self.config.get("safety_settings", {})
    
    def is_domain_blacklisted(self, domain: str) -> bool:
        """Check if domain is in blacklist"""
        blacklist = self.get_safety_settings().get("blacklisted_domains", [])
        domain_lower = domain.lower()
        
        for blocked_domain in blacklist:
            if blocked_domain.lower() in domain_lower:
                return True
        return False
    
    def should_extract_content_type(self, content_type: str) -> bool:
        """Check if should extract certain type of content"""
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
        """Get request delay time"""
        settings = self.get_request_settings()
        min_delay = settings.get("request_delay_min", 1)
        max_delay = settings.get("request_delay_max", 3)
        return random.uniform(min_delay, max_delay)
    
    def should_include_link(self, link_text: str, link_url: str) -> bool:
        """Determine if a link should be included"""
        secondary_config = self.get_secondary_page_config()
        
        # Check exclusion patterns
        exclude_patterns = secondary_config.get("exclude_patterns", [])
        link_text_lower = link_text.lower()
        link_url_lower = link_url.lower()
        
        for pattern in exclude_patterns:
            if pattern.lower() in link_text_lower or pattern.lower() in link_url_lower:
                return False
        
        # Check preferred patterns
        preferred_patterns = secondary_config.get("preferred_link_patterns", [])
        for pattern in preferred_patterns:
            if pattern.lower() in link_text_lower or pattern.lower() in link_url_lower:
                return True
        
        # Default strategy
        strategy = secondary_config.get("link_selection_strategy", "mixed")
        if strategy == "priority":
            return False  # Only select links matching preferred patterns
        
        return True  # mixed or random strategy accepts other links
    
    def save_config(self, output_file: Union[str, Path] = None) -> bool:
        """Save configuration to file"""
        try:
            output_file = Path(output_file) if output_file else self.config_file
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Config has been saved to: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update configuration setting"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            self.logger.info(f"Updated config: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        return {
            "total_user_agents": len(self.config.get("user_agents", [])),
            "max_sites_per_session": self.get_scraping_rules().get("max_sites_per_session", 0),
            "max_pages_per_site": self.get_scraping_rules().get("max_pages_per_site", 0),
            "blacklisted_domains": len(self.get_safety_settings().get("blacklisted_domains", [])),
            "preferred_link_patterns": len(self.get_secondary_page_config().get("preferred_link_patterns", [])),
            "safety_enabled": self.get_safety_settings().get("respect_robots_txt", False)
        }
    
    def print_config_summary(self):
        """Print configuration summary"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("🔧 Web Scraping Configuration Summary")
        print("="*50)
        print(f"🌐 Number of User-Agents: {stats['total_user_agents']}")
        print(f"📊 Max number of sites: {stats['max_sites_per_session']}")
        print(f"📄 Max pages per site: {stats['max_pages_per_site']}")
        print(f"🚫 Blacklisted domains: {stats['blacklisted_domains']} items")
        print(f"⭐ Preferred link patterns: {stats['preferred_link_patterns']} items")
        print(f"🛡️  Safety mode: {'Enabled' if stats['safety_enabled'] else 'Disabled'}")
        print("="*50)
