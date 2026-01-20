#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML API data collector
Collect XML format data from RSS feeds, World Bank and other sources
"""

import sys
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any
import random

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import XML_SOURCES, XML_SOURCE_GROUPS


class XMLAPICollector(BaseCollector):
    """XML API data collector"""
    
    def __init__(self):
        super().__init__('xml')
        
        # Initialize HTTP session
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:
        """Setup HTTP session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/xml, text/xml, application/rss+xml'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """Validate configuration - XML collector doesn't require additional config"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """Execute XML data collection"""
        self.start_collection()
        
        print("\nXML data collection")
        print("-" * 70)
        
        # Show submenu
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
                self._collect_all_xml_sources()
            elif choice == 'rss':
                self._collect_rss_feeds()
            elif choice == 'worldbank':
                self._collect_worldbank()
            elif choice == 'financial':
                self._collect_financial_xml()
            
            self.end_collection()
            self.log_summary()
            
            # Count collected XML files
            file_count = len(list(self.output_dir.glob('*.xml')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} XML files'
            }
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted collection")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.xml'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"XML collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _show_submenu(self) -> str:
        """Show submenu"""
        print("\nPlease select XML data source:")
        print("  [1] RSS news feeds - BBC, CNN, NASA, etc.")
        print("  [2] World Bank XML - Country list, economic indicators")
        print("  [3] Financial XML - ECB exchange rates")
        print("  [4] Collect all XML sources")
        print("  [0] Return to main menu")
        
        while True:
            try:
                choice = input("\nPlease enter option [0-4]: ").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return 'rss'
                elif choice == '2':
                    return 'worldbank'
                elif choice == '3':
                    return 'financial'
                elif choice == '4':
                    return 'all'
                else:
                    print("Error: Invalid option")
                    
            except KeyboardInterrupt:
                return None
    
    def _collect_all_xml_sources(self):
        """Collect all XML data sources"""
        print("\nStarting to collect all XML sources...")
        print("-" * 70)
        
        total = 3  # RSS + WorldBank + Financial
        self.set_total_items(total)
        
        sources = [
            ('RSS feeds', self._collect_rss_feeds),
            ('World Bank XML', self._collect_worldbank),
            ('Financial XML', self._collect_financial_xml)
        ]
        
        for name, collect_func in sources:
            try:
                print(f"\nCollecting: {name}")
                collect_func()
                print(f"  Completed")
            except Exception as e:
                self.logger.error(f"Failed to collect {name}: {e}")
                print(f"  Failed: {e}")
    
    def _collect_rss_feeds(self):
        """Collect RSS news feeds"""
        print("\nCollecting RSS news feeds...")
        
        rss_sources = XML_SOURCE_GROUPS['rss']['sources']
        
        for source in rss_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    Save successful")
                    self.increment_success()
                else:
                    print(f"    Download or validation failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _collect_worldbank(self):
        """Collect World Bank XML data"""
        print("\nCollecting World Bank XML data...")
        
        worldbank_sources = XML_SOURCE_GROUPS['worldbank']['sources']
        
        for source in worldbank_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    Save successful")
                    self.increment_success()
                else:
                    print(f"    Download or validation failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _collect_financial_xml(self):
        """Collect financial XML data"""
        print("\nCollecting financial XML data...")
        
        financial_sources = XML_SOURCE_GROUPS['financial_xml']['sources']
        
        for source in financial_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    Save successful")
                    self.increment_success()
                else:
                    print(f"    Download or validation failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _fetch_xml(self, url: str) -> str:
        """Fetch XML data"""
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"HTTP {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _validate_xml(self, xml_text: str, source_name: str) -> bool:
        """Validate XML format"""
        try:
            ET.fromstring(xml_text)
            return True
        except ET.ParseError as e:
            self.logger.error(f"Invalid XML for {source_name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"XML validation failed for {source_name}: {e}")
            return False
    
    def _save_xml(self, xml_text: str, filename: Path):
        """Save XML data"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_text)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")

