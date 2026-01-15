#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的Data Parsing Manager
支持干扰字符过滤功能
"""

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
    """增强的Data Parsing Manager，支持干扰字符过滤"""
    
    def __init__(self, enable_interference_filter: bool = True, 
                 filter_config: Optional[Dict[str, Any]] = None):
        """
        初始化增强解析管理器
        
        Args:
            enable_interference_filter: 是否启用干扰字符过滤器
            filter_config: 过滤器配置
        """
        super().__init__()
        
        self.enable_interference_filter = enable_interference_filter
        self.filter_config = filter_config or INTERFERENCE_FILTER_CONFIG.copy()
        
        if enable_interference_filter:
            self.filter_config['enabled'] = True
        
        self.logger.info(f"增强解析管理器初始化Completed，过滤器状态: {enable_interference_filter}")
        
        # 更新解析器配置，添加过滤器支持
        self._update_parser_configs()
    
    def _update_parser_configs(self):
        """更新解析器配置，添加过滤器支持"""
        
        # 创建支持过滤器的解析器工厂函数
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
        
        # 更新解析器配置
        self.parsers = {
            '1': {
                'name': 'HTML Data Parsing',
                'description': 'Extract text content from HTML pages' + 
                             (' (启用干扰字符过滤)' if self.enable_interference_filter else ''),
                'parser': create_html_parser
            },
            '2': {
                'name': 'Reddit Data Parsing',
                'description': 'Extract posts and comments from Reddit JSON' + 
                             (' (启用干扰字符过滤)' if self.enable_interference_filter else ''),
                'parser': create_reddit_parser
            },
            '3': {
                'name': 'Twitter Data Parsing',
                'description': 'Extract tweet content from Twitter JSON' + 
                             (' (启用干扰字符过滤)' if self.enable_interference_filter else ''),
                'parser': create_twitter_parser
            },
            '4': {
                'name': 'GitHub Data Parsing',
                'description': 'Extract repository content from GitHub JSON' + 
                             (' (启用干扰字符过滤)' if self.enable_interference_filter else ''),
                'parser': create_github_parser
            },
            '5': {
                'name': 'GodOfPrompt Data Parsing',
                'description': '从GodOfPrompt JSON中提取提示词内容' + 
                             (' (启用干扰字符过滤)' if self.enable_interference_filter else ''),
                'parser': create_godofprompt_parser
            }
        }
    
    def show_menu(self):
        """显示增强的解析菜单"""
        print("\n" + "="*70)
        print("📊 增强数据解析系统")
        print("="*70)
        
        if self.enable_interference_filter:
            print("🛡️  干扰字符过滤器: has been启用")
            print("   - 将移除emoji、数学符号、颜文字、其他语言文字")
            print("   - 保护Unicode攻击字符不被误删")
        else:
            print("⚠️  干扰字符过滤器: 未启用")
        
        print("\n可用的解析选项:")
        
        for key, parser_info in self.parsers.items():
            print(f"[{key}] {parser_info['name']}")
            print(f"    {parser_info['description']}")
        
        print(f"[6] 解析所有类型数据")
        print(f"[7] 切换过滤器状态 (当前: {'启用' if self.enable_interference_filter else '禁用'})")
        print(f"[8] 配置过滤器设置")
        print(f"[0] 退出")
        print("="*70)
    
    def toggle_filter(self):
        """切换过滤器状态"""
        self.enable_interference_filter = not self.enable_interference_filter
        
        if self.enable_interference_filter:
            self.filter_config['enabled'] = True
        
        self.logger.info(f"过滤器状态has been切换为: {self.enable_interference_filter}")
        
        # 重新配置解析器
        self._update_parser_configs()
        
        print(f"\n✅ 过滤器状态has been更新为: {'启用' if self.enable_interference_filter else '禁用'}")
    
    def configure_filter(self):
        """配置过滤器设置"""
        if not self.enable_interference_filter:
            print("\n⚠️  过滤器当前未启用，请先启用过滤器")
            return
        
        print("\n🔧 过滤器配置")
        print("="*50)
        
        categories = self.filter_config.get('categories', {})
        
        print("当前过滤类别设置:")
        for category, enabled in categories.items():
            status = "启用" if enabled else "禁用"
            print(f"  {category}: {status}")
        
        print("\n可配置选项:")
        print("[1] 切换emoji过滤")
        print("[2] 切换数学符号过滤")
        print("[3] 切换颜文字过滤")
        print("[4] 切换其他语言过滤")
        print("[5] 重置为默认设置")
        print("[0] 返回主菜单")
        
        try:
            choice = input("\n请选择配置选项: ").strip()
            
            if choice == '1':
                categories['emoji'] = not categories.get('emoji', True)
                print(f"Emoji过滤has been{'启用' if categories['emoji'] else '禁用'}")
            elif choice == '2':
                categories['math_symbols'] = not categories.get('math_symbols', True)
                print(f"数学符号过滤has been{'启用' if categories['math_symbols'] else '禁用'}")
            elif choice == '3':
                categories['kaomoji'] = not categories.get('kaomoji', True)
                print(f"颜文字过滤has been{'启用' if categories['kaomoji'] else '禁用'}")
            elif choice == '4':
                categories['other_languages'] = not categories.get('other_languages', True)
                print(f"其他语言过滤has been{'启用' if categories['other_languages'] else '禁用'}")
            elif choice == '5':
                self.filter_config = INTERFERENCE_FILTER_CONFIG.copy()
                self.filter_config['enabled'] = True
                print("has been重置为默认设置")
            elif choice == '0':
                return
            
            # 重新配置解析器
            self._update_parser_configs()
            
        except KeyboardInterrupt:
            print("\n操作has been取消")
    
    def run_interactive(self):
        """运行交互式解析系统"""
        while True:
            try:
                self.show_menu()
                choice = input("\n请选择操作: ").strip()
                
                if choice == '0':
                    print("👋 感谢使用增强数据解析系统!")
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
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n👋 程序has been退出")
                break
            except Exception as e:
                self.logger.error(f"运行时Error: {e}")
                print(f"❌ 发生Error: {e}")
    
    def run_parser(self, parser_key: str):
        """运行指定的解析器"""
        if parser_key not in self.parsers:
            print(f"❌ 无效的解析器选择: {parser_key}")
            return
        
        parser_info = self.parsers[parser_key]
        print(f"\n🚀 启动 {parser_info['name']}")
        
        try:
            # 创建解析器实例
            parser = parser_info['parser']()
            
            # 执行解析
            results = parser.parse_directory()
            
            if results:
                # 保存结果
                output_filename = f"{parser.parser_type}_parsed_filtered.json" if self.enable_interference_filter else f"{parser.parser_type}_parsed.json"
                parser.save_batch_results(results, output_filename)
                
                # 显示摘要
                parser.log_summary()
                
                # 显示过滤器统计
                if self.enable_interference_filter:
                    self._show_filter_summary(parser)
            else:
                print("⚠️  未找到可解析的数据")
                
        except Exception as e:
            self.logger.error(f"解析器运行Failed: {e}")
            print(f"❌ 解析Failed: {e}")
    
    def run_all_parsers(self):
        """运行所有解析器"""
        print(f"\n🚀 启动批量解析 (过滤器: {'启用' if self.enable_interference_filter else '禁用'})")
        
        total_results = {}
        
        for key, parser_info in self.parsers.items():
            print(f"\n{'='*50}")
            print(f"正在运行: {parser_info['name']}")
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
                    print(f"⚠️  {parser_info['name']}: 未找到可解析的数据")
                    
            except Exception as e:
                self.logger.error(f"{parser_info['name']} 运行Failed: {e}")
                print(f"❌ {parser_info['name']} Failed: {e}")
        
        # 显示总体摘要
        self._show_total_summary(total_results)
    
    def _show_filter_summary(self, parser):
        """显示过滤器摘要"""
        if hasattr(parser, 'get_filter_statistics'):
            filter_stats = parser.get_filter_statistics()
            if filter_stats and 'stats' in filter_stats:
                stats = filter_stats['stats']
                print(f"\n🛡️  过滤器统计:")
                print(f"   处理文本数: {stats.get('texts_processed', 0)}")
                print(f"   移除干扰字符数: {stats.get('interference_chars_removed', 0)}")
                print(f"   保护字符数: {stats.get('protected_chars_preserved', 0)}")
    
    def _show_total_summary(self, total_results: Dict[str, Any]):
        """显示总体摘要"""
        print(f"\n{'='*70}")
        print("📊 批量解析总体摘要")
        print(f"{'='*70}")
        
        total_files = sum(result['stats']['successful_files'] for result in total_results.values())
        total_texts = sum(result['stats']['total_texts_extracted'] for result in total_results.values())
        
        print(f"解析器数量: {len(total_results)}")
        print(f"总处理File数: {total_files}")
        print(f"总提取文本数: {total_texts}")
        
        if self.enable_interference_filter:
            total_filtered = sum(result['stats'].get('filtered_texts', 0) for result in total_results.values())
            total_chars_removed = sum(result['stats'].get('interference_chars_removed', 0) for result in total_results.values())
            print(f"过滤文本数: {total_filtered}")
            print(f"移除干扰字符数: {total_chars_removed}")
        
        print(f"{'='*70}")


def main():
    """主函数"""
    print("🚀 启动增强数据解析系统")
    
    # 创建增强解析管理器
    manager = EnhancedDataParsingManager(enable_interference_filter=False)
    
    # 运行交互式系统
    manager.run_interactive()


if __name__ == "__main__":
    main()


