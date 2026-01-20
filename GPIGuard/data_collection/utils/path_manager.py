#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Path Manager
Solve path confusion problem, provide unified path access interface
"""

from pathlib import Path
from typing import Optional


class PathManager:
    """Path Manager - Singleton Pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Project root directory (testscan directory)
        self.project_root = self._find_project_root()
        
        # Main directories
        self.data_root = self.project_root / "testscan_data"
        self.origin_data_dir = self.data_root / "origin_data"
        self.parsed_data_dir = self.data_root / "parsed_data"
        self.unicode_analysis_dir = self.data_root / "unicode_analysis"
        
        # Configuration directory
        self.config_dir = self.project_root / "data_collection" / "config"
        
        # Log directory
        self.log_dir = self.project_root / "log"
        
        self._initialized = True
    
    def _find_project_root(self) -> Path:
        """Find project root directory"""
        current = Path(__file__).resolve()
        
        # Search upward until finding directory containing testscan_data
        for parent in current.parents:
            if (parent / "testscan_data").exists():
                return parent
        
        # If not found, assume standard location
        # data_collection/utils/path_manager.py -> ../../
        return current.parent.parent.parent
    
    def get_origin_data_dir(self, data_type: Optional[str] = None) -> Path:
        """
        Get origin data directory
        
        Args:
            data_type: Data type (html, json, csv, xml, reddit, twitter)
        
        Returns:
            Origin data directory path
        """
        if data_type:
            return self.origin_data_dir / data_type
        return self.origin_data_dir
    
    def get_parsed_data_dir(self, data_type: Optional[str] = None) -> Path:
        """
        Get parsed data directory
        
        Args:
            data_type: Data type (json, csv, xml, html, reddit, twitter, github)
                      If provided, return parsed_data/{data_type}_analysis
                      If None, return parsed_data
        
        Returns:
            Parsed data directory path
        """
        if data_type:
            analysis_dir = self.parsed_data_dir / f"{data_type}_analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            return analysis_dir
        return self.parsed_data_dir
    
    def get_unicode_analysis_dir(self) -> Path:
        """Get Unicode analysis directory"""
        return self.unicode_analysis_dir
    
    def get_config_dir(self) -> Path:
        """Get configuration directory"""
        return self.config_dir
    
    def get_log_dir(self) -> Path:
        """Get log directory"""
        return self.log_dir
    
    def get_project_root(self) -> Path:
        """Get project root directory"""
        return self.project_root
    
    def ensure_dirs_exist(self):
        """Ensure all necessary directories exist"""
        dirs = [
            self.data_root,
            self.origin_data_dir,
            self.parsed_data_dir,
            self.unicode_analysis_dir,
            self.config_dir,
            self.log_dir
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_websites_dir(self) -> Path:
        """Get websites list file directory"""
        return self.project_root / "websites"
    
    def __repr__(self):
        return f"PathManager(project_root={self.project_root})"


