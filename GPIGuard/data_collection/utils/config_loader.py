#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Config File Loader
Unified config file loading and management
"""

import json
from pathlib import Path
from typing import Dict, Any, Union

from .logger import setup_logger


class ConfigLoader:
    """Config File Loader"""
    
    def __init__(self):
        self.logger = setup_logger('ConfigLoader', console_output=False)
    
    def load_json_config(self, config_path: Union[str, Path], default_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load JSON config file
        
        Args:
            config_path: Config file path
            default_config: Default configuration (optional)
        
        Returns:
            Config dictionary
        """
        config_path = Path(config_path)
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Successfully loaded config: {config_path}")
                return config
            else:
                self.logger.warning(f"Config file not found: {config_path}")
                if default_config:
                    self.logger.info("Using default configuration")
                    return default_config
                return {}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file {config_path}: {e}")
            if default_config:
                return default_config
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_path}: {e}")
            if default_config:
                return default_config
            return {}
    
    def save_json_config(self, config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
        """
        Save JSON config file
        
        Args:
            config: Config dictionary
            config_path: Config file path
        
        Returns:
            Success status
        """
        config_path = Path(config_path)
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully saved config: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config file {config_path}: {e}")
            return False






















