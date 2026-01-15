#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urljoin, urlparse, quote
import random
import sys
import os

# 导入 logger
from data_collection.utils.logger import setup_logger

# 修复相对导入问题
try:
    from .scraping_config import ScrapingConfig
except ImportError:
    from scraping_config import ScrapingConfig

class WebScraper:
    """网页爬取器"""
    
    def __init__(self, config: ScrapingConfig, output_dir: Union[str, Path] = "testscan_data"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('WebScraper', console_output=False)
        
        # 创建Output directory
        self.html_output_dir = self.output_dir / "origin_data" / "html"
        self.html_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化会话
        self.session = requests.Session()
        self._setup_session()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_pages_scraped": 0,
            "total_sites_scraped": 0
        }
    
    def _setup_session(self):
        """设置请求会话"""
        request_settings = self.config.get_request_settings()
        
        # 设置超时
        self.session.timeout = request_settings.get("timeout", 30)
        
        # 强制禁用代理（避免使用系统代理导致连接Failed）
        self.session.trust_env = False
        self.session.proxies = {
            'http': None,
            'https': None,
        }
        # 禁用代理环境变量
        import os
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        # 设置重试适配器 - 添加403到重试列表
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=request_settings.get("max_retries", 3),
            backoff_factor=request_settings.get("retry_delay", 2),
            status_forcelist=[403, 429, 500, 502, 503, 504],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置更完整的请求头，模拟真实浏览器
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
    
    def scrape_website(self, website_info: Dict[str, Any]) -> Dict[str, Any]:
        """爬取单个网站"""
        site_name = website_info.get('name', 'unknown')
        base_url = website_info.get('url', '')
        
        self.logger.info(f"开始爬取网站: {site_name} ({base_url})")
        
        if self.config.is_domain_blacklisted(base_url):
            self.logger.warning(f"网站在黑名单中，跳过: {base_url}")
            return self._create_error_result(website_info, "域名在黑名单中")
        
        scraping_result = {
            "website_info": website_info,
            "pages_scraped": [],
            "scraping_stats": {
                "total_pages": 0,
                "successful_pages": 0,
                "failed_pages": 0,
                "start_time": time.time()
            },
            "errors": []
        }
        
        try:
            # 爬取首页
            homepage_result = self._scrape_single_page(base_url, "homepage", website_info)
            if homepage_result:
                scraping_result["pages_scraped"].append(homepage_result)
                scraping_result["scraping_stats"]["successful_pages"] += 1
                
                # 发现并爬取二级页面
                if self.config.get_scraping_rules().get("include_secondary_pages", True):
                    secondary_pages = self._discover_secondary_pages(homepage_result)
                    
                    max_pages = self.config.get_scraping_rules().get("max_pages_per_site", 5)
                    pages_to_scrape = secondary_pages[:max_pages-1]  # 减1因为has been经爬取了首页
                    
                    for page_url in pages_to_scrape:
                        try:
                            # 添加延迟
                            time.sleep(self.config.get_request_delay())
                            
                            page_result = self._scrape_single_page(page_url, "secondary", website_info)
                            if page_result:
                                scraping_result["pages_scraped"].append(page_result)
                                scraping_result["scraping_stats"]["successful_pages"] += 1
                            else:
                                scraping_result["scraping_stats"]["failed_pages"] += 1
                                
                        except Exception as e:
                            self.logger.error(f"爬取二级页面Failed {page_url}: {e}")
                            scraping_result["errors"].append(f"二级页面爬取Failed: {page_url} - {e}")
                            scraping_result["scraping_stats"]["failed_pages"] += 1
            
            else:
                scraping_result["scraping_stats"]["failed_pages"] += 1
                scraping_result["errors"].append("首页爬取Failed")
            
            # 更新Statistics
            scraping_result["scraping_stats"]["total_pages"] = (
                scraping_result["scraping_stats"]["successful_pages"] + 
                scraping_result["scraping_stats"]["failed_pages"]
            )
            scraping_result["scraping_stats"]["end_time"] = time.time()
            scraping_result["scraping_stats"]["duration"] = (
                scraping_result["scraping_stats"]["end_time"] - 
                scraping_result["scraping_stats"]["start_time"]
            )
            
            self.stats["total_sites_scraped"] += 1
            self.stats["total_pages_scraped"] += scraping_result["scraping_stats"]["successful_pages"]
            
            self.logger.info(f"网站爬取Completed: {site_name}, 成功页面: {scraping_result['scraping_stats']['successful_pages']}")
            
        except Exception as e:
            self.logger.error(f"爬取网站时出错 {site_name}: {e}")
            scraping_result["errors"].append(f"网站爬取Error: {e}")
        
        return scraping_result
    
    def _scrape_single_page(self, url: str, page_type: str, website_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """爬取单个页面"""
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"爬取页面: {url} (尝试 {attempt + 1}/{max_attempts})")
                
                # 设置随机User-Agent
                self.session.headers['User-Agent'] = self.config.get_random_user_agent()
                
                # 添加Referer头（对某些网站有帮助）
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    self.session.headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
                
                # 发送请求 - 增加超时时间并禁用代理
                self.stats["total_requests"] += 1
                response = self.session.get(
                    url, 
                    timeout=45,  # 增加超时时间
                    allow_redirects=True,
                    verify=True  # 验证SSL证书
                )
                
                # Check响应
                if response.status_code == 200:
                    self.stats["successful_requests"] += 1
                    
                    # Check内容类型
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        self.logger.warning(f"非HTML内容，跳过: {url} (Content-Type: {content_type})")
                        return None
                    
                    # Check页面大小
                    content_length = len(response.content)
                    max_size = self.config.get_scraping_rules().get("max_page_size_mb", 10) * 1024 * 1024
                    
                    if content_length > max_size:
                        self.logger.warning(f"页面过大，跳过: {url} ({content_length / 1024 / 1024:.1f}MB)")
                        return None
                    
                    # 构建页面结果
                    page_result = {
                        "url": url,
                        "page_type": page_type,
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "content_length": content_length,
                        "encoding": response.encoding or 'utf-8',
                        "html_content": response.text,
                        "response_headers": dict(response.headers),
                        "scrape_timestamp": time.time(),
                        "website_info": website_info
                    }
                    
                    # 保存原始HTML
                    if self.config.get_output_settings().get("save_raw_html", True):
                        self._save_raw_html(page_result)
                    
                    return page_result
                    
                elif response.status_code == 403:
                    # 403Error，尝试更换User-Agent后重试
                    if attempt < max_attempts - 1:
                        self.logger.warning(f"页面返回403，更换User-Agent后重试: {url}")
                        time.sleep(2 * (attempt + 1))  # 递增延迟
                        continue
                    else:
                        self.stats["failed_requests"] += 1
                        self.logger.warning(f"页面请求Failed: {url} (状态码: 403，has been尝试{max_attempts}次)")
                        return None
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.warning(f"页面请求Failed: {url} (状态码: {response.status_code})")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"页面请求超时，重试: {url} (尝试 {attempt + 1}/{max_attempts})")
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.warning(f"页面请求超时: {url} (has been尝试{max_attempts}次)")
                    return None
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"连接Error，重试: {url} - {str(e)[:100]}")
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"连接Failed: {url} - {str(e)[:200]}")
                    return None
                
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1 and '502' not in str(e):
                    self.logger.warning(f"请求异常，重试: {url} - {str(e)[:100]}")
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"页面请求异常: {url} - {str(e)[:200]}")
                    return None
                
            except Exception as e:
                self.stats["failed_requests"] += 1
                self.logger.error(f"爬取页面时出错: {url} - {str(e)[:200]}")
                return None
        
        # 所有尝试都Failed
        return None
    
    def _discover_secondary_pages(self, homepage_result: Dict[str, Any]) -> List[str]:
        """发现二级页面链接"""
        
        try:
            from bs4 import BeautifulSoup
            
            html_content = homepage_result.get("html_content", "")
            base_url = homepage_result.get("url", "")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找所有链接
            links = soup.find_all('a', href=True)
            
            secondary_urls = []
            secondary_config = self.config.get_secondary_page_config()
            max_links = secondary_config.get("max_links_to_check", 20)
            
            for link in links[:max_links * 2]:  # Check更多链接以便筛选
                href = link.get('href', '').strip()
                link_text = link.get_text(strip=True)
                
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                
                # Check是否为同域名
                if not self._is_same_domain(base_url, absolute_url):
                    continue
                
                # Check是否应该包含此链接
                if self.config.should_include_link(link_text, absolute_url):
                    if absolute_url not in secondary_urls and absolute_url != base_url:
                        secondary_urls.append(absolute_url)
                        
                        if len(secondary_urls) >= max_links:
                            break
            
            self.logger.info(f"发现 {len(secondary_urls)} 个二级页面链接")
            return secondary_urls
            
        except Exception as e:
            self.logger.error(f"发现二级页面时出错: {e}")
            return []
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check两个URL是否为同一域名"""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False
    
    def _save_raw_html(self, page_result: Dict[str, Any]):
        """保存原始HTML内容"""

        try:
            website_info = page_result["website_info"]
            website_name = website_info.get("name", "unknown")
            page_type = page_result.get("page_type", "unknown")

            # 获取网站排名/编号，用于File命名
            rank = website_info.get("rank", 0)
            source_row = website_info.get("source_row", 0)

            # 使用排名或行号作为编号
            site_number = rank if rank > 0 else source_row

            # 创建基于编号的File名
            # 清理File名，移除非法字符
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', website_name)
            timestamp = int(page_result.get("scrape_timestamp", time.time()))

            # 格式：编号_网站名_页面类型_时间戳.html
            filename = f"{site_number:06d}_{safe_name}_{page_type}_{timestamp}.html"
            file_path = self.html_output_dir / filename

            # 保存HTML内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(page_result["html_content"])

            # 更新页面结果中的File路径
            page_result["saved_html_path"] = str(file_path)

            self.logger.debug(f"HTMLhas been保存: {file_path}")

        except Exception as e:
            self.logger.error(f"保存HTMLFailed: {e}")
    
    def _create_error_result(self, website_info: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """创建Error结果"""
        return {
            "website_info": website_info,
            "pages_scraped": [],
            "scraping_stats": {
                "total_pages": 0,
                "successful_pages": 0,
                "failed_pages": 0,
                "start_time": time.time(),
                "end_time": time.time(),
                "duration": 0
            },
            "errors": [error_message]
        }
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """获取爬取Statistics"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """重置Statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_pages_scraped": 0,
            "total_sites_scraped": 0
        }
