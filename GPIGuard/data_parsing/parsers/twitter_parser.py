#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Twitter Data Parsing器
从Twitter JSONFile中提取推文文本
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import html
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import TextExtractor, FileUtils


class TwitterParser(BaseParser):
    """Twitter Data Parsing器（兼容旧格式）"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('twitter', enable_interference_filter, filter_config)
    
    def decode_text(self, text: str) -> str:
        """基础文本解码处理"""
        if not text:
            return ""
        return html.unescape(text).strip()
    
    def process_tweets(self, tweets: List[Dict], query: str, source_file: str) -> Dict[str, Any]:
        """处理推文数据（兼容旧格式）"""
        processed_tweets = []
        
        for tweet in tweets:
            cleaned_tweet = {
                'id': str(tweet.get('id', '')),
                'text': self.decode_text(tweet.get('text', '')),
                'author_username': tweet.get('author_username', ''),
                'author_name': tweet.get('author_name', ''),
                'created_at': tweet.get('created_at', ''),
                'lang': tweet.get('lang', ''),
                'public_metrics': tweet.get('public_metrics', {}),
                'url': tweet.get('url', '')
            }
            
            # 添加处理后的元数据
            cleaned_tweet['text_content'] = cleaned_tweet['text']
            cleaned_tweet['content_length'] = len(cleaned_tweet['text'])
            
            processed_tweets.append(cleaned_tweet)
        
        # 构建输出数据（与旧格式相同）
        output_data = {
            "parsing_info": {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "total_tweets": len(processed_tweets),
                "source_file": source_file
            },
            "tweets": processed_tweets
        }
        
        return output_data
    
    def parse_file(self, file_path: Path) -> bool:
        """
        解析单个Twitter JSONFile
        返回布尔值表示成功/Failed
        """
        self.logger.info(f"Parsing Twitter file: {file_path}")
        print(f"🔍 处理File: {file_path.name}")
        
        try:
            # 读取JSONFile
            content = FileUtils.safe_read_file(file_path)
            data = json.loads(content)
            
            # 从collection_info获取查询信息
            query = "unknown"
            if 'collection_info' in data:
                query = data['collection_info'].get('query', 'unknown')
            
            # 处理推文
            if 'tweets' in data and data['tweets']:
                tweets_data = self.process_tweets(data['tweets'], query, file_path.name)
                output_filename = f"{file_path.stem}_parsed.json"
                output_path = self.output_dir / output_filename
                self.save_parsed_data(tweets_data, output_path)
                
                print(f"   🐦 处理推文: {len(data['tweets'])} entries")
            
            self.logger.info(f"Successfully parsed {file_path.name}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            print(f"   ❌ JSON格式Error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            print(f"   ❌ 解析Error: {e}")
            return False
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """获取所有Twitter JSONFile"""
        # 匹配所有JSONFile（包括 twitter_*_data.json 和 *_tweets.json 格式）
        return list(directory.glob('*.json'))
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """解析整个directory"""
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        print(f"\n找到 {len(files)} 个Twitter数据File")
        
        self.stats['total_files'] = len(files)
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end=' ')
            success = self.parse_file(file_path)
            
            if success:
                self.stats['successful_files'] += 1
                print(f"✅ {file_path.name} 处理Completed")
            else:
                self.stats['failed_files'] += 1
                print(f"❌ {file_path.name} 处理Failed")
        
        return []
