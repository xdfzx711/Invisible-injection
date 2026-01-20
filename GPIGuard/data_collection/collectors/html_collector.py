#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML data collector
Scrape HTML pages based on URLs provided by user
"""

import time
from pathlib import Path
from typing import Dict, Any, List

from data_collection.base_collector import BaseCollector
from data_collection.utils.excel_reader import ExcelReader
from data_collection.utils.config_loader import ConfigLoader
from data_collection.scrapers.web_scraper import WebScraper
from data_collection.scrapers.scraping_config import ScrapingConfig


class HTMLCollector(BaseCollector):
    """HTML data collector"""
    
    def __init__(self):
        super().__init__('html')
        
        # Config file path
        self.config_file = self.get_config_path('web_scraping_config.json')
        
        # If config is not in new location, try reading from old location
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "web_scraping_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # Initialize Excel reader
        self.excel_reader = ExcelReader()
        
        # Config loader
        self.config_loader = ConfigLoader()
        
        # Web scraper (lazy initialization)
        self.scraper = None
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.config_file.exists():
            self.logger.error(f"Config file not found: {self.config_file}")
            print(f"\nError: Config file not found: {self.config_file}")
            print(f"Please ensure config file exists: data_collection/config/web_scraping_config.json")
            print(f"Or: web_scraping_config.json")
            return False
        
        # Try to load config
        config = self.config_loader.load_json_config(self.config_file)
        if not config:
            self.logger.error("Failed to load config")
            return False
        
        # Validate required config keys
        required_keys = ['request_settings', 'scraping_rules']
        for key in required_keys:
            if key not in config:
                self.logger.error(f"Missing required config key: {key}")
                return False
        
        return True
    
    def collect(self) -> Dict[str, Any]:
        """Execute HTML collection"""
        self.start_collection()
        
        try:
            # 1. Get URLs provided by user
            websites = self._get_urls_from_user()
            if not websites:
                return {
                    'success': False,
                    'message': 'No URLs provided',
                    'file_count': 0
                }
            
            self.set_total_items(len(websites))
            
            # 2. Initialize web scraper
            self._initialize_scraper()
            
            # 3. Batch scrape websites
            print(f"\nStarting to scrape {len(websites)} websites...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            results = self._scrape_websites(websites)
            
            self.end_collection()
            self.log_summary()
            
            # Calculate total size
            total_size = sum(r.get('size', 0) for r in results if r.get('success'))
            
            return {
                'success': True,
                'file_count': self.stats['successful_items'],
                'total_size': total_size,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {self.stats["successful_items"]} websites'
            }
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted scraping operation")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted by user',
                'file_count': self.stats['successful_items'],
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"Collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'file_count': self.stats['successful_items'],
                'stats': self.get_stats()
            }
    
    def _get_urls_from_user(self) -> List[Dict[str, Any]]:
        """Get URLs from user input"""
        print("\nPlease enter URLs to scrape (one per line, press Enter to finish):")
        print("Example: https://example.com")
        print("-" * 70)
        
        urls = []
        url_count = 0
        
        while True:
            try:
                url = input(f"URL {url_count + 1} (press Enter to finish): ").strip()
                
                if not url:
                    if url_count == 0:
                        print("Error: At least one URL is required")
                        continue
                    break
                
                # Simple URL format validation
                if not url.startswith(('http://', 'https://')):
                    print("Warning: URL should start with http:// or https://")
                    confirm = input("Continue adding this URL? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                
                # Extract domain name from URL as name
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc or 'unknown'
                
                urls.append({
                    'url': url,
                    'domain': domain,
                    'name': domain
                })
                
                url_count += 1
                print(f"Added: {domain}")
                
            except KeyboardInterrupt:
                print("\n\nUser canceled input")
                if urls:
                    confirm = input(f"\nEntered {len(urls)} URLs, continue with these URLs? (y/n): ").strip().lower()
                    if confirm == 'y':
                        break
                return []
        
        print(f"\nTotal {len(urls)} URLs entered")
        return urls
    
    def _initialize_scraper(self):
        """Initialize web scraper"""
        try:
            # Use old ScrapingConfig and WebScraper
            scraping_config = ScrapingConfig(self.config_file)
            self.scraper = WebScraper(scraping_config, str(self.path_manager.data_root))
            self.logger.info("Web scraper initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper: {e}")
            raise
    
    def _scrape_websites(self, websites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch scrape websites"""
        results = []
        
        for i, website in enumerate(websites, 1):
            try:
                domain = website.get('domain', website.get('name', 'unknown'))
                print(f"\n[{i}/{len(websites)}] Scraping: {domain}")
                
                # Call old scraper
                result = self.scraper.scrape_website(website)
                
                if result.get('scraping_stats', {}).get('successful_pages', 0) > 0:
                    self.increment_success()
                    print(f"  Success: {result['scraping_stats']['successful_pages']} pages")
                else:
                    self.increment_failure()
                    print(f"  Failed")
                
                results.append(result)
                
                # Add delay
                if i < len(websites):
                    time.sleep(1)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"Failed to scrape {website.get('domain')}: {e}")
                self.increment_failure()
                print(f"  Error: {e}")
        
        return results

