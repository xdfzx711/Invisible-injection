#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


try:
    import snscrape.modules.twitter as sntwitter
    import snscrape
    SNSCRAPE_AVAILABLE = True
    snscrape_version = getattr(snscrape, '__version__', 'unknown')
except ImportError:
    SNSCRAPE_AVAILABLE = False
    snscrape_version = None


try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

from data_collection.base_collector import BaseCollector


class TwitterCollector(BaseCollector):

    
    def __init__(self):
        super().__init__('twitter')
        
        print(f"📦 snscrape version: {snscrape_version if SNSCRAPE_AVAILABLE else 'not installed'}")
        
        # Config file path
        self.config_file = self.get_config_path('twitter_config.json')
        
        # If config is not in new location, try reading from old location
        if not self.config_file.exists():
            old_config = self.path_manager.get_project_root() / "twitter_collect" / "twitter_config.json"
            if old_config.exists():
                self.config_file = old_config
                self.logger.info(f"Using config from old location: {old_config}")
        
        # Twitter API object (lazy initialization)
        self.client = None
        self.config = None
        self.data_source = "hybrid"  # hybrid, snscrape, api
        self.api_available = False
        self.snscrape_available = SNSCRAPE_AVAILABLE
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        if not self.config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_file}")
            print(f"\nWarning: Twitter config file not found")
            print(f"Will try to use snscrape mode (no API key required)")
            print(f"\nTo use the official API, please create config file:")
            print(f"  {self.config_file}")
            print("\nExample content:")
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
        """Setup Twitter API client"""
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
            print("✅ Twitter official API client initialized successfully")
            self.logger.info("Twitter API client initialized")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to setup Twitter API: {e}")
            print(f"⚠️ Twitter official API initialization failed: {e}")
            print("💡 Will use snscrape mode")
            return SNSCRAPE_AVAILABLE
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method"""
        self.start_collection()
        
        try:
            # Validate configuration
            if not self.validate_config():
                return {
                    'success': False,
                    'message': 'No valid data source available',
                    'stats': self.get_stats()
                }
            
            # Setup API
            self._setup_api()
            
            # Print available data sources
            self._print_data_source_info()
            
            print("\nTwitter data collection")
            print("-" * 70)
            
            # Get user input
            print("\nPlease enter keywords to search (separated by commas)")
            print("Example: unicode,security,python")
            user_input = input("\nKeywords: ").strip()
            
            if not user_input:
                print("Error: No keywords provided")
                return {
                    'success': False,
                    'message': 'No keywords provided',
                    'stats': self.get_stats()
                }
            
            keywords = [k.strip() for k in user_input.split(',')]
            
            # Get tweet limit
            print("\nPlease enter the number of tweets to collect per keyword")
            print("(Press Enter to use default: 100)")
            limit_input = input("\nTweet count: ").strip()
            
            if not limit_input:
                limit = 100
            else:
                try:
                    limit = int(limit_input)
                except ValueError:
                    print("Invalid count, using default: 100")
                    limit = 100
            
            # Collect data
            print(f"\nStarting to collect tweets for {len(keywords)} keywords...")
            print(f"Output directory: {self.output_dir}")
            print("-" * 70)
            
            for keyword in keywords:
                try:
                    print(f"\nCollecting: {keyword}")
                    # Collect data
                    data = self._search_tweets(keyword, max_results=limit)
                    
                    # Save data
                    if data:
                        # Generate safe filename
                        safe_filename = keyword.replace(' ', '_').replace('#', '').replace('@', '')[:50]
                        filename = f"{safe_filename}_tweets.json"
                        self._save_data(data, filename)
                        self.increment_success()
                        print(f"  Successfully saved")
                    else:
                        self.increment_failure()
                        print(f"  Failed: No data collected")
                except Exception as e:
                    self.logger.error(f"Failed to collect tweets for '{keyword}': {e}")
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
                'message': f'Successfully collected {self.stats["successful_items"]} keywords'
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
            self.logger.error(f"Twitter collection failed: {e}", exc_info=True)
            self.end_collection()
            return {
                'success': False,
                'message': f'Collection failed: {e}',
                'stats': self.get_stats()
            }
    
    def _print_data_source_info(self):
        """Print data source information"""
        print("🔧 Data collector configuration:")
        print(f"   📊 Data source mode: {self.data_source}")
        print(f"   🔑 Official API: {'✅ Available' if self.api_available else '❌ Not available'}")
        print(f"   🕷️ snscrape: {'✅ Available' if self.snscrape_available else '❌ Not available'}")
        
        if self.data_source == "hybrid":
            print("💡 Hybrid mode: Prioritize snscrape, fallback to official API")
        elif self.data_source == "snscrape":
            print("💡 snscrape mode: No API key needed, no rate limit")
        elif self.data_source == "api":
            print("💡 Official API mode: Requires authentication, has rate limit")
        
        print("-" * 70)
    
    def _search_tweets(self, query: str, max_results: int = 100) -> Dict[str, Any]:
        """Search tweets - supports multiple data sources"""
        print(f"🔍 Searching tweets: '{query}'")
        print(f"📊 Target count: {max_results} tweets")
        
        # 根据数据源选择搜索方法
        if self.data_source == "snscrape":
            return self._search_tweets_snscrape(query, max_results)
        elif self.data_source == "api":
            return self._search_tweets_api(query, max_results)
        else:  # hybrid
            return self._search_tweets_hybrid(query, max_results)
    
    def _search_tweets_hybrid(self, query: str, max_results: int) -> Dict[str, Any]:
        """Hybrid mode search - intelligent fallback strategy"""
        print("🔄 Using hybrid mode search")
        
        # Prioritize snscrape
        if self.snscrape_available:
            print("🕷️ Step 1: Try snscrape...")
            result = self._search_tweets_snscrape(query, max_results)
            if result and result.get('tweets'):
                print("✅ snscrape search successful")
                return result
            else:
                print("⚠️ snscrape found no results or failed")
        
        # Fallback to official API
        if self.api_available:
            print("🔄 Step 2: Fallback to official API...")
            try:
                result = self._search_tweets_api(query, max_results)
                if result and result.get('tweets'):
                    print("✅ Official API search successful")
                    return result
                else:
                    print("⚠️ Official API found no results")
            except Exception as e:
                print(f"⚠️ Official API failed: {e}")
        
        # All methods failed
        print("❌ All data sources failed")
        return None
    
    def _search_tweets_snscrape(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search tweets using snscrape"""
        if not self.snscrape_available:
            print("❌ snscrape not available")
            return None
        
        print(f"🕷️ Searching tweets using snscrape: '{query}'")
        tweets_data = []
        
        try:
            scraper = sntwitter.TwitterSearchScraper(query)
            
            tweet_count = 0
            for i, tweet in enumerate(scraper.get_items()):
                if i >= max_results:
                    break
                
                try:
                    # Convert to unified format
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
                    
                    # Progress display
                    if tweet_count % 10 == 0:
                        print(f"📄 Fetched {tweet_count} tweets...")
                    
                    # Add small delay
                    if tweet_count % 20 == 0:
                        time.sleep(0.5)
                
                except Exception as tweet_error:
                    self.logger.warning(f"Failed to process tweet: {tweet_error}")
                    continue
            
            if len(tweets_data) > 0:
                print(f"✅ snscrape search completed, fetched {len(tweets_data)} tweets")
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
                print("⚠️ snscrape did not fetch any tweets")
                return None
        
        except Exception as e:
            self.logger.error(f"snscrape search failed: {e}")
            print(f"❌ snscrape search failed: {e}")
            return None
    
    def _search_tweets_api(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search tweets using official API"""
        if not self.api_available:
            print("❌ Official API not available")
            return None
        
        print(f"🔑 Searching tweets using official API: '{query}'")
        
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API限制
                tweet_fields=['created_at', 'author_id', 'lang', 'public_metrics', 'source'],
                user_fields=['username', 'name', 'verified']
            )
            
            if not response.data:
                print("⚠️ Official API found no tweets")
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
            
            print(f"✅ Official API search completed, fetched {len(tweets_data)} tweets")
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
            print(f"❌ Official API search failed: {e}")
            return None
    
    def _save_data(self, data: Dict[str, Any], filename: str):
        """Save data to JSON file, supports merging and deduplication"""
        filepath = self.output_dir / filename
        
        try:
            # Check if file already exists
            if filepath.exists():
                # Load existing data
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # Merge tweet data, deduplicate by ID
                existing_tweet_ids = {t['id'] for t in existing_data.get('tweets', [])}
                new_tweets = [t for t in data.get('tweets', []) if t['id'] not in existing_tweet_ids]
                
                # Merge
                existing_data['tweets'].extend(new_tweets)
                existing_data['collection_info']['tweets_count'] = len(existing_data['tweets'])
                existing_data['collection_info']['last_updated'] = datetime.now().isoformat()
                
                # Save merged data
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Data merged and saved: {filepath}")
                print(f"   New tweets: {len(new_tweets)}")
                self.logger.info(f"Merged {len(new_tweets)} new tweets into {filename}")
            else:
                # Save new file directly
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Data saved: {filepath}")
                self.logger.info(f"Saved: {filename}")
        
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {e}")
            print(f"❌ Failed to save data: {e}")
