#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reddit data parser
Extract posts and comments text from Reddit JSON files
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
    """Reddit data parser (compatible with old format)"""
    
    def __init__(self, enable_interference_filter: bool = True, filter_config: Dict[str, Any] = None):
        super().__init__('reddit', enable_interference_filter, filter_config)
    
    def decode_text(self, text: str) -> str:
        """Basic text decoding processing"""
        if not text:
            return ""
        
        # HTML entity decoding
        text = html.unescape(text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Apply interference character filter
        text = self._process_extracted_text(text)
        
        return text
    
    def extract_text_content(self, post: Dict) -> str:
        """Merge all text content from posts"""
        text_parts = []
        
        if post.get('title'):
            text_parts.append(post['title'])
        
        if post.get('selftext'):
            text_parts.append(post['selftext'])
        
        return ' '.join(text_parts).strip()
    
    def process_posts(self, submissions: List[Dict], subreddit_name: str, source_file: str) -> Dict[str, Any]:
        """Process post data (compatible with old format)"""
        processed_posts = []
        
        for post in submissions:
            # Keep only useful fields and decode
            cleaned_post = {
                'id': post['id'],
                'title': self.decode_text(post.get('title', '')),
                'selftext': self.decode_text(post.get('selftext', '')),
                'score': post.get('score', 0),
                'url': post.get('url', ''),
                'permalink': post.get('permalink', '')
            }
            
            # Add processed metadata
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
        """Process comment data (compatible with old format)"""
        processed_comments = []
        
        for comment in comments:
            # Keep only useful fields and decode
            cleaned_comment = {
                'id': comment['id'],
                'submission_id': comment.get('submission_id', ''),
                'body': self.decode_text(comment.get('body', '')),
                'score': comment.get('score', 0),
                'permalink': comment.get('permalink', '')
            }
            
            # Add processed metadata
            cleaned_comment['text_content'] = cleaned_comment['body']
            cleaned_comment['content_length'] = len(cleaned_comment['text_content'])
            
            processed_comments.append(cleaned_comment)
        
        # Build output data (identical to old format)
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
        """Extract subreddit name from filename"""
        # chatgpt_promptDesign_data.json -> chatgpt_promptDesign
        # unicode_data.json -> unicode
        base_name = filename.replace('_data.json', '')
        return base_name
    
    def parse_file(self, file_path: Path) -> bool:
        """
        Parse a single Reddit JSON file
        Return boolean indicating success/failure
        """
        self.logger.info(f"Parsing Reddit file: {file_path}")
        print(f"🔍 Processing file: {file_path.name}")
        
        try:
            # Read JSON file
            content = FileUtils.safe_read_file(file_path)
            data = json.loads(content)
            
            # Extract subreddit name
            subreddit_name = self.extract_subreddit_name(file_path.name)
            
            # Process posts
            if 'submissions' in data and data['submissions']:
                posts_data = self.process_posts(data['submissions'], subreddit_name, file_path.name)
                posts_filename = f"{subreddit_name}_posts_parsed.json"
                posts_path = self.output_dir / posts_filename
                self.save_parsed_data(posts_data, posts_path)
                
                print(f"   📋 Processing posts: {len(data['submissions'])} items")
            
            # Process comments
            if 'comments' in data and data['comments']:
                comments_data = self.process_comments(data['comments'], subreddit_name, file_path.name)
                comments_filename = f"{subreddit_name}_comments_parsed.json"
                comments_path = self.output_dir / comments_filename
                self.save_parsed_data(comments_data, comments_path)
                
                print(f"   💬 Processing comments: {len(data['comments'])} items")
            
            self.logger.info(f"Successfully parsed {file_path.name}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            print(f"   ❌ JSON format error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            print(f"   ❌ Parsing error: {e}")
            return False
    
    def _get_files_to_parse(self, directory: Path) -> List[Path]:
        """Get all Reddit JSON files"""
        return list(directory.glob('*_data.json'))
    
    def parse_directory(self, directory: Path = None) -> List[Dict[str, Any]]:
        """
        Parse entire directory
        """
        if directory is None:
            directory = self.input_dir
        
        if not directory.exists():
            self.logger.warning(f"Directory not found: {directory}")
            return []
        
        files = self._get_files_to_parse(directory)
        self.logger.info(f"Found {len(files)} files to parse in {directory}")
        print(f"\nFound {len(files)} Reddit data files")
        
        self.stats['total_files'] = len(files)
        
        subreddits = []
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end=' ')
            success = self.parse_file(file_path)
            
            if success:
                self.stats['successful_files'] += 1
                subreddit_name = self.extract_subreddit_name(file_path.name)
                subreddits.append(subreddit_name)
                print(f"✅ {file_path.name} processing completed")
            else:
                self.stats['failed_files'] += 1
                print(f"❌ {file_path.name} processing failed")
        
        # Generate summary report
        if subreddits:
            self._generate_summary_report(subreddits)
        
        # Note: Returns empty list here because results have been saved separately to different files
        # No need for batch summary
        return []
    
    def _generate_summary_report(self, subreddits: List[str]):
        """Generate parsing summary report"""
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
        
        # List generated files
        for subreddit in set(subreddits):
            summary["output_files"].extend([
                f"{subreddit}_posts_parsed.json",
                f"{subreddit}_comments_parsed.json"
            ])
        
        summary_path = self.output_dir / "reddit_parsing_summary.json"
        self.save_parsed_data(summary, summary_path)
        print(f"\n💾 Summary report saved: reddit_parsing_summary.json")
