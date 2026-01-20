#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Config Manager
Manage config files for all collectors
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import setup_logger
from .path_manager import PathManager


class ConfigManager:
    """Unified Config Manager - Singleton Pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = setup_logger('ConfigManager', console_output=False)
        self.path_manager = PathManager()
        self.config_dir = self.path_manager.get_config_dir()
        
        # Config cache
        self._config_cache = {}
        
        self._initialized = True
    
    def get_config(self, config_name: str, fallback_paths: list = None) -> Optional[Dict[str, Any]]:
        """
        Get config file
        
        Args:
            config_name: Config file name (e.g.: reddit_config.json)
            fallback_paths: Fallback paths list (by priority)
        
        Returns:
            Config dictionary, None if not exists
        """
        # Check cache
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # Load from config directory first
        config_path = self.config_dir / config_name
        
        if config_path.exists():
            config = self._load_json(config_path)
            if config:
                self._config_cache[config_name] = config
                self.logger.info(f"Loaded config from new location: {config_path}")
                return config
        
        # Try fallback paths
        if fallback_paths:
            for fallback_path in fallback_paths:
                fallback_full = self.path_manager.get_project_root() / fallback_path
                if fallback_full.exists():
                    config = self._load_json(fallback_full)
                    if config:
                        self._config_cache[config_name] = config
                        self.logger.info(f"Loaded config from fallback: {fallback_full}")
                        return config
        
        self.logger.warning(f"Config file not found: {config_name}")
        return None
    
    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        Save config file
        
        Args:
            config_name: Config file name
            config: Config dictionary
        
        Returns:
            Success status
        """
        config_path = self.config_dir / config_name
        
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Update cache
            self._config_cache[config_name] = config
            
            self.logger.info(f"Saved config: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config {config_name}: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate if config contains required keys
        
        Args:
            config: Config dictionary
            required_keys: Required keys list
        
        Returns:
            Validity status
        """
        if not config:
            return False
        
        for key in required_keys:
            if key not in config or not config[key]:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        return True
    
    def get_web_scraping_config(self) -> Dict[str, Any]:
        """Get web scraping config"""
        config = self.get_config(
            'web_scraping_config.json',
            fallback_paths=['web_scraping_config.json']
        )
        
        # If no config exists, return default config
        if not config:
            return self._get_default_web_scraping_config()
        
        return config
    
    def get_reddit_config(self) -> Dict[str, Any]:
        """Get Reddit config"""
        return self.get_config(
            'reddit_config.json',
            fallback_paths=['reddit_collect/reddit_config.json']
        )
    
    def get_twitter_config(self) -> Dict[str, Any]:
        """Get Twitter config"""
        return self.get_config(
            'twitter_config.json',
            fallback_paths=['twitter_collect/twitter_config.json']
        )
    
    def _load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load {file_path}: {e}")
            return None
    
    def _get_default_web_scraping_config(self) -> Dict[str, Any]:
        """Get default web scraping config"""
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
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            "scraping_rules": {
                "max_sites_per_session": 50,
                "max_pages_per_site": 5,
                "include_homepage": True,
                "include_secondary_pages": True,
                "max_page_size_mb": 10,
                "skip_binary_files": True
            },
            "content_extraction": {
                "extract_text": True,
                "extract_links": True,
                "extract_images": True,
                "extract_forms": True,
                "extract_meta": True,
                "min_text_length": 10,
                "max_text_length": 10000
            },
            "output_settings": {
                "save_raw_html": True,
                "save_extracted_content": True,
                "output_format": "json",
                "compress_html": False,
                "create_summary_report": True
            }
        }
    
    def clear_cache(self):
        """Clear config cache"""
        self._config_cache = {}
        self.logger.info("Config cache cleared")
    
    def reload_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Reload config file
        
        Args:
            config_name: Config file name
        
        Returns:
            New config dictionary
        """
        # Clear cache for this config
        if config_name in self._config_cache:
            del self._config_cache[config_name]
        
        # Reload
        return self.get_config(config_name)
    
    def list_configs(self) -> list:
        """List all available config files"""
        config_files = []
        
        if self.config_dir.exists():
            for file in self.config_dir.glob('*.json'):
                if not file.name.endswith('.example'):
                    config_files.append(file.name)
        
        return sorted(config_files)
    
    def __repr__(self):
        return f"ConfigManager(config_dir={self.config_dir}, cached_configs={list(self._config_cache.keys())})"






















