#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON API数据收集器
从各种公共API收集JSON格式的数据
"""

import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
import random

# 添加项目根directory到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import (
    GITHUB_SOURCES, PUBLIC_API_SOURCES, FINANCIAL_API_SOURCES, 
    WEATHER_API_SOURCES, JSON_SOURCE_GROUPS
)


class JSONAPICollector(BaseCollector):
    """JSON API数据收集器"""
    
    def __init__(self):
        super().__init__('json')
        
        # 初始化HTTP会话
        self.session = self._setup_session()
        
    def _setup_session(self) -> requests.Session:
        """设置HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """验证配置 - JSON收集器不需要额外配置"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """执行JSON数据收集"""
        self.start_collection()
        
        print("\nJSON API数据收集")
        print("-" * 70)
        
        # 显示子菜单
        choice = self._show_submenu()
        
        if not choice:
            return {
                'success': False,
                'message': 'User cancelled',
                'file_count': 0
            }
        
        try:
            # 根据选择收集数据
            if choice == 'all':
                self._collect_all_json_sources()
            elif choice == 'github':
                self._collect_github()
            elif choice == 'public':
                self._collect_public_apis()
            elif choice == 'financial':
                self._collect_financial()
            elif choice == 'weather':
                self._collect_weather()
            
            self.end_collection()
            self.log_summary()
            
            # 统计收集的File
            file_count = len(list(self.output_dir.glob('*.json')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} JSON files'
            }
            
        except KeyboardInterrupt:
            print("\n\n用户中断收集")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.json'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"JSON collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _show_submenu(self) -> str:
        """显示子菜单"""
        print("\n请选择JSON数据源:")
        print("  [1] GitHub API - 收集GitHub用户和仓库数据")
        print("  [2] 公共API - Wikipedia, NASA, Wikidata")
        print("  [3] 金融API - 加密货币价格, 汇率数据")
        print("  [4] 天气API - 城市天气数据")
        print("  [5] 收集所有JSON数据源")
        print("  [0] 返回主菜单")
        
        while True:
            try:
                choice = input("\n请输入选项 [0-5]: ").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return 'github'
                elif choice == '2':
                    return 'public'
                elif choice == '3':
                    return 'financial'
                elif choice == '4':
                    return 'weather'
                elif choice == '5':
                    return 'all'
                else:
                    print("Error: 无效的选项")
                    
            except KeyboardInterrupt:
                return None
    
    def _collect_all_json_sources(self):
        """收集所有JSON数据源"""
        print("\n开始收集所有JSON数据源...")
        print("-" * 70)
        
        total = 4  # GitHub + Public + Financial + Weather
        self.set_total_items(total)
        
        sources = [
            ('GitHub API', self._collect_github),
            ('公共API', self._collect_public_apis),
            ('金融API', self._collect_financial),
            ('天气API', self._collect_weather)
        ]
        
        for name, collect_func in sources:
            try:
                print(f"\n正在收集: {name}")
                collect_func()
                print(f"  Completed")
            except Exception as e:
                self.logger.error(f"Failed to collect {name}: {e}")
                print(f"  Failed: {e}")
    
    def _collect_github(self):
        """收集GitHub API数据"""
        print("\n收集GitHub数据...")
        
        users = GITHUB_SOURCES['users']
        
        for user_info in users:
            username = user_info['username']
            success_count = 0
            try:
                # 收集用户信息
                user_url = f"https://api.github.com/users/{username}"
                user_data = self._fetch_json(user_url)
                
                if user_data:
                    filename = self.output_dir / f"github_user_{username}.json"
                    self._save_json(user_data, filename)
                    print(f"  保存用户: {username} ({user_info['description']})")
                    success_count += 1
                
                # 收集仓库信息
                repos_url = f"https://api.github.com/users/{username}/repos?per_page=5"
                repos_data = self._fetch_json(repos_url)
                
                if repos_data:
                    filename = self.output_dir / f"github_repos_{username}.json"
                    self._save_json(repos_data, filename)
                    print(f"  保存仓库: {username}")
                    success_count += 1
                
                if success_count > 0:
                    self.increment_success()
                else:
                    self.increment_failure()
                
                time.sleep(1)  # 避免API限制
                
            except Exception as e:
                self.logger.error(f"Failed to collect GitHub data for {username}: {e}")
                self.increment_failure()
                print(f"  Error: {username} - {e}")
    
    def _collect_public_apis(self):
        """收集公共API数据"""
        print("\n收集公共API数据...")
        
        for source in PUBLIC_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    保存: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _collect_financial(self):
        """收集金融API数据"""
        print("\n收集金融API数据...")
        
        for source in FINANCIAL_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"financial_{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    保存: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _collect_weather(self):
        """收集天气API数据"""
        print("\n收集天气API数据...")
        
        for source in WEATHER_API_SOURCES:
            source_name = source['name']
            source_type = source['type']
            
            print(f"  {source['description']}")
            
            for i, url in enumerate(source['urls'], 1):
                try:
                    data = self._fetch_json(url)
                    
                    if data:
                        filename = self.output_dir / f"{source_type}_{source_name}_{i}.json"
                        self._save_json(data, filename)
                        print(f"    保存: {source_type} #{i}")
                        self.increment_success()
                    else:
                        self.increment_failure()
                    
                    time.sleep(random.uniform(0.5, 1))
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    self.increment_failure()
                    print(f"    Failed: {e}")
    
    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """获取JSON数据"""
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"HTTP {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from {url}: {e}")
            return None
    
    def _save_json(self, data: Dict[str, Any], filename: Path):
        """保存JSON数据"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")

