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


from data_collection.utils.logger import setup_logger


try:
    from .scraping_config import ScrapingConfig
except ImportError:
    from scraping_config import ScrapingConfig

class WebScraper:
    
    def __init__(self, config: ScrapingConfig, output_dir: Union[str, Path] = "testscan_data"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('WebScraper', console_output=False)
        
        self.html_output_dir = self.output_dir / "origin_data" / "html"
        self.html_output_dir.mkdir(parents=True, exist_ok=True)
        
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
        request_settings = self.config.get_request_settings()
        
        self.session.timeout = request_settings.get("timeout", 30)
        
        self.session.trust_env = False
        self.session.proxies = {
            'http': None,
            'https': None,
        }
        import os
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
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
        site_name = website_info.get('name', 'unknown')
        base_url = website_info.get('url', '')
        
        self.logger.info(f"Start scraping website: {site_name} ({base_url})")
        
        if self.config.is_domain_blacklisted(base_url):
            self.logger.warning(f"Website is in blacklist, skipping: {base_url}")
            return self._create_error_result(website_info, "Domain is in blacklist")
        
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
            # Scrape homepage
            homepage_result = self._scrape_single_page(base_url, "homepage", website_info)
            if homepage_result:
                scraping_result["pages_scraped"].append(homepage_result)
                scraping_result["scraping_stats"]["successful_pages"] += 1
                
                # Discover and scrape secondary pages
                if self.config.get_scraping_rules().get("include_secondary_pages", True):
                    secondary_pages = self._discover_secondary_pages(homepage_result)
                    
                    max_pages = self.config.get_scraping_rules().get("max_pages_per_site", 5)
                    pages_to_scrape = secondary_pages[:max_pages-1]  # Subtract 1 because homepage has already been scraped
                    
                    for page_url in pages_to_scrape:
                        try:
                            # Add delay
                            time.sleep(self.config.get_request_delay())
                            
                            page_result = self._scrape_single_page(page_url, "secondary", website_info)
                            if page_result:
                                scraping_result["pages_scraped"].append(page_result)
                                scraping_result["scraping_stats"]["successful_pages"] += 1
                            else:
                                scraping_result["scraping_stats"]["failed_pages"] += 1
                                
                        except Exception as e:
                            self.logger.error(f"Failed to scrape secondary page {page_url}: {e}")
                            scraping_result["errors"].append(f"Failed to scrape secondary page: {page_url} - {e}")
                            scraping_result["scraping_stats"]["failed_pages"] += 1
            
            else:
                scraping_result["scraping_stats"]["failed_pages"] += 1
                scraping_result["errors"].append("Failed to scrape homepage")
            
            # Update statistics
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
            
            self.logger.info(f"Website scraping completed: {site_name}, successful pages: {scraping_result['scraping_stats']['successful_pages']}")
            
        except Exception as e:
            self.logger.error(f"Error scraping website {site_name}: {e}")
            scraping_result["errors"].append(f"Website scraping error: {e}")
        
        return scraping_result
    
    def _scrape_single_page(self, url: str, page_type: str, website_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scrape a single page"""
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Scraping page: {url} (attempt {attempt + 1}/{max_attempts})")
                
                # Set random User-Agent
                self.session.headers['User-Agent'] = self.config.get_random_user_agent()
                
                # Add Referer header (helpful for some websites)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    self.session.headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
                
                # Send request - increase timeout and disable proxy
                self.stats["total_requests"] += 1
                response = self.session.get(
                    url, 
                    timeout=45,  # Increase timeout
                    allow_redirects=True,
                    verify=True  # Verify SSL certificate
                )
                
                # Check response
                if response.status_code == 200:
                    self.stats["successful_requests"] += 1
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        self.logger.warning(f"Non-HTML content, skipping: {url} (Content-Type: {content_type})")
                        return None
                    
                    # Check page size
                    content_length = len(response.content)
                    max_size = self.config.get_scraping_rules().get("max_page_size_mb", 10) * 1024 * 1024
                    
                    if content_length > max_size:
                        self.logger.warning(f"Page too large, skipping: {url} ({content_length / 1024 / 1024:.1f}MB)")
                        return None
                    
                    # Build page result
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
                    
                    # Save raw HTML
                    if self.config.get_output_settings().get("save_raw_html", True):
                        self._save_raw_html(page_result)
                    
                    return page_result
                    
                elif response.status_code == 403:
                    # 403 error, try again with different User-Agent
                    if attempt < max_attempts - 1:
                        self.logger.warning(f"Page returned 403, retrying with different User-Agent: {url}")
                        time.sleep(2 * (attempt + 1))  # Incremental delay
                        continue
                    else:
                        self.stats["failed_requests"] += 1
                        self.logger.warning(f"Page request failed: {url} (status code: 403, attempted {max_attempts} times)")
                        return None
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.warning(f"Page request failed: {url} (status code: {response.status_code})")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"Page request timeout, retrying: {url} (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.warning(f"Page request timeout: {url} (attempted {max_attempts} times)")
                    return None
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"Connection error, retrying: {url} - {str(e)[:100]}")
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"Connection failed: {url} - {str(e)[:200]}")
                    return None
                
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1 and '502' not in str(e):
                    self.logger.warning(f"Request exception, retrying: {url} - {str(e)[:100]}")
                    time.sleep(2 * (attempt + 1))
                    continue
                else:
                    self.stats["failed_requests"] += 1
                    self.logger.error(f"Page request exception: {url} - {str(e)[:200]}")
                    return None
                
            except Exception as e:
                self.stats["failed_requests"] += 1
                self.logger.error(f"Error scraping page: {url} - {str(e)[:200]}")
                return None
        
        # All attempts failed
        return None
    
    def _discover_secondary_pages(self, homepage_result: Dict[str, Any]) -> List[str]:
        """Discover secondary page links"""
        
        try:
            from bs4 import BeautifulSoup
            
            html_content = homepage_result.get("html_content", "")
            base_url = homepage_result.get("url", "")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            secondary_urls = []
            secondary_config = self.config.get_secondary_page_config()
            max_links = secondary_config.get("max_links_to_check", 20)
            
            for link in links[:max_links * 2]:  # Check more links for filtering
                href = link.get('href', '').strip()
                link_text = link.get_text(strip=True)
                
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                
                # Check if same domain
                if not self._is_same_domain(base_url, absolute_url):
                    continue
                
                # Check if should include this link
                if self.config.should_include_link(link_text, absolute_url):
                    if absolute_url not in secondary_urls and absolute_url != base_url:
                        secondary_urls.append(absolute_url)
                        
                        if len(secondary_urls) >= max_links:
                            break
            
            self.logger.info(f"Discovered {len(secondary_urls)} secondary page links")
            return secondary_urls
            
        except Exception as e:
            self.logger.error(f"Error discovering secondary pages: {e}")
            return []
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False
    
    def _save_raw_html(self, page_result: Dict[str, Any]):
        """Save raw HTML content"""

        try:
            website_info = page_result["website_info"]
            website_name = website_info.get("name", "unknown")
            page_type = page_result.get("page_type", "unknown")

            # Get website rank/number for file naming
            rank = website_info.get("rank", 0)
            source_row = website_info.get("source_row", 0)

            # Use rank or row number as site number
            site_number = rank if rank > 0 else source_row

            # Create filename based on number
            # Clean filename, remove illegal characters
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', website_name)
            timestamp = int(page_result.get("scrape_timestamp", time.time()))

            # Format: number_website_name_page_type_timestamp.html
            filename = f"{site_number:06d}_{safe_name}_{page_type}_{timestamp}.html"
            file_path = self.html_output_dir / filename

            # Save HTML content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(page_result["html_content"])

            # Update file path in page result
            page_result["saved_html_path"] = str(file_path)

            self.logger.debug(f"HTML has been saved: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save HTML: {e}")
    
    def _create_error_result(self, website_info: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Create error result"""
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
        """Get scraping statistics"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_pages_scraped": 0,
            "total_sites_scraped": 0
        }
