#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Twitter数据收集器
使用Twitter API v2和snscrape收集推文数据
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# 尝试导入snscrape
try:
    import snscrape.modules.twitter as sntwitter
    import snscrape
    SNSCRAPE_AVAILABLE = True
    snscrape_version = getattr(snscrape, '__version__', 'unknown')
except ImportError:
    SNSCRAPE_AVAILABLE = False
    snscrape_version = None

# 尝试导入tweepy
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

from data_collection.base_collector import BaseCollector


class TwitterCollector(BaseCollector):
    """Twitter数据收集器 - 支持官方API和snscrape"""
    
    def __init__(self):
        super().__init__('twitter')
        
        print(f"📦 snscrape版本: {snscrape_version if SNSCRAPE_AVAILABLE else 'not installed'}")
        
        # 配置File路径
        self.config_file = self.get_config_path('twitter_config.json')
        
        # 如果配置不在新位置，尝试从旧位置读取
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "twitter_collect" / "twitter_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # Twitter API对象（延迟初始化）
        self.client = None
        self.config = None
        self.data_source = "hybrid"  # hybrid, snscrape, api
        self.api_available = False
        self.snscrape_available = SNSCRAPE_AVAILABLE
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_file}")
            print(f"\nWarning: 未找到Twitter配置File")
            print(f"将尝试使用snscrape模式（不需要API密钥）")
            print(f"\n如需使用官方API，请创建配置File:")
            print(f"  {self.config_file}")
            print("\n示例内容:")
            print(json.dumps({
                "bearer_token": "your_bearer_token",
                "api_key": "your_api_key",
                "api_secret": "your_api_secret",
                "access_token": "your_access_token",
                "access_token_secret": "your_access_token_secret"
            }, indent=2))
            return SNSCRAPE_AVAILABLE
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate config: {e}")
            return SNSCRAPE_AVAILABLE
    
    def _setup_api(self) -> bool:
        """设置Twitter API客户端"""
        if not self.config:
            self.logger.info("No API config, will use snscrape if available")
            return SNSCRAPE_AVAILABLE
        
        if not TWEEPY_AVAILABLE:
            self.logger.warning("tweepy not installed, can only use snscrape")
            return SNSCRAPE_AVAILABLE
        
        try:
            self.client = tweepy.Client(
                bearer_token=self.config.get('bearer_token'),
                consumer_key=self.config.get('api_key'),
                consumer_secret=self.config.get('api_secret'),
                access_token=self.config.get('access_token'),
                access_token_secret=self.config.get('access_token_secret'),
                wait_on_rate_limit=True
            )
            self.api_available = True
            print("✅ Twitter官方API客户端初始化成功")
            self.logger.info("Twitter API client initialized")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to setup Twitter API: {e}")
            print(f"⚠️ Twitter官方API初始化Failed: {e}")
            print("💡 将使用snscrape模式")
            return SNSCRAPE_AVAILABLE
    
    def collect(self) -> Dict[str, Any]:
        """主收集方法"""
        self.start_collection()
        
        try:
            # 验证配置
            if not self.validate_config():
                return {
                    'success': False,
                    'message': 'No valid data source available',
                    'stats': self.get_stats()
                }
            
            # 设置API
            self._setup_api()
            
            # 显示可用的数据源
            self._print_data_source_info()
            
            print("\nTwitter数据收集")
            print("-" * 70)
            
            # 获取用户输入
            print("\n请输入要搜索的关键词（用逗号分隔）")
            print("示例: unicode,security,python")
            user_input = input("\n关键词: ").strip()
            
            if not user_input:
                print("Error: 未输入关键词")
                return {
                    'success': False,
                    'message': 'No keywords provided',
                    'stats': self.get_stats()
                }
            
            keywords = [k.strip() for k in user_input.split(',')]
            
            # 获取数量
            print("\n请输入每个关键词要收集的推文数量")
            print("（直接回车使用默认: 100）")
            limit_input = input("\n推文数量: ").strip()
            
            if not limit_input:
                limit = 100
            else:
                try:
                    limit = int(limit_input)
                except ValueError:
                    print("无效数量，使用默认: 100")
                    limit = 100
            
            # 收集数据
            print(f"\n开始收集 {len(keywords)} 个关键词的推文...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            for keyword in keywords:
                try:
                    print(f"\n正在收集: {keyword}")
                    # 收集数据
                    data = self._search_tweets(keyword, max_results=limit)
                    
                    # 保存数据
                    if data:
                        # 生成安全的File名
                        safe_filename = keyword.replace(' ', '_').replace('#', '').replace('@', '')[:50]
                        filename = f"{safe_filename}_tweets.json"
                        self._save_data(data, filename)
                        self.increment_success()
                        print(f"  成功并has been保存")
                    else:
                        self.increment_failure()
                        print(f"  Failed: 未收集到数据")
                except Exception as e:
                    self.logger.error(f"Failed to collect tweets for '{keyword}': {e}")
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
                'message': f'Successfully collected {self.stats["successful_items"]} keywords'
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
            self.logger.error(f"Twitter collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _print_data_source_info(self):
        """显示数据源信息"""
        print("🔧 数据收集器配置:")
        print(f"   📊 数据源模式: {self.data_source}")
        print(f"   🔑 官方API: {'✅ 可用' if self.api_available else '❌ 不可用'}")
        print(f"   🕷️ snscrape: {'✅ 可用' if self.snscrape_available else '❌ 不可用'}")
        
        if self.data_source == "hybrid":
            print("💡 混合模式：优先snscrape，备用官方API")
        elif self.data_source == "snscrape":
            print("💡 snscrape模式：无需API密钥，无速率限制")
        elif self.data_source == "api":
            print("💡 官方API模式：需要认证，有速率限制")
        
        print("-" * 70)
    
    def _search_tweets(self, query: str, max_results: int = 100) -> Dict[str, Any]:
        """搜索推文 - 支持多种数据源"""
        print(f"🔍 搜索推文: '{query}'")
        print(f"📊 目标数量: {max_results} entries推文")
        
        # 根据数据源选择搜索方法
        if self.data_source == "snscrape":
            return self._search_tweets_snscrape(query, max_results)
        elif self.data_source == "api":
            return self._search_tweets_api(query, max_results)
        else:  # hybrid
            return self._search_tweets_hybrid(query, max_results)
    
    def _search_tweets_hybrid(self, query: str, max_results: int) -> Dict[str, Any]:
        """混合模式搜索 - 智能回退策略"""
        print("🔄 使用混合模式搜索")
        
        # 优先使用snscrape
        if self.snscrape_available:
            print("🕷️ 第一步：尝试snscrape...")
            result = self._search_tweets_snscrape(query, max_results)
            if result and result.get('tweets'):
                print("✅ snscrape搜索成功")
                return result
            else:
                print("⚠️ snscrape未找到结果或Failed")
        
        # 回退到官方API
        if self.api_available:
            print("🔄 第二步：回退到官方API...")
            try:
                result = self._search_tweets_api(query, max_results)
                if result and result.get('tweets'):
                    print("✅ 官方API搜索成功")
                    return result
                else:
                    print("⚠️ 官方API未找到结果")
            except Exception as e:
                print(f"⚠️ 官方APIFailed: {e}")
        
        # 所有方法都Failed
        print("❌ 所有数据源都Failed")
        return None
    
    def _search_tweets_snscrape(self, query: str, max_results: int) -> Dict[str, Any]:
        """使用snscrape搜索推文"""
        if not self.snscrape_available:
            print("❌ snscrape不可用")
            return None
        
        print(f"🕷️ 使用snscrape搜索推文: '{query}'")
        tweets_data = []
        
        try:
            scraper = sntwitter.TwitterSearchScraper(query)
            
            tweet_count = 0
            for i, tweet in enumerate(scraper.get_items()):
                if i >= max_results:
                    break
                
                try:
                    # 转换为统一格式
                    processed_tweet = {
                        "id": str(tweet.id),
                        "text": tweet.content or "",
                        "author_id": str(tweet.user.id) if tweet.user else "",
                        "author_username": tweet.user.username if tweet.user else "",
                        "author_name": tweet.user.displayname if tweet.user else "",
                        "created_at": tweet.date.isoformat() if tweet.date else "",
                        "lang": tweet.lang or "",
                        "public_metrics": {
                            "retweet_count": getattr(tweet, 'retweetCount', 0) or 0,
                            "like_count": getattr(tweet, 'likeCount', 0) or 0,
                            "reply_count": getattr(tweet, 'replyCount', 0) or 0,
                            "quote_count": getattr(tweet, 'quoteCount', 0) or 0
                        },
                        "url": tweet.url or "",
                        "source": "snscrape"
                    }
                    tweets_data.append(processed_tweet)
                    tweet_count += 1
                    
                    # 进度显示
                    if tweet_count % 10 == 0:
                        print(f"📄 has been获取 {tweet_count} entries推文...")
                    
                    # 添加小延迟
                    if tweet_count % 20 == 0:
                        time.sleep(0.5)
                
                except Exception as tweet_error:
                    self.logger.warning(f"Failed to process tweet: {tweet_error}")
                    continue
            
            if len(tweets_data) > 0:
                print(f"✅ snscrape搜索Completed，获取 {len(tweets_data)} entries推文")
                return {
                    "collection_info": {
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "tweets_count": len(tweets_data),
                        "data_source": "snscrape"
                    },
                    "tweets": tweets_data
                }
            else:
                print("⚠️ snscrape未获取到任何推文")
                return None
        
        except Exception as e:
            self.logger.error(f"snscrape search failed: {e}")
            print(f"❌ snscrape搜索Failed: {e}")
            return None
    
    def _search_tweets_api(self, query: str, max_results: int) -> Dict[str, Any]:
        """使用官方API搜索推文"""
        if not self.api_available:
            print("❌ 官方API不可用")
            return None
        
        print(f"🔑 使用官方API搜索推文: '{query}'")
        
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API限制
                tweet_fields=['created_at', 'author_id', 'lang', 'public_metrics', 'source'],
                user_fields=['username', 'name', 'verified']
            )
            
            if not response.data:
                print("⚠️ 官方API未找到推文")
                return None
            
            tweets_data = []
            for tweet in response.data:
                tweet_info = {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "author_id": str(tweet.author_id) if hasattr(tweet, 'author_id') else "",
                    "created_at": tweet.created_at.isoformat() if hasattr(tweet, 'created_at') else "",
                    "lang": tweet.lang if hasattr(tweet, 'lang') else "",
                    "public_metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                    "source": "twitter_api"
                }
                tweets_data.append(tweet_info)
            
            print(f"✅ 官方API搜索Completed，获取 {len(tweets_data)} entries推文")
            return {
                "collection_info": {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "tweets_count": len(tweets_data),
                    "data_source": "twitter_api"
                },
                "tweets": tweets_data
            }
        
        except Exception as e:
            self.logger.error(f"API search failed: {e}")
            print(f"❌ 官方API搜索Failed: {e}")
            return None
    
    def _save_data(self, data: Dict[str, Any], filename: str):
        """保存数据到JSONFile，支持合并和去重"""
        filepath = self.output_dir / filename
        
        try:
            # CheckFile是否has beenexists
            if filepath.exists():
                # 加载现有数据
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # 合并推文数据，根据ID去重
                existing_tweet_ids = {t['id'] for t in existing_data.get('tweets', [])}
                new_tweets = [t for t in data.get('tweets', []) if t['id'] not in existing_tweet_ids]
                
                # 合并
                existing_data['tweets'].extend(new_tweets)
                existing_data['collection_info']['tweets_count'] = len(existing_data['tweets'])
                existing_data['collection_info']['last_updated'] = datetime.now().isoformat()
                
                # 保存合并后的数据
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 数据has been合并保存: {filepath}")
                print(f"   新增推文: {len(new_tweets)} entries")
                self.logger.info(f"Merged {len(new_tweets)} new tweets into {filename}")
            else:
                # 直接保存新File
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 数据has been保存: {filepath}")
                self.logger.info(f"Saved: {filename}")
        
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")
            print(f"❌ 保存数据Failed: {e}")
