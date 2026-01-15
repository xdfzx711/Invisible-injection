#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reddit数据收集器
通过Reddit API收集指定subreddit的帖子和评论数据
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
    """Reddit数据收集器"""
    
    def __init__(self):
        super().__init__('reddit')
        
        # Checkpraw是否可用
        if not PRAW_AVAILABLE:
            self.logger.error("praw library not installed. Install with: pip install praw")
            raise ImportError("praw library required for Reddit collection")
        
        # 配置File路径
        self.config_file = self.get_config_path('reddit_config.json')
        
        # 如果配置不在新位置，尝试从旧位置读取
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "reddit_collect" / "reddit_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # Reddit API对象（延迟初始化）
        self.reddit = None
        self.config = None
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.config_file.exists():
            self.logger.error(f"Config file not found: {self.config_file}")
            print(f"\nError: 未找到Reddit配置File")
            print(f"请创建配置File: {self.config_file}")
            print(f"或: reddit_collect/reddit_config.json")
            print("\n示例内容:")
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
        """认证Reddit API"""
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
            print("✅ Reddit API认证成功")
            self.logger.info("Reddit API authenticated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Reddit API authentication failed: {e}")
            print(f"Error: Reddit API认证Failed - {e}")
            return False
    
    def _parse_target(self, target_str: str) -> tuple:
        """解析目标字符串，返回(类型, 名称)
        
        Args:
            target_str: 目标字符串，如 "r/python" 或 "u/spez"
            
        Returns:
            (type, name): 例如 ("subreddit", "python") 或 ("user", "spez")
        """
        target_str = target_str.strip()
        
        if target_str.startswith('r/'):
            return ('subreddit', target_str[2:])
        elif target_str.startswith('u/'):
            return ('user', target_str[2:])
        else:
            # 默认作为subreddit处理（向后兼容）
            return ('subreddit', target_str)
    
    def collect(self) -> Dict[str, Any]:
        """主收集方法"""
        self.start_collection()
        
        try:
            # 认证
            if not self._authenticate():
                return {
                    'success': False,
                    'message': 'Authentication failed',
                    'stats': self.get_stats()
                }
            
            print("\nReddit数据收集")
            print("-" * 70)

            # 从配置File加载targets和limit
            # 优先使用新的targets字段，兼容旧的subreddits字段
            targets = self.config.get('targets', [])
            if not targets:
                # 向后兼容：如果没有targets，从subreddits读取并转换
                subreddits = self.config.get('subreddits', [])
                targets = [f"r/{s}" for s in subreddits]
            
            limit = self.config.get('limit', 50)

            if not targets:
                self.logger.error("配置File中未指定targets或subreddits，无法继续。")
                print("Error: 配置File中未指定要收集的目标。")
                return {
                    'success': False,
                    'message': 'No targets specified in config file',
                    'stats': self.get_stats()
                }
            
            # 收集数据
            print(f"\n开始收集 {len(targets)} 个目标...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            for target in targets:
                try:
                    # 解析目标类型
                    target_type, target_name = self._parse_target(target)
                    
                    if target_type == 'subreddit':
                        print(f"\n正在收集: r/{target_name}")
                        data = self._collect_subreddit_data(target_name, limit=limit)
                        save_name = f"r_{target_name}"
                    elif target_type == 'user':
                        print(f"\n正在收集: u/{target_name}")
                        data = self._collect_user_data(target_name, limit=limit)
                        save_name = f"u_{target_name}"
                    else:
                        self.logger.warning(f"Unknown target type: {target}")
                        continue
                    
                    # 保存数据
                    if data:
                        self._save_data(data, save_name)
                        self.increment_success()
                        print(f"  成功并has been保存")
                    else:
                        self.increment_failure()
                        print(f"  Failed: 未收集到数据")
                except Exception as e:
                    self.logger.error(f"Failed to collect {target}: {e}")
                    self.increment_failure()
                    print(f"  Failed: {e}")
            
            self.end_collection()
            self.log_summary()
            
            # 统计收集的File
            file_count = len(list(self.output_dir.glob('*.json')))
            
            return {
                'success': True,
                'file_count': file_count,
                'output_dir': str(self.output_dir),
                'stats': self.get_stats(),
                'message': f'Successfully collected {self.stats["successful_items"]} targets'
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
            self.logger.error(f"Reddit collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _collect_subreddit_data(self, subreddit_name: str, limit: int = 100) -> Dict[str, Any]:
        """收集指定subreddit的数据"""
        print(f"🔍 开始收集 r/{subreddit_name} 的数据...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # 收集帖子数据
            submissions_data = []
            comments_data = []
            
            # 获取最新帖子（按时间顺序）
            for submission in subreddit.new(limit=limit):
                # 收集帖子信息
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
                
                # 收集评论
                try:
                    submission.comments.replace_more(limit=0)  # 不展开"更多评论"
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
                
                # 简单的速率控制
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
            print(f"❌ 收集 r/{subreddit_name} 数据Failed: {e}")
            return None
    
    def _collect_user_data(self, username: str, limit: int = 100) -> Dict[str, Any]:
        """收集指定用户的数据"""
        print(f"🔍 开始收集 u/{username} 的数据...")
        
        try:
            redditor = self.reddit.redditor(username)
            
            # 收集用户发布的帖子
            submissions_data = []
            comments_data = []
            
            # 获取用户最新的提交
            print(f"  收集用户帖子...")
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
            
            # 获取用户最新的评论
            print(f"  收集用户评论...")
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
            print(f"❌ 收集 u/{username} 数据Failed: {e}")
            return None
    
    def _save_data(self, data: Dict[str, Any], save_name: str):
        """保存数据到JSONFile
        
        Args:
            data: 要保存的数据字典
            save_name: 保存的File名前缀（如 "r_python" 或 "u_spez"）
        """
        if not data:
            return
        
        # 清理File名
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', save_name)
        filename = self.output_dir / f"{safe_name}_data.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved: {filename.name}")
            print(f"💾 数据has been保存: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")
            print(f"❌ 保存数据Failed: {e}")
