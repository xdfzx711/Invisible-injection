#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON API data collector
Collect JSON formatted data from various public APIs
"""

import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
import random

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import (
    GITHUB_SOURCES, PUBLIC_API_SOURCES, FINANCIAL_API_SOURCES, 
    WEATHER_API_SOURCES, JSON_SOURCE_GROUPS
)


class JSONAPICollector(BaseCollector):
    """JSON API data collector"""
    
    def __init__(self):
        super().__init__('json')
        
        # Initialize HTTP session
        self.session = self._setup_session()
        
    def _setup_session(self) -> requests.Session:
        """Setup HTTP session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """Validate configuration - JSON collector does not require additional configuration"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """Execute JSON data collection"""
        self.start_collection()
        
        print("\nJSON API data collection")
        print("-" * 70)
        
        # Display submenu
        choice = self._show_submenu()
        
        if not choice:
            return {
                'success': False,
                'message': 'User cancelled',
                'file_count': 0
            }
        
        try:
            # Collect data based on choice
            if choice == 'all':
                self._collect_all_json_sources()
            elif choice == 'github':
                self._collect_github()
            elif choice == 'public':
                self._collect_public_apis()
            elif choice == 'financial':
                self._collect_financial()
            elif choice == 'weather':
                self._collect_weather()
            
            self.end_collection()
            self.log_summary()
            
            # Count collected JSON files
            file_count = len(list(self.output_dir.glob('*.json')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} JSON files'
            }
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted collection")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.json'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"JSON collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _show_submenu(self) -> str:
        """Display submenu"""
        print("\nPlease select JSON data source:")
        print("  [1] GitHub API - Collect GitHub user and repository data")
        print("  [2] Public APIs - Wikipedia, NASA, Wikidata")
        print("  [3] Financial APIs - Cryptocurrency prices, exchange rates")
        print("  [4] Weather APIs - City weather data")
        print("  [5] Collect all JSON data sources")
        print("  [0] Return to main menu")
        
        while True:
            try:
                choice = input("\nPlease enter option [0-5]: ").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return 'github'
                elif choice == '2':
                    return 'public'
                elif choice == '3':
                    return 'financial'
                elif choice == '4':
                    return 'weather'
                elif choice == '5':
                    return 'all'
                else:
                    print("Error: Invalid option")
                    
            except KeyboardInterrupt:
                return None
    
    def _collect_all_json_sources(self):
        """Collect all JSON data sources"""
        print("\nStarting to collect all JSON data sources...")
        print("-" * 70)
        
        total = 4  # GitHub + Public + Financial + Weather
        self.set_total_items(total)
        
        sources = [
            ('GitHub API', self._collect_github),
            ('Public APIs', self._collect_public_apis),
            ('Financial APIs', self._collect_financial),
            ('Weather APIs', self._collect_weather)
        ]
        
        for name, collect_func in sources:
            try:
                print(f"\nCollecting: {name}")
                collect_func()
                print(f"  Completed")
            except Exception as e:
                self.logger.error(f"Failed to collect {name}: {e}")
                print(f"  Failed: {e}")
    
    def _collect_github(self):
        """Collect GitHub API data"""
        print("\nCollecting GitHub data...")
        
        users = GITHUB_SOURCES['users']
        
        for user_info in users:
            username = user_info['username']
            success_count = 0
            try:
                # Collect user information
                user_url = f"https://api.github.com/users/{username}"
                user_data = self._fetch_json(user_url)
                
                if user_data:
                    filename = self.output_dir / f"github_user_{username}.json"
                    self._save_json(user_data, filename)
                    print(f"  Saved user: {username} ({user_info['description']})")
                    success_count += 1
                
                # Collect repository information
                repos_url = f"https://api.github.com/users/{username}/repos?per_page=5"
                repos_data = self._fetch_json(repos_url)
                
                if repos_data:
                    filename = self.output_dir / f"github_repos_{username}.json"
                    self._save_json(repos_data, filename)
                    print(f"  Saved repos: {username}")
                    success_count += 1
                
                if success_count > 0:
                    self.increment_success()
                else:
                    self.increment_failure()
                
                time.sleep(1)  # Avoid API rate limiting
                
            except Exception as e:
                self.logger.error(f"Failed to collect GitHub data for {username}: {e}")
                self.increment_failure()
                print(f"  Error: {username} - {e}")
    
    def _collect_public_apis(self):
        """Collect public API data"""
        print("\nCollecting public API data...")
        
        for source in PUBLIC_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    Saved: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _collect_financial(self):
        """Collect financial API data"""
        print("\nCollecting financial API data...")
        
        for source in FINANCIAL_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"financial_{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    Saved: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _collect_weather(self):
        """Collect weather API data"""
        print("\nCollecting weather API data...")
        
        for source in WEATHER_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    Saved: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(0.5, 1))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data"""
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"HTTP {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from {url}: {e}")
            return None
    
    def _save_json(self, data: Dict[str, Any], filename: Path):
        """Save JSON data"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")

