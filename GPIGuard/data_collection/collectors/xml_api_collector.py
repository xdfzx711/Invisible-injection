#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML API数据收集器
从RSS、世界银行等数据源收集XML格式的数据
"""

import sys
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any
import random

# 添加项目根directory到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_collection.base_collector import BaseCollector
from data_collection.utils.api_sources import XML_SOURCES, XML_SOURCE_GROUPS


class XMLAPICollector(BaseCollector):
    """XML API数据收集器"""
    
    def __init__(self):
        super().__init__('xml')
        
        # 初始化HTTP会话
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:
        """设置HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/xml, text/xml, application/rss+xml'
        })
        session.timeout = 30
        return session
    
    def validate_config(self) -> bool:
        """验证配置 - XML收集器不需要额外配置"""
        return True
    
    def collect(self) -> Dict[str, Any]:
        """执行XML数据收集"""
        self.start_collection()
        
        print("\nXML数据收集")
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
                self._collect_all_xml_sources()
            elif choice == 'rss':
                self._collect_rss_feeds()
            elif choice == 'worldbank':
                self._collect_worldbank()
            elif choice == 'financial':
                self._collect_financial_xml()
            
            self.end_collection()
            self.log_summary()
            
            # 统计收集的File
            file_count = len(list(self.output_dir.glob('*.xml')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {file_count} XML files'
            }
            
        except KeyboardInterrupt:
            print("\n\n用户中断收集")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.xml'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"XML collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _show_submenu(self) -> str:
        """显示子菜单"""
        print("\n请选择XML数据源:")
        print("  [1] RSS新闻源 - BBC, CNN, NASA等")
        print("  [2] 世界银行XML - 国家列表, 经济指标")
        print("  [3] 金融XML - 欧洲央行汇率")
        print("  [4] 收集所有XML数据源")
        print("  [0] 返回主菜单")
        
        while True:
            try:
                choice = input("\n请输入选项 [0-4]: ").strip()
                
                if choice == '0':
                    return None
                elif choice == '1':
                    return 'rss'
                elif choice == '2':
                    return 'worldbank'
                elif choice == '3':
                    return 'financial'
                elif choice == '4':
                    return 'all'
                else:
                    print("Error: 无效的选项")
                    
            except KeyboardInterrupt:
                return None
    
    def _collect_all_xml_sources(self):
        """收集所有XML数据源"""
        print("\n开始收集所有XML数据源...")
        print("-" * 70)
        
        total = 3  # RSS + WorldBank + Financial
        self.set_total_items(total)
        
        sources = [
            ('RSS新闻源', self._collect_rss_feeds),
            ('世界银行XML', self._collect_worldbank),
            ('金融XML', self._collect_financial_xml)
        ]
        
        for name, collect_func in sources:
            try:
                print(f"\n正在收集: {name}")
                collect_func()
                print(f"  Completed")
            except Exception as e:
                self.logger.error(f"Failed to collect {name}: {e}")
                print(f"  Failed: {e}")
    
    def _collect_rss_feeds(self):
        """收集RSS新闻源"""
        print("\n收集RSS新闻源...")
        
        rss_sources = XML_SOURCE_GROUPS['rss']['sources']
        
        for source in rss_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    保存成功")
                    self.increment_success()
                else:
                    print(f"    下载或验证Failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _collect_worldbank(self):
        """收集世界银行XML数据"""
        print("\n收集世界银行XML数据...")
        
        worldbank_sources = XML_SOURCE_GROUPS['worldbank']['sources']
        
        for source in worldbank_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    保存成功")
                    self.increment_success()
                else:
                    print(f"    下载或验证Failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _collect_financial_xml(self):
        """收集金融XML数据"""
        print("\n收集金融XML数据...")
        
        financial_sources = XML_SOURCE_GROUPS['financial_xml']['sources']
        
        for source in financial_sources:
            source_name = source['name']
            url = source['url']
            
            print(f"  {source['description']}")
            
            try:
                xml_text = self._fetch_xml(url)
                
                if xml_text and self._validate_xml(xml_text, source_name):
                    filename = self.output_dir / f"{source_name}.xml"
                    self._save_xml(xml_text, filename)
                    print(f"    保存成功")
                    self.increment_success()
                else:
                    print(f"    下载或验证Failed")
                    self.increment_failure()
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                self.logger.error(f"Failed to collect {source_name}: {e}")
                self.increment_failure()
                print(f"    Error: {e}")
    
    def _fetch_xml(self, url: str) -> str:
        """获取XML数据"""
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"HTTP {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _validate_xml(self, xml_text: str, source_name: str) -> bool:
        """验证XML格式"""
        try:
            ET.fromstring(xml_text)
            return True
        except ET.ParseError as e:
            self.logger.error(f"Invalid XML for {source_name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"XML validation failed for {source_name}: {e}")
            return False
    
    def _save_xml(self, xml_text: str, filename: Path):
        """保存XML数据"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_text)
            self.logger.info(f"Saved: {filename.name}")
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")

