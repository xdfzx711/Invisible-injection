#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据解析统一入口
提供交互式菜单，解析收集到的各类数据
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
        
        # 解析器配置
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
                'description': '从GodOfPrompt JSON中提取提示词内容',
                'parser': GodOfPromptParser
            }
        }
    
    def show_menu(self):
        """显示解析菜单"""
        print("\n" + "="*70)
        print(" "*20 + "数据解析系统")
        print("="*70)
        print("\n请选择要解析的Data type:\n")

        for key, parser_info in self.parsers.items():
            print(f"  [{key}] {parser_info['name']}")
            print(f"      {parser_info['description']}")

        print(f"\n  [6] 解析所有数据")
        print(f"  [0] 退出")
        print("\n" + "="*70)
    
    def run_parser(self, parser_key: str) -> bool:
        """运行指定的解析器"""
        if parser_key not in self.parsers:
            print(f"无效的选择: {parser_key}")
            return False
        
        parser_info = self.parsers[parser_key]
        print(f"\n{'='*70}")
        print(f"启动 {parser_info['name']}")
        print(f"{'='*70}\n")
        
        try:
            # 创建解析器实例
            parser = parser_info['parser']()
            
            # Check输入directory是否exists
            if not parser.input_dir.exists():
                print(f"Error: 输入directory不exists: {parser.input_dir}")
                print(f"请先使用Data Collection Module收集数据")
                return False
            
            # 解析directory（每个File会单独保存）
            results = parser.parse_directory()
            
            # 显示摘要
            parser.log_summary()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Parser failed: {e}", exc_info=True)
            print(f"\n解析Failed: {e}")
            return False
    
    def parse_all(self) -> bool:
        """解析所有Data type"""
        print(f"\n{'='*70}")
        print(f"开始解析所有数据")
        print(f"{'='*70}\n")
        
        success_count = 0
        total_count = len(self.parsers)
        
        for parser_key, parser_info in self.parsers.items():
            print(f"\n{'='*70}")
            print(f"[{parser_key}/{total_count}] {parser_info['name']}")
            print(f"{'='*70}\n")
            
            try:
                parser = parser_info['parser']()
                
                # Check输入directory
                if not parser.input_dir.exists():
                    print(f"跳过: 输入directory不exists ({parser.input_dir})")
                    continue
                
                # 解析（每个File会单独保存）
                results = parser.parse_directory()
                
                parser.log_summary()
                if parser.stats['successful_files'] > 0:
                    success_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to parse {parser_info['name']}: {e}")
                print(f"Error: {e}")
        
        # 显示总结
        print(f"\n{'='*70}")
        print(f"全部解析Completed")
        print(f"{'='*70}")
        print(f"成功: {success_count}/{total_count} 个解析器")
        print(f"Output directory: {self.path_manager.get_parsed_data_dir()}")
        print(f"{'='*70}\n")
        
        return success_count > 0
    
    def run(self):
        """运行解析管理器"""
        print("\n" + "="*70)
        print(" "*22 + "数据解析系统")
        print("="*70)
        print("\n系统信息:")
        print(f"  项目根directory: {self.path_manager.get_project_root()}")
        print(f"  Origin data directory: {self.path_manager.data_root / 'origin_data'}")
        print(f"  Parsed data directory: {self.path_manager.get_parsed_data_dir()}")
        print(f"  Log directory: {self.path_manager.get_log_dir()}")
        
        while True:
            self.show_menu()

            try:
                choice = input("\n请输入选项 [0-6]: ").strip()

                if choice == '0':
                    print("\n退出解析系统")
                    break
                elif choice == '6':
                    self.parse_all()
                    print("\n是否继续解析其他数据? (y/n): ", end='')
                    continue_choice = input().strip().lower()
                    if continue_choice != 'y':
                        print("\n退出解析系统")
                        break
                elif choice in self.parsers:
                    self.run_parser(choice)
                    print("\n是否继续解析其他数据? (y/n): ", end='')
                    continue_choice = input().strip().lower()
                    if continue_choice != 'y':
                        print("\n退出解析系统")
                        break
                else:
                    print(f"\n无效的选项: {choice}")
                    
            except KeyboardInterrupt:
                print("\n\n用户中断")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                print(f"\nError: {e}")


def main():
    """主函数"""
    manager = DataParsingManager()
    manager.run()


if __name__ == "__main__":
    main()

