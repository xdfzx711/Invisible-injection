#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reddit data collector
Collect posts and comments data from specified subreddits via Reddit API
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

from data_collection.base_collector import BaseCollector


class RedditCollector(BaseCollector):
    """Reddit data collector"""
    
    def __init__(self):
        super().__init__('reddit')
        
        # Check if praw is available
        if not PRAW_AVAILABLE:
            self.logger.error("praw library not installed. Install with: pip install praw")
            raise ImportError("praw library required for Reddit collection")
        
        # Config file path
        self.config_file = self.get_config_path('reddit_config.json')
        
        # If config is not in new location, try reading from old location
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "reddit_collect" / "reddit_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # Reddit API object (lazy initialization)
        self.reddit = None
        self.config = None
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.config_file.exists():
            self.logger.error(f"Config file not found: {self.config_file}")
            print(f"\nError: Reddit config file not found")
            print(f"Please create config file: {self.config_file}")
            print(f"Or: reddit_collect/reddit_config.json")
            print("\nExample content:")
            print(json.dumps({
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
                "user_agent": "UnicodeAgent/1.0 by YourUsername"
            }, indent=2))
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_keys = ['client_id', 'client_secret', 'user_agent']
            for key in required_keys:
                if key not in config or not config[key]:
                    self.logger.error(f"Missing required key in config: {key}")
                    return False
            
            self.config = config
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate config: {e}")
            return False
    
    def _authenticate(self) -> bool:
        """Authenticate Reddit API"""
        if not self.config:
            if not self.validate_config():
                return False
        
        try:
            self.reddit = praw.Reddit(
                client_id=self.config['client_id'],
                client_secret=self.config['client_secret'],
                user_agent=self.config['user_agent']
            )
            
            # 测试连接
            self.reddit.user.me()
            print("✅ Reddit API authentication successful")
            self.logger.info("Reddit API authenticated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Reddit API authentication failed: {e}")
            print(f"Error: Reddit API authentication failed - {e}")
            return False
    
    def _parse_target(self, target_str: str) -> tuple:
        """Parse target string, return (type, name)
        
        Args:
            target_str: Target string like "r/python" or "u/spez"
            
        Returns:
            (type, name): For example ("subreddit", "python") or ("user", "spez")
        """
        target_str = target_str.strip()
        
        if target_str.startswith('r/'):
            return ('subreddit', target_str[2:])
        elif target_str.startswith('u/'):
            return ('user', target_str[2:])
        else:
            # Default as subreddit (backward compatible)
            return ('subreddit', target_str)
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method"""
        self.start_collection()
        
        try:
            # 认证
            if not self._authenticate():
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'stats': self.get_stats()
                }
            
            print("\nReddit data collection")
            print("-" * 70)

            # Load targets and limit from config file
            # Prioritize new targets field, compatible with old subreddits field
            targets = self.config.get('targets', [])
            if not targets:
                # Backward compatible: if no targets, read from subreddits and convert
                subreddits = self.config.get('subreddits', [])
                targets = [f"r/{s}" for s in subreddits]
            
            limit = self.config.get('limit', 50)

            if not targets:
                self.logger.error("No targets or subreddits specified in config file, cannot continue.")
                print("Error: No targets specified in config file for collection.")
                return {
                    'success': False,
                    'message': 'No targets specified in config file',
                    'stats': self.get_stats()
                }
            
            # 收集数据
            print(f"\nStarting to collect {len(targets)} targets...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            for target in targets:
                try:
                    # 解析目标类型
                    target_type, target_name = self._parse_target(target)
                    
                    if target_type == 'subreddit':
                        print(f"\nCollecting: r/{target_name}")
                        data = self._collect_subreddit_data(target_name, limit=limit)
                        save_name = f"r_{target_name}"
                    elif target_type == 'user':
                        print(f"\nCollecting: u/{target_name}")
                        data = self._collect_user_data(target_name, limit=limit)
                        save_name = f"u_{target_name}"
                    else:
                        self.logger.warning(f"Unknown target type: {target}")
                        continue
                    
                    # 保存数据
                    if data:
                        self._save_data(data, save_name)
                        self.increment_success()
                        print(f"  Success and saved")
                    else:
                        self.increment_failure()
                        print(f"  Failed: No data collected")
                except Exception as e:
                    self.logger.error(f"Failed to collect {target}: {e}")
                    self.increment_failure()
                    print(f"  Failed: {e}")
            
            self.end_collection()
            self.log_summary()
            
            # Count collected JSON files
            file_count = len(list(self.output_dir.glob('*.json')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {self.stats["successful_items"]} targets'
            }
            
        except KeyboardInterrupt:
            print("\n\nUser interrupted collection")
            self.end_collection()
            return {
                'success': False,
                'message': 'Collection interrupted',
                'file_count': len(list(self.output_dir.glob('*.json'))),
                'stats': self.get_stats()
            }
        except Exception as e:
            self.logger.error(f"Reddit collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _collect_subreddit_data(self, subreddit_name: str, limit: int = 100) -> Dict[str, Any]:
        """Collect data from specified subreddit"""
        print(f"🔍 Starting to collect data from r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Collect submission data
            submissions_data = []
            comments_data = []
            
            # Get latest submissions (by time order)
            for submission in subreddit.new(limit=limit):
                # Collect submission information
                submission_info = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "subreddit": subreddit_name
                }
                submissions_data.append(submission_info)
                
                # Collect comments data
                try:
                    submission.comments.replace_more(limit=0)  # Do not expand "more comments"
                    for comment in submission.comments.list():
                        if hasattr(comment, 'body') and comment.body != '[deleted]':
                            comment_info = {
                                "id": comment.id,
                                "submission_id": submission.id,
                                "body": comment.body,
                                "author": str(comment.author) if comment.author else "[deleted]",
                                "score": comment.score,
                                "created_utc": comment.created_utc,
                                "permalink": f"https://reddit.com{comment.permalink}",
                                "subreddit": subreddit_name
                            }
                            comments_data.append(comment_info)
                
                except Exception as e:
                    self.logger.warning(f"Failed to collect comments for post {submission.id}: {e}")
                
                # Simple rate limiting
                time.sleep(0.1)
            
            print(f"📊 收集Completed: {len(submissions_data)} 个帖子, {len(comments_data)} entries评论")
            
            return {
                "collection_info": {
                    "type": "subreddit",
                    "subreddit": subreddit_name,
                    "timestamp": datetime.now().isoformat(),
                    "submissions_count": len(submissions_data),
                    "comments_count": len(comments_data)
                },
                "submissions": submissions_data,
                "comments": comments_data
            }
        
        except Exception as e:
            self.logger.error(f"Failed to collect r/{subreddit_name}: {e}")
            print(f"❌ Failed to collect r/{subreddit_name} data: {e}")
            return None
    
    def _collect_user_data(self, username: str, limit: int = 100) -> Dict[str, Any]:
        """Collect data from specified user"""
        print(f"🔍 Starting to collect data from u/{username}...")
        
        try:
            redditor = self.reddit.redditor(username)
            
            # Collect user published submissions
            submissions_data = []
            comments_data = []
            
            # Get user latest submissions
            print(f"  Collecting user posts...")
            for submission in redditor.submissions.new(limit=limit):
                submission_info = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "subreddit": str(submission.subreddit)
                }
                submissions_data.append(submission_info)
                time.sleep(0.1)
            
            # Get user latest comments
            print(f"  Collecting user comments...")
            for comment in redditor.comments.new(limit=limit):
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comment_info = {
                        "id": comment.id,
                        "submission_id": comment.submission.id if hasattr(comment, 'submission') else None,
                        "body": comment.body,
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "score": comment.score,
                        "created_utc": comment.created_utc,
                        "permalink": f"https://reddit.com{comment.permalink}",
                        "subreddit": str(comment.subreddit)
                    }
                    comments_data.append(comment_info)
                time.sleep(0.1)
            
            print(f"📊 收集Completed: {len(submissions_data)} 个帖子, {len(comments_data)} entries评论")
            
            return {
                "collection_info": {
                    "type": "user",
                    "username": username,
                    "timestamp": datetime.now().isoformat(),
                    "submissions_count": len(submissions_data),
                    "comments_count": len(comments_data)
                },
                "submissions": submissions_data,
                "comments": comments_data
            }
        
        except Exception as e:
            self.logger.error(f"Failed to collect u/{username}: {e}")
            print(f"❌ Failed to collect u/{username} data: {e}")
            return None
    
    def _save_data(self, data: Dict[str, Any], save_name: str):
        """Save data to JSON file
        
        Args:
            data: Data dictionary to save
            save_name: File name prefix to save (like "r_python" or "u_spez")
        """
        if not data:
            return
        
        # Clean filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', save_name)
        filename = self.output_dir / f"{safe_name}_data.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved: {filename.name}")
            print(f"💾 Data saved: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")
            print(f"❌ Failed to save data: {e}")
