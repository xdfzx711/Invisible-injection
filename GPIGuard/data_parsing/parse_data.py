#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Parsing Unified Entry Point
Provides interactive menu for parsing collected data of various types
"""

from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_parsing.parsers import (
    HTMLParser, RedditParser, TwitterParser, GithubParser, GodOfPromptParser
)
from data_collection.utils import setup_logger, PathManager


class DataParsingManager:
    """Data Parsing Manager"""
    
    def __init__(self):
        self.logger = setup_logger('DataParsingManager')
        self.path_manager = PathManager()
        
        # Parser configuration
        self.parsers = {
            '1': {
                'name': 'HTML Data Parsing',
                'description': 'Extract text content from HTML pages',
                'parser': HTMLParser
            },
            '2': {
                'name': 'Reddit Data Parsing',
                'description': 'Extract posts and comments from Reddit JSON',
                'parser': RedditParser
            },
            '3': {
                'name': 'Twitter Data Parsing',
                'description': 'Extract tweet content from Twitter JSON',
                'parser': TwitterParser
            },
            '4': {
                'name': 'GitHub Data Parsing',
                'description': 'Extract repository content from GitHub JSON',
                'parser': GithubParser
            },
            '5': {
                'name': 'GodOfPrompt Data Parsing',
                'description': 'Extract prompt content from GodOfPrompt JSON',
                'parser': GodOfPromptParser
            }
        }
    
    def show_menu(self):
        """Display parsing menu"""
        print("\n" + "="*70)
        print(" "*20 + "Data Parsing System")
        print("="*70)
        print("\nSelect data type to parse:\n")

        for key, parser_info in self.parsers.items():
            print(f"  [{key}] {parser_info['name']}")
            print(f"      {parser_info['description']}")

        print(f"\n  [6] Parse all data")
        print(f"  [0] Exit")
        print("\n" + "="*70)
    
    def run_parser(self, parser_key: str) -> bool:
        """Run the specified parser"""
        if parser_key not in self.parsers:
            print(f"Invalid choice: {parser_key}")
            return False
        
        parser_info = self.parsers[parser_key]
        print(f"\n{'='*70}")
        print(f"Starting {parser_info['name']}")
        print(f"{'='*70}\n")
        
        try:
            # Create parser instance
            parser = parser_info['parser']()
            
            # Check if input directory exists
            if not parser.input_dir.exists():
                print(f"Error: Input directory does not exist: {parser.input_dir}")
                print(f"Please use Data Collection Module to collect data first")
                return False
            
            # Parse directory (each file will be saved separately)
            results = parser.parse_directory()
            
            # 显示摘要
            parser.log_summary()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Parser failed: {e}", exc_info=True)
            print(f"\nParsing failed: {e}")
            return False
    
    def parse_all(self) -> bool:
        """Parse all data types"""
        print(f"\n{'='*70}")
        print(f"Starting to parse all data")
        print(f"{'='*70}\n")
        
        success_count = 0
        total_count = len(self.parsers)
        
        for parser_key, parser_info in self.parsers.items():
            print(f"\n{'='*70}")
            print(f"[{parser_key}/{total_count}] {parser_info['name']}")
            print(f"{'='*70}\n")
            
            try:
                parser = parser_info['parser']()
                
                # Check input directory
                if not parser.input_dir.exists():
                    print(f"Skipping: Input directory does not exist ({parser.input_dir})")
                    continue
                
                # Parse (each file will be saved separately)
                results = parser.parse_directory()
                
                parser.log_summary()
                if parser.stats['successful_files'] > 0:
                    success_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to parse {parser_info['name']}: {e}")
                print(f"Error: {e}")
        
        # Display summary
        print(f"\n{'='*70}")
        print(f"All parsing completed")
        print(f"{'='*70}")
        print(f"Success: {success_count}/{total_count} parsers")
        print(f"Output directory: {self.path_manager.get_parsed_data_dir()}")
        print(f"{'='*70}\n")
        
        return success_count > 0
    
    def run(self):
        """Run the parsing manager"""
        print("\n" + "="*70)
        print(" "*22 + "Data Parsing System")
        print("="*70)
        print("\nSystem Information:")
        print(f"  Project root directory: {self.path_manager.get_project_root()}")
        print(f"  Origin data directory: {self.path_manager.data_root / 'origin_data'}")
        print(f"  Parsed data directory: {self.path_manager.get_parsed_data_dir()}")
        print(f"  Log directory: {self.path_manager.get_log_dir()}")
        
        while True:
            self.show_menu()

            try:
                choice = input("\nEnter option [0-6]: ").strip()

                if choice == '0':
                    print("\nExiting parsing system")
                    break
                elif choice == '6':
                    self.parse_all()
                    print("\nContinue parsing other data? (y/n): ", end='')
                    continue_choice = input().strip().lower()
                    if continue_choice != 'y':
                        print("\nExiting parsing system")
                        break
                elif choice in self.parsers:
                    self.run_parser(choice)
                    print("\nContinue parsing other data? (y/n): ", end='')
                    continue_choice = input().strip().lower()
                    if continue_choice != 'y':
                        print("\nExiting parsing system")
                        break
                else:
                    print(f"\nInvalid option: {choice}")
                    
            except KeyboardInterrupt:
                print("\n\nUser interrupted")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                print(f"\nError: {e}")


def main():
    """Main function"""
    manager = DataParsingManager()
    manager.run()


if __name__ == "__main__":
    main()

