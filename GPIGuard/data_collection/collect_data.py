#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Collection Main Program - Unified Entry Point
Provides interactive interface for users to select data type to collect
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root directory to path
# collect_data.py -> data_collection -> testscan
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data_collection.utils.logger import setup_logger
from data_collection.utils.path_manager import PathManager


class DataCollectionManager:
    """Data Collection Manager"""
    
    def __init__(self):
        self.logger = setup_logger('DataCollectionManager', console_output=False)
        self.path_manager = PathManager()
        
        # Ensure necessary directories exist
        self.path_manager.ensure_dirs_exist()
        
        # Register all available collectors
        # Delayed import to avoid circular dependencies
        self.collectors = {
            '1': {
                'name': 'HTML Data Collection',
                'description': 'Crawl HTML pages based on user-provided URLs',
                'type': 'html',
                'module': 'data_collection.collectors.html_collector',
                'class': 'HTMLCollector'
            },
            '2': {
                'name': 'Reddit Data Collection',
                'description': 'Collect Reddit posts and comments',
                'type': 'reddit',
                'module': 'data_collection.collectors.reddit_collector',
                'class': 'RedditCollector'
            },
            '3': {
                'name': 'Twitter Data Collection',
                'description': 'Collect Twitter tweet data',
                'type': 'twitter',
                'module': 'data_collection.collectors.twitter_collector',
                'class': 'TwitterCollector'
            },
            '4': {
                'name': 'GitHub Data Collection',
                'description': 'Collect GitHub repository data (README, Issues, etc.)',
                'type': 'github',
                'module': 'data_collection.collectors.github_collector',
                'class': 'GithubCollector'
            },
            '5': {
                'name': 'GodOfPrompt Data Collection',
                'description': 'Collect free prompts from GodOfPrompt.ai',
                'type': 'godofprompt',
                'module': 'data_collection.collectors.godofprompt_collector',
                'class': 'GodOfPromptCollector'
            }
        }
    
    def show_menu(self):
        """Display interactive menu"""
        print("\n" + "="*70)
        print("Unicode Agent - Data Collection System")
        print("="*70)
        print("\nPlease select data type to collect:\n")

        for key, info in self.collectors.items():
            print(f"  [{key}] {info['name']}")
            print(f"      {info['description']}")
            print()

        print(f"  [6] Collect all data types")
        print(f"  [0] Exit")
        print("\n" + "="*70)
    
    def load_collector(self, collector_key: str):
        """
        Dynamically load collector class
        
        Args:
            collector_key: Collector key
        
        Returns:
            Collector instance
        """
        if collector_key not in self.collectors:
            return None
        
        info = self.collectors[collector_key]
        
        try:
            # Dynamically import module
            import importlib
            module = importlib.import_module(info['module'])
            collector_class = getattr(module, info['class'])
            
            # Instantiate collector
            collector = collector_class()
            return collector
            
        except ImportError as e:
            self.logger.error(f"Failed to import collector {info['class']}: {e}")
            print(f"\nError: Collector {info['name']} not yet implemented")
            print(f"Tip: Module {info['module']} does not exist")
            return None
        except Exception as e:
            self.logger.error(f"Failed to instantiate collector: {e}")
            print(f"\nError: Unable to initialize collector {info['name']}: {e}")
            return None
    
    def run_collector(self, collector_key: str) -> bool:
        """
        Run specified collector
        
        Args:
            collector_key: Collector key
        
        Returns:
            Whether successful
        """
        if collector_key not in self.collectors:
            print(f"\nError: Invalid selection: {collector_key}")
            return False
        
        collector_info = self.collectors[collector_key]
        print(f"\n{'='*70}")
        print(f"Starting {collector_info['name']}")
        print(f"{'='*70}\n")
        
        # Load collector
        collector = self.load_collector(collector_key)
        if collector is None:
            return False
        
        try:
            # Validate configuration
            if not collector.validate_config():
                print(f"\nError: Collector configuration invalid")
                print(f"Please check configuration file: {collector.path_manager.get_config_dir()}")
                return False
            
            # Execute collection
            result = collector.collect()
            
            # Display result
            if result.get('success', False):
                self.show_collection_result(result, collector_info['type'])
                return True
            else:
                print(f"\nCollection failed: {result.get('message', 'Unknown error')}")
                return False
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted operation")
            self.logger.info("Collection interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Collector execution failed: {e}", exc_info=True)
            print(f"\nError: Exception occurred during collection: {e}")
            return False
    
    def collect_all(self):
        """Collect all types of data"""
        print("\n" + "="*70)
        print("Starting collection of all data types")
        print("="*70)
        
        results = {}
        for key, info in self.collectors.items():
            print(f"\n{'-'*70}")
            print(f"Collecting: {info['name']}")
            print(f"{'-'*70}")
            
            success = self.run_collector(key)
            results[info['type']] = success
            
            if not success:
                print(f"\nWarning: {info['name']} collection failed, continuing to next...")
        
        # Display summary
        self.show_overall_summary(results)
    
    def show_collection_result(self, result: Dict[str, Any], data_type: str):
        """Display collection result"""
        print(f"\nCompleted {data_type.upper()} data collection")
        print(f"Output directory: testscan_data/origin_data/{data_type}/")
        
        if 'file_count' in result:
            print(f"Files collected: {result['file_count']}")
        
        if 'total_size' in result:
            size_mb = result['total_size'] / (1024 * 1024)
            print(f"Total size: {size_mb:.2f} MB")
        
        if 'stats' in result:
            stats = result['stats']
            print(f"Successful items: {stats.get('successful_items', 0)}")
            print(f"Failed items: {stats.get('failed_items', 0)}")
            
            if 'duration_seconds' in stats:
                print(f"Duration: {stats['duration_seconds']:.2f} seconds")
        
        if 'message' in result:
            print(f"Message: {result['message']}")
    
    def show_overall_summary(self, results: Dict[str, bool]):
        """Display overall summary"""
        print("\n" + "="*70)
        print("Collection Summary")
        print("="*70)
        
        total = len(results)
        successful = sum(1 for success in results.values() if success)
        failed = total - successful
        
        for data_type, success in results.items():
            status = "Success" if success else "Failed"
            symbol = "[OK]" if success else "[FAIL]"
            print(f"  {symbol} {data_type.upper()}: {status}")
        
        print(f"\nTotal: {successful}/{total} successful, {failed}/{total} failed")
        print("="*70)
    
    def run(self):
        """Run main program"""
        print("\n" + "="*70)
        print("Welcome to Unicode Agent Data Collection System")
        print("="*70)
        
        while True:
            self.show_menu()

            try:
                choice = input("\nPlease enter option [0-6]: ").strip()

                if choice == '0':
                    print("\nExiting data collection system")
                    break

                elif choice == '6':
                    confirm = input("\nConfirm collection of all data types? This may take a long time (y/n): ").strip().lower()
                    if confirm == 'y':
                        self.collect_all()
                    else:
                        print("Cancelled")
                        continue

                elif choice in self.collectors:
                    self.run_collector(choice)

                else:
                    print("\nError: Invalid option, please select again")
                    continue
                
                # Ask whether to continue
                if choice != '0':
                    continue_choice = input("\nContinue collecting other data? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        print("\nExiting data collection system")
                        break
            
            except KeyboardInterrupt:
                print("\n\nUser interrupted operation")
                break
            except EOFError:
                print("\n\nInput ended, exiting program")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                print(f"\nError occurred: {e}")
                continue


def main():
    """Main function"""
    try:
        manager = DataCollectionManager()
        manager.run()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

