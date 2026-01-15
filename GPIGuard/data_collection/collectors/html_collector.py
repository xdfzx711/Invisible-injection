#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML数据收集器
根据用户输入的网址爬取HTML页面
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
    """HTML数据收集器"""
    
    def __init__(self):
        super().__init__('html')
        
        # 配置File路径
        self.config_file = self.get_config_path('web_scraping_config.json')
        
        # 如果配置不在新位置，尝试从旧位置读取
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "web_scraping_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # 初始化Excel读取器
        self.excel_reader = ExcelReader()
        
        # 配置加载器
        self.config_loader = ConfigLoader()
        
        # 爬虫对象（延迟初始化）
        self.scraper = None
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.config_file.exists():
            self.logger.error(f"Config file not found: {self.config_file}")
            print(f"\nError: 未找到配置File: {self.config_file}")
            print(f"请确保配置Fileexists: data_collection/config/web_scraping_config.json")
            print(f"或: web_scraping_config.json")
            return False
        
        # 尝试加载配置
        config = self.config_loader.load_json_config(self.config_file)
        if not config:
            self.logger.error("Failed to load config")
            return False
        
        # 验证必需的配置项
        required_keys = ['request_settings', 'scraping_rules']
        for key in required_keys:
            if key not in config:
                self.logger.error(f"Missing required config key: {key}")
                return False
        
        return True
    
    def collect(self) -> Dict[str, Any]:
        """执行HTML收集"""
        self.start_collection()
        
        try:
            # 1. 获取用户输入的网址
            websites = self._get_urls_from_user()
            if not websites:
                return {
                    'success': False,
                    'message': 'No URLs provided',
                    'file_count': 0
                }
            
            self.set_total_items(len(websites))
            
            # 2. 初始化爬虫
            self._initialize_scraper()
            
            # 3. 批量爬取
            print(f"\n开始爬取 {len(websites)} 个网站...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            results = self._scrape_websites(websites)
            
            self.end_collection()
            self.log_summary()
            
            # 计算总大小
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
            print("\n\n用户中断爬取操作")
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
        """获取用户输入的网址"""
        print("\n请输入要爬取的网址 (每行一个URL，输入空行结束):")
        print("示例: https://example.com")
        print("-" * 70)
        
        urls = []
        url_count = 0
        
        while True:
            try:
                url = input(f"URL {url_count + 1} (直接回车Completed输入): ").strip()
                
                if not url:
                    if url_count == 0:
                        print("Error: 至少需要输入一个URL")
                        continue
                    break
                
                # 简单验证URL格式
                if not url.startswith(('http://', 'https://')):
                    print("Warning: URL应该以 http:// 或 https:// 开头")
                    confirm = input("是否继续添加此URL? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                
                # 从URL提取域名作为名称
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc or 'unknown'
                
                urls.append({
                    'url': url,
                    'domain': domain,
                    'name': domain
                })
                
                url_count += 1
                print(f"has been添加: {domain}")
                
            except KeyboardInterrupt:
                print("\n\n用户取消输入")
                if urls:
                    confirm = input(f"\nhas been输入 {len(urls)} 个URL，是否使用这些URL继续? (y/n): ").strip().lower()
                    if confirm == 'y':
                        break
                return []
        
        print(f"\n共输入 {len(urls)} 个URL")
        return urls
    
    def _initialize_scraper(self):
        """初始化爬虫"""
        try:
            # 使用旧的ScrapingConfig和WebScraper
            scraping_config = ScrapingConfig(self.config_file)
            self.scraper = WebScraper(scraping_config, str(self.path_manager.data_root))
            self.logger.info("Web scraper initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper: {e}")
            raise
    
    def _scrape_websites(self, websites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量爬取网站"""
        results = []
        
        for i, website in enumerate(websites, 1):
            try:
                domain = website.get('domain', website.get('name', 'unknown'))
                print(f"\n[{i}/{len(websites)}] 爬取: {domain}")
                
                # 调用旧的爬虫
                result = self.scraper.scrape_website(website)
                
                if result.get('scraping_stats', {}).get('successful_pages', 0) > 0:
                    self.increment_success()
                    print(f"  成功: {result['scraping_stats']['successful_pages']} 个页面")
                else:
                    self.increment_failure()
                    print(f"  Failed")
                
                results.append(result)
                
                # 添加延迟
                if i < len(websites):
                    time.sleep(1)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"Failed to scrape {website.get('domain')}: {e}")
                self.increment_failure()
                print(f"  Error: {e}")
        
        return results

