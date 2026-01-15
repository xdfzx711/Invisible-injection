#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reddit Data Parsing器
从Reddit JSONFile中提取帖子和评论文本
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import html
import re
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_parsing.base_parser import BaseParser
from data_parsing.utils import FileUtils


class RedditParser(BaseParser):
    """Reddit Data Parsing器（兼容旧格式）"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('reddit', enable_interference_filter, filter_config)
    
    def decode_text(self, text: str) -> str:
        """基础文本解码处理"""
        if not text:
            return ""
        
        # HTML实体解码
        text = html.unescape(text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 应用干扰字符过滤器
        text = self._process_extracted_text(text)
        
        return text
    
    def extract_text_content(self, post: Dict) -> str:
        """合并帖子的所有文本内容"""
        text_parts = []
        
        if post.get('title'):
            text_parts.append(post['title'])
        
        if post.get('selftext'):
            text_parts.append(post['selftext'])
        
        return ' '.join(text_parts).strip()
    
    def process_posts(self, submissions: List[Dict], subreddit_name: str, source_file: str) -> Dict[str, Any]:
        """处理帖子数据（兼容旧格式）"""
        processed_posts = []
        
        for post in submissions:
            # 只保留有用字段并解码
            cleaned_post = {
                'id': post['id'],
                'title': self.decode_text(post.get('title', '')),
                'selftext': self.decode_text(post.get('selftext', '')),
                'score': post.get('score', 0),
                'url': post.get('url', ''),
                'permalink': post.get('permalink', '')
            }
            
            # 添加处理后的元数据
            cleaned_post['text_content'] = self.extract_text_content(cleaned_post)
            cleaned_post['content_length'] = len(cleaned_post['text_content'])
            
            processed_posts.append(cleaned_post)
        
        # 构建输出数据（与旧格式完全相同）
        output_data = {
            "parsing_info": {
                "subreddit": subreddit_name,
                "timestamp": datetime.now().isoformat(),
                "total_posts": len(processed_posts),
                "source_file": source_file
            },
            "posts": processed_posts
        }
        
        return output_data
    
    def process_comments(self, comments: List[Dict], subreddit_name: str, source_file: str) -> Dict[str, Any]:
        """处理评论数据（兼容旧格式）"""
        processed_comments = []
        
        for comment in comments:
            # 只保留有用字段并解码
            cleaned_comment = {
                'id': comment['id'],
                'submission_id': comment.get('submission_id', ''),
                'body': self.decode_text(comment.get('body', '')),
                'score': comment.get('score', 0),
                'permalink': comment.get('permalink', '')
            }
            
            # 添加处理后的元数据
            cleaned_comment['text_content'] = cleaned_comment['body']
            cleaned_comment['content_length'] = len(cleaned_comment['text_content'])
            
            processed_comments.append(cleaned_comment)
        
        # 构建输出数据（与旧格式完全相同）
        output_data = {
            "parsing_info": {
                "subreddit": subreddit_name,
                "timestamp": datetime.now().isoformat(),
                "total_comments": len(processed_comments),
                "source_file": source_file
            },
            "comments": processed_comments
        }
        
        return output_data
    
    def extract_subreddit_name(self, filename: str) -> str:
        """从File名提取subreddit名称"""
        # chatgpt_promptDesign_data.json -> chatgpt_promptDesign
        # unicode_data.json -> unicode
        base_name = filename.replace('_data.json', '')
        return base_name
    
    def parse_file(self, file_path: Path) -> bool:
        """
        解析单个Reddit JSONFile
        返回布尔值表示成功/Failed
        """
        self.logger.info(f"Parsing Reddit file: {file_path}")
        print(f"🔍 处理File: {file_path.name}")
        
        try:
            # 读取JSONFile
            content = FileUtils.safe_read_file(file_path)
            data = json.loads(content)
            
            # 提取subreddit名称
            subreddit_name = self.extract_subreddit_name(file_path.name)
            
            # 处理帖子
            if 'submissions' in data and data['submissions']:
                posts_data = self.process_posts(data['submissions'], subreddit_name, file_path.name)
                posts_filename = f"{subreddit_name}_posts_parsed.json"
                posts_path = self.output_dir / posts_filename
                self.save_parsed_data(posts_data, posts_path)
                
                print(f"   📋 处理帖子: {len(data['submissions'])} 个")
            
            # 处理评论
            if 'comments' in data and data['comments']:
                comments_data = self.process_comments(data['comments'], subreddit_name, file_path.name)
                comments_filename = f"{subreddit_name}_comments_parsed.json"
                comments_path = self.output_dir / comments_filename
                self.save_parsed_data(comments_data, comments_path)
                
                print(f"   💬 处理评论: {len(data['comments'])} 个")
            
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
        """获取所有Reddit JSONFile"""
        return list(directory.glob('*_data.json'))
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """
        解析整个directory
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\n找到 {len(files)} 个Reddit数据File")
        
        self.stats['total_files'] = len(files)
        
        subreddits = []
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end=' ')
            success = self.parse_file(file_path)
            
            if success:
                self.stats['successful_files'] += 1
                subreddit_name = self.extract_subreddit_name(file_path.name)
                subreddits.append(subreddit_name)
                print(f"✅ {file_path.name} 处理Completed")
            else:
                self.stats['failed_files'] += 1
                print(f"❌ {file_path.name} 处理Failed")
        
        # 生成汇总报告
        if subreddits:
            self._generate_summary_report(subreddits)
        
        # 注意：这里返回空列表，因为结果has been经分别保存到不同File
        # 不需要批量汇总
        return []
    
    def _generate_summary_report(self, subreddits: List[str]):
        """生成解析汇总报告"""
        summary = {
            "processing_info": {
                "timestamp": datetime.now().isoformat(),
                "input_directory": str(self.input_dir),
                "output_directory": str(self.output_dir)
            },
            "statistics": {
                "processed_files": self.stats['successful_files'],
                "subreddits": list(set(subreddits))
            },
            "output_files": []
        }
        
        # 列出生成的File
        for subreddit in set(subreddits):
            summary["output_files"].extend([
                f"{subreddit}_posts_parsed.json",
                f"{subreddit}_comments_parsed.json"
            ])
        
        summary_path = self.output_dir / "reddit_parsing_summary.json"
        self.save_parsed_data(summary, summary_path)
        print(f"\n💾 汇总报告has been保存: reddit_parsing_summary.json")
