#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据收集主程序 - 统一入口
提供交互式界面，让用户选择要收集的Data type
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根directory到路径
# collect_data.py -> data_collection -> testscan
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data_collection.utils.logger import setup_logger
from data_collection.utils.path_manager import PathManager


class DataCollectionManager:
    """数据收集管理器"""
    
    def __init__(self):
        self.logger = setup_logger('DataCollectionManager', console_output=False)
        self.path_manager = PathManager()
        
        # 确保必要directoryexists
        self.path_manager.ensure_dirs_exist()
        
        # 注册所有可用的收集器
        # 延迟导入，避免循环依赖
        self.collectors = {
            '1': {
                'name': 'HTML数据收集',
                'description': '根据用户输入的网址爬取HTML页面',
                'type': 'html',
                'module': 'data_collection.collectors.html_collector',
                'class': 'HTMLCollector'
            },
            '2': {
                'name': 'Reddit数据收集',
                'description': '收集Reddit帖子和评论',
                'type': 'reddit',
                'module': 'data_collection.collectors.reddit_collector',
                'class': 'RedditCollector'
            },
            '3': {
                'name': 'Twitter数据收集',
                'description': '收集Twitter推文数据',
                'type': 'twitter',
                'module': 'data_collection.collectors.twitter_collector',
                'class': 'TwitterCollector'
            },
            '4': {
                'name': 'GitHub数据收集',
                'description': '收集GitHub仓库数据 (README, Issues等)',
                'type': 'github',
                'module': 'data_collection.collectors.github_collector',
                'class': 'GithubCollector'
            },
            '5': {
                'name': 'GodOfPrompt数据收集',
                'description': '从 GodOfPrompt.ai 收集免费提示词',
                'type': 'godofprompt',
                'module': 'data_collection.collectors.godofprompt_collector',
                'class': 'GodOfPromptCollector'
            }
        }
    
    def show_menu(self):
        """显示交互式菜单"""
        print("\n" + "="*70)
        print("Unicode Agent - 数据收集系统")
        print("="*70)
        print("\n请选择要收集的Data type:\n")

        for key, info in self.collectors.items():
            print(f"  [{key}] {info['name']}")
            print(f"      {info['description']}")
            print()

        print(f"  [6] 收集所有类型数据")
        print(f"  [0] 退出")
        print("\n" + "="*70)
    
    def load_collector(self, collector_key: str):
        """
        动态加载收集器类
        
        Args:
            collector_key: 收集器键值
        
        Returns:
            收集器实例
        """
        if collector_key not in self.collectors:
            return None
        
        info = self.collectors[collector_key]
        
        try:
            # 动态导入模块
            import importlib
            module = importlib.import_module(info['module'])
            collector_class = getattr(module, info['class'])
            
            # 实例化收集器
            collector = collector_class()
            return collector
            
        except ImportError as e:
            self.logger.error(f"Failed to import collector {info['class']}: {e}")
            print(f"\nError: 收集器 {info['name']} 尚未实现")
            print(f"提示: 模块 {info['module']} 不exists")
            return None
        except Exception as e:
            self.logger.error(f"Failed to instantiate collector: {e}")
            print(f"\nError: 无法初始化收集器 {info['name']}: {e}")
            return None
    
    def run_collector(self, collector_key: str) -> bool:
        """
        运行指定的收集器
        
        Args:
            collector_key: 收集器键值
        
        Returns:
            是否成功
        """
        if collector_key not in self.collectors:
            print(f"\nError: 无效的选择: {collector_key}")
            return False
        
        collector_info = self.collectors[collector_key]
        print(f"\n{'='*70}")
        print(f"启动 {collector_info['name']}")
        print(f"{'='*70}\n")
        
        # 加载收集器
        collector = self.load_collector(collector_key)
        if collector is None:
            return False
        
        try:
            # 验证配置
            if not collector.validate_config():
                print(f"\nError: 收集器配置无效")
                print(f"请Check配置File: {collector.path_manager.get_config_dir()}")
                return False
            
            # 执行收集
            result = collector.collect()
            
            # 显示结果
            if result.get('success', False):
                self.show_collection_result(result, collector_info['type'])
                return True
            else:
                print(f"\n收集Failed: {result.get('message', 'Unknown error')}")
                return False
            
        except KeyboardInterrupt:
            print("\n\n用户中断操作")
            self.logger.info("Collection interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Collector execution failed: {e}", exc_info=True)
            print(f"\nError: 收集过程中发生异常: {e}")
            return False
    
    def collect_all(self):
        """收集所有类型的数据"""
        print("\n" + "="*70)
        print("开始收集所有类型的数据")
        print("="*70)
        
        results = {}
        for key, info in self.collectors.items():
            print(f"\n{'-'*70}")
            print(f"正在收集: {info['name']}")
            print(f"{'-'*70}")
            
            success = self.run_collector(key)
            results[info['type']] = success
            
            if not success:
                print(f"\nWarning: {info['name']} 收集Failed，继续下一个...")
        
        # 显示总结
        self.show_overall_summary(results)
    
    def show_collection_result(self, result: Dict[str, Any], data_type: str):
        """显示收集结果"""
        print(f"\nCompleted {data_type.upper()} 数据收集")
        print(f"Output directory: testscan_data/origin_data/{data_type}/")
        
        if 'file_count' in result:
            print(f"收集File数: {result['file_count']}")
        
        if 'total_size' in result:
            size_mb = result['total_size'] / (1024 * 1024)
            print(f"总大小: {size_mb:.2f} MB")
        
        if 'stats' in result:
            stats = result['stats']
            print(f"成功项: {stats.get('successful_items', 0)}")
            print(f"Failed项: {stats.get('failed_items', 0)}")
            
            if 'duration_seconds' in stats:
                print(f"耗时: {stats['duration_seconds']:.2f} 秒")
        
        if 'message' in result:
            print(f"信息: {result['message']}")
    
    def show_overall_summary(self, results: Dict[str, bool]):
        """显示总体摘要"""
        print("\n" + "="*70)
        print("收集总结")
        print("="*70)
        
        total = len(results)
        successful = sum(1 for success in results.values() if success)
        failed = total - successful
        
        for data_type, success in results.items():
            status = "成功" if success else "Failed"
            symbol = "[OK]" if success else "[FAIL]"
            print(f"  {symbol} {data_type.upper()}: {status}")
        
        print(f"\n总计: {successful}/{total} 成功, {failed}/{total} Failed")
        print("="*70)
    
    def run(self):
        """运行主程序"""
        print("\n" + "="*70)
        print("欢迎使用 Unicode Agent 数据收集系统")
        print("="*70)
        
        while True:
            self.show_menu()

            try:
                choice = input("\n请输入选项 [0-6]: ").strip()

                if choice == '0':
                    print("\n退出数据收集系统")
                    break

                elif choice == '6':
                    confirm = input("\n确认收集所有类型的数据？这可能需要较长时间 (y/n): ").strip().lower()
                    if confirm == 'y':
                        self.collect_all()
                    else:
                        print("has been取消")
                        continue

                elif choice in self.collectors:
                    self.run_collector(choice)

                else:
                    print("\nError: 无效的选项，请重新选择")
                    continue
                
                # 询问是否继续
                if choice != '0':
                    continue_choice = input("\n是否继续收集其他数据? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        print("\n退出数据收集系统")
                        break
            
            except KeyboardInterrupt:
                print("\n\n用户中断操作")
                break
            except EOFError:
                print("\n\n输入结束，退出程序")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                print(f"\n发生Error: {e}")
                continue


def main():
    """主函数"""
    try:
        manager = DataCollectionManager()
        manager.run()
    except Exception as e:
        print(f"\n致命Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

