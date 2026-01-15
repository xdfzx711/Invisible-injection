#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV API数据收集器
从政府和公共数据源收集CSV格式的数据
"""

import sys
import csv
import time
import requests
from pathlib import Path
from typing import Dict, Any
import random

# 添加项目根directory到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import GOVERNMENT_CSV_SOURCES


class CSVAPICollector(BaseCollector):
    """CSV API数据收集器"""
    
    def __init__(self):
        super().__init__('csv')
        
        # 初始化HTTP会话
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:
        """设置HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/csv, text/plain'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """验证配置 - CSV收集器不需要额外配置"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """执行CSV数据收集"""
        self.start_collection()
        
        print("\nCSV数据收集 - 政府开放数据")
        print("-" * 70)
        print("\n将收集以下数据:")
        print("  - 美国联邦假日数据")
        print("  - 美国州代码数据")
        print("  - 英国邮编数据")
        print("  - 国家代码数据")
        print("  - 世界城市数据")
        print("  - 世界货币代码")
        print()
        
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            return {
                'success': False,
                'message': 'User cancelled',
                'file_count': 0
            }
        
        try:
            print("\n开始收集CSV数据...")
            print("-" * 70)
            
            self._collect_government_data()
            
            self.end_collection()
            self.log_summary()
            
            # 统计收集的File
            file_count = len(list(self.output_dir.glob('*.csv')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} CSV files'
            }
            
        except KeyboardInterrupt:
            print("\n\n用户中断收集")
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
        """收集政府开放数据"""
        self.set_total_items(len(GOVERNMENT_CSV_SOURCES))
        
        for source in GOVERNMENT_CSV_SOURCES:
            source_name = source['name']
            country = source['country']
            url = source['url']
            
            print(f"\n[{country}] {source['description']}")
            
            try:
                # 获取CSV数据
                csv_text = self._fetch_csv(url)
                
                if csv_text:
                    # 验证CSV格式
                    if self._validate_csv(csv_text, source_name):
                        # 保存CSVFile
                        filename = self.output_dir / f"{country}_{source_name}.csv"
                        self._save_csv(csv_text, filename)
                        
                        # 统计行数
                        line_count = len(csv_text.strip().split('\n'))
                        print(f"  保存成功: {line_count} 行")
                        
                        self.increment_success()
                    else:
                        print(f"  格式验证Failed")
                        self.increment_failure()
                else:
                    print(f"  下载Failed")
                    self.increment_failure()
                
                # 添加延迟
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                print(f"  Error: {e}")
                self.increment_failure()
    
    def _fetch_csv(self, url: str) -> str:
        """获取CSV数据"""
        try:
            # 尝试验证SSL
            try:
                response = self.session.get(url, timeout=30, verify=True)
            except requests.exceptions.SSLError:
                # SSL验证Failed，尝试不验证
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
        """验证CSV格式"""
        try:
            # 尝试解析前几行
            lines = csv_text.strip().split('\n')[:5]
            
            if len(lines) < 2:
                self.logger.error(f"CSV too short: {source_name}")
                return False
            
            # 验证是否可以被CSV解析器读取
            csv_reader = csv.reader(lines)
            headers = next(csv_reader)
            
            if not headers:
                self.logger.error(f"No CSV headers found: {source_name}")
                return False
            
            # 至少有一行数据
            try:
                next(csv_reader)
            except StopIteration:
                self.logger.warning(f"CSV has no data rows: {source_name}")
                # 即使没有数据行也接受（可能只是空数据集）
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"CSV validation failed for {source_name}: {e}")
            return False
    
    def _save_csv(self, csv_text: str, filename: Path):
        """保存CSV数据"""
        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_text)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")






















