#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_parsing.parse_data import DataParsingManager
from data_parsing.parsers import (
    HTMLParser, RedditParser, TwitterParser, GithubParser, GodOfPromptParser
)
from data_collection.utils import setup_logger, PathManager
from data_parsing.filters import INTERFERENCE_FILTER_CONFIG


class EnhancedDataParsingManager(DataParsingManager):
    """Enhanced Data Parsing Manager supporting interference character filtering"""
    
    def __init__(self, enable_interference_filter: bool = True, 
                 filter_config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced parsing manager
        
        Args:
            enable_interference_filter: Whether to enable interference character filter
            filter_config: Filter configuration
        """
        super().__init__()
        
        self.enable_interference_filter = enable_interference_filter
        self.filter_config = filter_config or INTERFERENCE_FILTER_CONFIG.copy()
        
        if enable_interference_filter:
            self.filter_config['enabled'] = True
        
        self.logger.info(f"Enhanced parser manager initialization completed, filter status: {enable_interference_filter}")
        
        # Update parser configuration, add filter support
        self._update_parser_configs()
    
    def _update_parser_configs(self):
        """Update parser configuration, add filter support"""
        
        # Create parser factory functions supporting filter
        def create_html_parser():
            return HTMLParser(self.enable_interference_filter, self.filter_config)
        
        def create_reddit_parser():
            return RedditParser(self.enable_interference_filter, self.filter_config)
        
        def create_twitter_parser():
            return TwitterParser(self.enable_interference_filter, self.filter_config)
        
        def create_github_parser():
            return GithubParser(self.enable_interference_filter, self.filter_config)
        
        def create_godofprompt_parser():
            return GodOfPromptParser(self.enable_interference_filter, self.filter_config)
        
        # Update parser configuration
        self.parsers = {
            '1': {
                'name': 'HTML Data Parsing',
                'description': 'Extract text content from HTML pages' + 
                             (' (Interference character filter enabled)' if self.enable_interference_filter else ''),
                'parser': create_html_parser
            },
            '2': {
                'name': 'Reddit Data Parsing',
                'description': 'Extract posts and comments from Reddit JSON' + 
                             (' (Interference character filter enabled)' if self.enable_interference_filter else ''),
                'parser': create_reddit_parser
            },
            '3': {
                'name': 'Twitter Data Parsing',
                'description': 'Extract tweet content from Twitter JSON' + 
                             (' (Interference character filter enabled)' if self.enable_interference_filter else ''),
                'parser': create_twitter_parser
            },
            '4': {
                'name': 'GitHub Data Parsing',
                'description': 'Extract repository content from GitHub JSON' + 
                             (' (Interference character filter enabled)' if self.enable_interference_filter else ''),
                'parser': create_github_parser
            },
            '5': {
                'name': 'GodOfPrompt Data Parsing',
                'description': 'Extract prompt content from GodOfPrompt JSON' + 
                             (' (Interference character filter enabled)' if self.enable_interference_filter else ''),
                'parser': create_godofprompt_parser
            }
        }
    
    def show_menu(self):
        """Display enhanced parsing menu"""
        print("\n" + "="*70)
        print("📊 Enhanced Data Parsing System")
        print("="*70)
        
        if self.enable_interference_filter:
            print("🛡️  Interference character filter: Enabled")
            print("   - Will remove emoji, math symbols, kaomoji, other language characters")
            print("   - Protect Unicode attack characters from being accidentally deleted")
        else:
            print("⚠️  Interference character filter: Disabled")
        
        print("\nAvailable parsing options:")
        
        for key, parser_info in self.parsers.items():
            print(f"[{key}] {parser_info['name']}")
            print(f"    {parser_info['description']}")
        
        print(f"[6] Parse all data types")
        print(f"[7] Toggle filter status (Current: {'Enabled' if self.enable_interference_filter else 'Disabled'})")
        print(f"[8] Configure filter settings")
        print(f"[0] Exit")
        print("="*70)
    
    def toggle_filter(self):
        """Toggle filter status"""
        self.enable_interference_filter = not self.enable_interference_filter
        
        if self.enable_interference_filter:
            self.filter_config['enabled'] = True
        
        self.logger.info(f"Filter status toggled to: {self.enable_interference_filter}")
        
        # Reconfigure parser
        self._update_parser_configs()
        
        print(f"\n✅ Filter status updated to: {'Enabled' if self.enable_interference_filter else 'Disabled'}")
    
    def configure_filter(self):
        """Configure filter settings"""
        if not self.enable_interference_filter:
            print("\n⚠️  Filter is currently disabled, please enable it first")
            return
        
        print("\n🔧 Filter Configuration")
        print("="*50)
        
        categories = self.filter_config.get('categories', {})
        
        print("Current filter category settings:")
        for category, enabled in categories.items():
            status = "Enabled" if enabled else "Disabled"
            print(f"  {category}: {status}")
        
        print("\nConfigurable options:")
        print("[1] Toggle emoji filtering")
        print("[2] Toggle math symbol filtering")
        print("[3] Toggle kaomoji filtering")
        print("[4] Toggle other language filtering")
        print("[5] Reset to default settings")
        print("[0] Return to main menu")
        
        try:
            choice = input("\nSelect configuration option: ").strip()
            
            if choice == '1':
                categories['emoji'] = not categories.get('emoji', True)
                print(f"Emoji filtering has been {'enabled' if categories['emoji'] else 'disabled'}")
            elif choice == '2':
                categories['math_symbols'] = not categories.get('math_symbols', True)
                print(f"Math symbol filtering has been {'enabled' if categories['math_symbols'] else 'disabled'}")
            elif choice == '3':
                categories['kaomoji'] = not categories.get('kaomoji', True)
                print(f"Kaomoji filtering has been {'enabled' if categories['kaomoji'] else 'disabled'}")
            elif choice == '4':
                categories['other_languages'] = not categories.get('other_languages', True)
                print(f"Other language filtering has been {'enabled' if categories['other_languages'] else 'disabled'}")
            elif choice == '5':
                self.filter_config = INTERFERENCE_FILTER_CONFIG.copy()
                self.filter_config['enabled'] = True
                print("Settings have been reset to default")
            elif choice == '0':
                return
            
            # Reconfigure parser
            self._update_parser_configs()
            
        except KeyboardInterrupt:
            print("\nOperation cancelled")
    
    def run_interactive(self):
        """Run interactive parsing system"""
        while True:
            try:
                self.show_menu()
                choice = input("\nSelect operation: ").strip()
                
                if choice == '0':
                    print("👋 Thank you for using enhanced data parsing system!")
                    break
                elif choice in self.parsers:
                    self.run_parser(choice)
                elif choice == '6':
                    self.run_all_parsers()
                elif choice == '7':
                    self.toggle_filter()
                elif choice == '8':
                    self.configure_filter()
                else:
                    print("❌ Invalid choice, please try again")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Program exited")
                break
            except Exception as e:
                self.logger.error(f"Runtime error: {e}")
                print(f"❌ Error occurred: {e}")
    
    def run_parser(self, parser_key: str):
        """Run the specified parser"""
        if parser_key not in self.parsers:
            print(f"❌ Invalid parser selection: {parser_key}")
            return
        
        parser_info = self.parsers[parser_key]
        print(f"\n🚀 Starting {parser_info['name']}")
        
        try:
            # Create parser instance
            parser = parser_info['parser']()
            
            # Execute parsing
            results = parser.parse_directory()
            
            if results:
                # Save results
                output_filename = f"{parser.parser_type}_parsed_filtered.json" if self.enable_interference_filter else f"{parser.parser_type}_parsed.json"
                parser.save_batch_results(results, output_filename)
                
                # Display summary
                parser.log_summary()
                
                # Display filter statistics
                if self.enable_interference_filter:
                    self._show_filter_summary(parser)
            else:
                print("⚠️  No parseable data found")
                
        except Exception as e:
            self.logger.error(f"Parser execution failed: {e}")
            print(f"❌ Parsing failed: {e}")
    
    def run_all_parsers(self):
        """Run all parsers"""
        print(f"\n🚀 Starting batch parsing (Filter: {'Enabled' if self.enable_interference_filter else 'Disabled'})")
        
        total_results = {}
        
        for key, parser_info in self.parsers.items():
            print(f"\n{'='*50}")
            print(f"Running: {parser_info['name']}")
            print(f"{'='*50}")
            
            try:
                parser = parser_info['parser']()
                results = parser.parse_directory()
                
                if results:
                    output_filename = f"{parser.parser_type}_parsed_filtered.json" if self.enable_interference_filter else f"{parser.parser_type}_parsed.json"
                    parser.save_batch_results(results, output_filename)
                    parser.log_summary()
                    
                    total_results[parser.parser_type] = {
                        'results_count': len(results),
                        'stats': parser.get_stats()
                    }
                    
                    if self.enable_interference_filter:
                        self._show_filter_summary(parser)
                else:
                    print(f"⚠️  {parser_info['name']}: No parseable data found")
                    
            except Exception as e:
                self.logger.error(f"{parser_info['name']} failed to run: {e}")
                print(f"❌ {parser_info['name']} Failed: {e}")
        
        # Display overall summary
        self._show_total_summary(total_results)
    
    def _show_filter_summary(self, parser):
        """Display filter summary"""
        if hasattr(parser, 'get_filter_statistics'):
            filter_stats = parser.get_filter_statistics()
            if filter_stats and 'stats' in filter_stats:
                stats = filter_stats['stats']
                print(f"\n🛡️  Filter statistics:")
                print(f"   Texts processed: {stats.get('texts_processed', 0)}")
                print(f"   Interference characters removed: {stats.get('interference_chars_removed', 0)}")
                print(f"   Protected characters preserved: {stats.get('protected_chars_preserved', 0)}")
    
    def _show_total_summary(self, total_results: Dict[str, Any]):
        """Display overall summary"""
        print(f"\n{'='*70}")
        print("📊 Batch parsing overall summary")
        print(f"{'='*70}")
        
        total_files = sum(result['stats']['successful_files'] for result in total_results.values())
        total_texts = sum(result['stats']['total_texts_extracted'] for result in total_results.values())
        
        print(f"Number of parsers: {len(total_results)}")
        print(f"Total files processed: {total_files}")
        print(f"Total texts extracted: {total_texts}")
        
        if self.enable_interference_filter:
            total_filtered = sum(result['stats'].get('filtered_texts', 0) for result in total_results.values())
            total_chars_removed = sum(result['stats'].get('interference_chars_removed', 0) for result in total_results.values())
            print(f"Filtered texts: {total_filtered}")
            print(f"Interference characters removed: {total_chars_removed}")
        
        print(f"{'='*70}")


def main():
    """Main function"""
    print("🚀 Starting enhanced data parsing system")
    
    # Create enhanced parsing manager
    manager = EnhancedDataParsingManager(enable_interference_filter=False)
    
    # Run interactive system
    manager.run_interactive()


if __name__ == "__main__":
    main()


