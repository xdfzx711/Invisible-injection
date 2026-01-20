#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import sys
import csv
import time
import requests
from pathlib import Path
from typing import Dict, Any
import random

# Add project root directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import GOVERNMENT_CSV_SOURCES


class CSVAPICollector(BaseCollector):

    
    def __init__(self):
        super().__init__('csv')
        
        # Initialize HTTP session
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/csv, text/plain'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """Validate configuration - CSV collector does not need additional configuration"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """Execute CSV data collection"""
        self.start_collection()
        
        print("\nCSV Data Collection - Government Open Data")
        print("-" * 70)
        print("\nWill collect the following data:")
        print("  - US Federal Holiday Data")
        print("  - US State Code Data")
        print("  - UK Postcode Data")
        print("  - Country Code Data")
        print("  - World Cities Data")
        print("  - World Currency Code")
        print()
        
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            return {
                'success': False,
                'message': 'User cancelled',
                'file_count': 0
            }
        
        try:
            print("\nStarting CSV data collection...")
            print("-" * 70)
            
            self._collect_government_data()
            
            self.end_collection()
            self.log_summary()
            
            # Count collected files
            file_count = len(list(self.output_dir.glob('*.csv')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} CSV files'
            }
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted collection")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.csv'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"CSV collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _collect_government_data(self):
        """Collect government open data"""
        self.set_total_items(len(GOVERNMENT_CSV_SOURCES))
        
        for source in GOVERNMENT_CSV_SOURCES:
            source_name = source['name']
            country = source['country']
            url = source['url']
            
            print(f"\n[{country}] {source['description']}")
            
            try:
                # Fetch CSV data
                csv_text = self._fetch_csv(url)
                
                if csv_text:
                    # Validate CSV format
                    if self._validate_csv(csv_text, source_name):
                        # Save CSV file
                        filename = self.output_dir / f"{country}_{source_name}.csv"
                        self._save_csv(csv_text, filename)
                        
                        # Count lines
                        line_count = len(csv_text.strip().split('\n'))
                        print(f"  Saved successfully: {line_count} lines")
                        
                        self.increment_success()
                    else:
                        print(f"  Format validation failed")
                        self.increment_failure()
                else:
                    print(f"  Download failed")
                    self.increment_failure()
                
                # Add delay
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                print(f"  Error: {e}")
                self.increment_failure()
    
    def _fetch_csv(self, url: str) -> str:
        """Fetch CSV data"""
        try:
            # Try to verify SSL
            try:
                response = self.session.get(url, timeout=30, verify=True)
            except requests.exceptions.SSLError:
                # SSL verification failed, try without verification
                self.logger.warning(f"SSL verification failed, retrying without verification: {url}")
                response = self.session.get(url, timeout=30, verify=False)
            
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"HTTP {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _validate_csv(self, csv_text: str, source_name: str) -> bool:
        """Validate CSV format"""
        try:
            # Try to parse first few lines
            lines = csv_text.strip().split('\n')[:5]
            
            if len(lines) < 2:
                self.logger.error(f"CSV too short: {source_name}")
                return False
            
            # Verify if it can be read by CSV parser
            csv_reader = csv.reader(lines)
            headers = next(csv_reader)
            
            if not headers:
                self.logger.error(f"No CSV headers found: {source_name}")
                return False
            
            # At least one data row
            try:
                next(csv_reader)
            except StopIteration:
                self.logger.warning(f"CSV has no data rows: {source_name}")
                # Accept even without data rows (might be just an empty dataset)
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"CSV validation failed for {source_name}: {e}")
            return False
    
    def _save_csv(self, csv_text: str, filename: Path):
        """Save CSV data"""
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_text)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")






















