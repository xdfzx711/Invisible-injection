#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一配置管理器
管理所有收集器的配置File
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import setup_logger
from .path_manager import PathManager


class ConfigManager:
    """统一配置管理器 - Singleton Pattern"""
    
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
        
        # 配置缓存
        self._config_cache = {}
        
        self._initialized = True
    
    def get_config(self, config_name: str, fallback_paths: list = None) -> Optional[Dict[str, Any]]:
        """
        获取配置File
        
        Args:
            config_name: 配置File名（如：reddit_config.json）
            fallback_paths: 备用路径列表（按优先级）
        
        Returns:
            配置字典，如果不exists返回None
        """
        # Check缓存
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # 优先从新Configuration directory读取
        config_path = self.config_dir / config_name
        
        if config_path.exists():
            config = self._load_json(config_path)
            if config:
                self._config_cache[config_name] = config
                self.logger.info(f"Loaded config from new location: {config_path}")
                return config
        
        # 尝试备用路径
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
        保存配置File
        
        Args:
            config_name: 配置File名
            config: 配置字典
        
        Returns:
            是否成功
        """
        config_path = self.config_dir / config_name
        
        try:
            # 确保directoryexists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            self._config_cache[config_name] = config
            
            self.logger.info(f"Saved config: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config {config_name}: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any], required_keys: list) -> bool:
        """
        验证配置是否包含必需的键
        
        Args:
            config: 配置字典
            required_keys: 必需的键列表
        
        Returns:
            是否有效
        """
        if not config:
            return False
        
        for key in required_keys:
            if key not in config or not config[key]:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        return True
    
    def get_web_scraping_config(self) -> Dict[str, Any]:
        """获取HTML爬取配置"""
        config = self.get_config(
            'web_scraping_config.json',
            fallback_paths=['web_scraping_config.json']
        )
        
        # 如果没有配置，返回默认配置
        if not config:
            return self._get_default_web_scraping_config()
        
        return config
    
    def get_reddit_config(self) -> Dict[str, Any]:
        """获取Reddit配置"""
        return self.get_config(
            'reddit_config.json',
            fallback_paths=['reddit_collect/reddit_config.json']
        )
    
    def get_twitter_config(self) -> Dict[str, Any]:
        """获取Twitter配置"""
        return self.get_config(
            'twitter_config.json',
            fallback_paths=['twitter_collect/twitter_config.json']
        )
    
    def _load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSONFile"""
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
        """获取默认HTML爬取配置"""
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
        """清除配置缓存"""
        self._config_cache = {}
        self.logger.info("Config cache cleared")
    
    def reload_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        重新加载配置File
        
        Args:
            config_name: 配置File名
        
        Returns:
            新的配置字典
        """
        # 清除该配置的缓存
        if config_name in self._config_cache:
            del self._config_cache[config_name]
        
        # 重新加载
        return self.get_config(config_name)
    
    def list_configs(self) -> list:
        """列出所有可用的配置File"""
        config_files = []
        
        if self.config_dir.exists():
            for file in self.config_dir.glob('*.json'):
                if not file.name.endswith('.example'):
                    config_files.append(file.name)
        
        return sorted(config_files)
    
    def __repr__(self):
        return f"ConfigManager(config_dir={self.config_dir}, cached_configs={list(self._config_cache.keys())})"






















